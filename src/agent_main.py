"""
Main Agent Orchestrator for Inventory Intelligence Tool (IIT)

This module implements the main agent orchestrator using a pluggable tool pattern
with Composio integration for automated inventory management and reorder decisions.
"""

import argparse
import asyncio
import csv
import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

from composio import ComposioToolSet, WorkspaceType
from dotenv import load_dotenv
import os

# Import all our modules
from src.connectors.unified_mcp_connector import UnifiedMCPConnector
from src.connectors.supplier_connector import SupplierConnector
# Keep legacy connectors for fallback (if needed)
from src.connectors.email_connector import EmailConnector
from src.connectors.notion_connector import NotionConnector
from src.policies.reorder_policy import ReorderPolicy
from src.models.llm_rationale import generate_rationale
from src.utils.logger import setup_logger
from src.utils.config import Config

# Load environment variables
load_dotenv()

class InventoryAgent:
    """
    Main agent orchestrator that coordinates inventory intelligence and automated reordering.
    
    Uses a pluggable tool pattern with Composio integration for:
    - Inventory monitoring and forecasting
    - Automated reorder decisions with LLM rationale
    - Notion page management
    - Email approval workflows
    - Supplier order placement
    """
    
    def __init__(self, dry_run: bool = False):
        """Initialize the inventory agent with all connectors and policies."""
        self.dry_run = dry_run
        self.logger = setup_logger(__name__)
        
        # Configuration
        self.auto_order_threshold = float(os.getenv("AUTO_ORDER_THRESHOLD", "500.0"))
        self.vendor_trust_threshold = float(os.getenv("VENDOR_TRUST_THRESHOLD", "0.8"))
        
        # Initialize unified MCP connector (replaces individual connectors)
        self.mcp_connector = UnifiedMCPConnector(demo_mode=dry_run)
        
        # Initialize legacy connectors as fallbacks (with proper config)
        from src.utils.config import Config
        config = Config()
        # Note: SheetsConnector is now replaced by UnifiedMCPConnector
        # self.legacy_sheets_connector = SheetsConnector(config)
        self.legacy_notion_connector = NotionConnector()
        self.legacy_email_connector = EmailConnector()
        
        # Supplier connector (not yet integrated with MCP)
        self.supplier_connector = SupplierConnector()
        
        # Initialize policies
        self.reorder_policy = ReorderPolicy()
        
        # Initialize Composio toolset (kept for backward compatibility)
        self.composio_api_key = os.getenv("COMPOSIO_API_KEY", "ak_7KV1PgJT2x0XIC_wqejz")
        self.webhook_secret = os.getenv("WEBHOOK_SECRET", "ed999b5c-aea7-44a8-b910-cae4b47cfb46")
        
        try:
            self.toolset = ComposioToolSet(
                workspace_config=WorkspaceType.Host(),
                api_key=self.composio_api_key
            )
            self.logger.info("Composio toolset initialized successfully")
        except Exception as e:
            self.logger.warning(f"Composio initialization failed: {e}. Using MCP connector only.")
            self.toolset = None
        
        # Initialize logging database
        self._init_logging_db()
        
        # Perform health check
        health_status = self.mcp_connector.health_check()
        self.logger.info(f"MCP Connector Health: {health_status}")
        
        self.logger.info(f"Inventory Agent initialized (dry_run={dry_run})")
        self.logger.info(f"Available MCP tools: {len(self.mcp_connector.get_available_tools())}")
    
    def _init_logging_db(self):
        """Initialize SQLite database for action logging."""
        try:
            self.db_path = "demo/agent_actions.db"
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sku TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    status TEXT,
                    order_id TEXT,
                    cost REAL,
                    vendor TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            self.logger.info(f"Action logging database initialized at {self.db_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize SQLite DB, falling back to CSV: {e}")
            self.db_path = None
            self.csv_path = "demo/agent_actions.csv"
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
    
    def _log_action(self, sku: str, action: str, details: str = "", status: str = "success", 
                   order_id: str = "", cost: float = 0.0, vendor: str = ""):
        """Log agent actions to SQLite or CSV."""
        timestamp = datetime.now().isoformat()
        
        try:
            if self.db_path:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO agent_actions 
                    (timestamp, sku, action, details, status, order_id, cost, vendor)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (timestamp, sku, action, details, status, order_id, cost, vendor))
                conn.commit()
                conn.close()
            else:
                # Fallback to CSV
                with open(self.csv_path, 'a', newline='') as f:
                    writer = csv.writer(f)
                    if f.tell() == 0:  # Write header if file is empty
                        writer.writerow(['timestamp', 'sku', 'action', 'details', 'status', 'order_id', 'cost', 'vendor'])
                    writer.writerow([timestamp, sku, action, details, status, order_id, cost, vendor])
                    
        except Exception as e:
            self.logger.error(f"Failed to log action: {e}")
    
    async def run_cycle(self) -> Dict[str, Any]:
        """
        Main orchestration cycle that processes inventory and makes reorder decisions.
        
        Steps:
        1. Fetch inventory and recent transactions (last 90 days)
        2. For each SKU:
           a. Run reorder_policy to get recommendation
           b. Generate LLM rationale
           c. Create or update Notion reorder page
           d. If cost < threshold and vendor trust >= threshold -> auto place order
           e. Else collect for batch approval email
        3. Send batch approval email for all pending approvals
        4. Update Google Sheet with status and order ID if placed
        5. Log actions into local SQLite or CSV
        
        Returns:
            Dict with cycle summary and results
        """
        cycle_start = time.time()
        self.logger.info("=== Starting Agent Run Cycle ===")
        
        results = {
            "cycle_start": datetime.now().isoformat(),
            "processed_skus": 0,
            "reorders_recommended": 0,
            "auto_orders_placed": 0,
            "approval_emails_sent": 0,
            "batch_approvals_pending": 0,
            "errors": [],
            "cycle_duration_seconds": 0
        }
        
        # Collect pending approvals for batch email
        pending_approvals = []
        
        try:
            # Step 1: Fetch inventory and recent transactions
            self.logger.info("Step 1: Fetching inventory and transaction data...")
            inventory_data = await self._fetch_inventory_data()
            transaction_data = await self._fetch_transaction_data()
            
            if not inventory_data:
                self.logger.warning("No inventory data found, skipping cycle")
                return results
            
            self.logger.info(f"Processing {len(inventory_data)} SKUs")
            
            # Step 2: Process each SKU
            for sku_data in inventory_data:
                try:
                    approval_request = await self._process_sku(sku_data, transaction_data, results)
                    if approval_request:
                        pending_approvals.append(approval_request)
                    results["processed_skus"] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing SKU {sku_data.get('sku', 'unknown')}: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
                    self._log_action(sku_data.get('sku', 'unknown'), "process_error", error_msg, "error")
            
            # Step 3: Send batch approval email if there are pending approvals
            if pending_approvals:
                self.logger.info(f"Sending batch approval email for {len(pending_approvals)} reorder requests")
                batch_message_id = self._send_batch_approval_email(pending_approvals)
                if batch_message_id:
                    results["approval_emails_sent"] = 1  # One batch email sent
                    results["batch_approvals_pending"] = len(pending_approvals)
                    self.logger.info(f"Batch approval email sent with {len(pending_approvals)} requests")
                else:
                    self.logger.error("Failed to send batch approval email")
                    results["errors"].append("Failed to send batch approval email")
            
            # Step 4: Final summary
            cycle_duration = time.time() - cycle_start
            results["cycle_duration_seconds"] = round(cycle_duration, 2)
            
            self.logger.info(f"=== Cycle Complete in {cycle_duration:.2f}s ===")
            self.logger.info(f"Processed: {results['processed_skus']} SKUs")
            self.logger.info(f"Reorders recommended: {results['reorders_recommended']}")
            self.logger.info(f"Auto orders placed: {results['auto_orders_placed']}")
            self.logger.info(f"Batch approval emails sent: {results['approval_emails_sent']}")
            self.logger.info(f"Pending approvals in batch: {results['batch_approvals_pending']}")
            
            if results["errors"]:
                self.logger.warning(f"Errors encountered: {len(results['errors'])}")
            
            return results
            
        except Exception as e:
            error_msg = f"Critical error in run_cycle: {str(e)}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
            results["cycle_duration_seconds"] = time.time() - cycle_start
            return results
    
    async def _fetch_inventory_data(self) -> List[Dict]:
        """Fetch current inventory data from Google Sheets via MCP connector."""
        try:
            inventory_items = await self.mcp_connector.read_inventory_data()
            # Convert InventoryItem objects to dictionaries for compatibility
            return [
                {
                    'sku': item.sku,
                    'on_hand': item.current_stock,
                    'reorder_point': item.reorder_point,
                    'reorder_quantity': item.reorder_quantity,
                    'vendor': item.vendor,
                    'cost': item.cost,
                    'description': item.description,
                    'category': item.category
                }
                for item in inventory_items
            ]
        except Exception as e:
            self.logger.error(f"Failed to fetch inventory data via MCP: {e}")
            # Fallback to legacy connector
            try:
                self.logger.info("Falling back to legacy sheets connector")
                return await self.legacy_sheets_connector.get_inventory_data()
            except Exception as fallback_error:
                self.logger.error(f"Legacy connector also failed: {fallback_error}")
                return []
    
    async def _fetch_transaction_data(self) -> List[Dict]:
        """Fetch recent transaction data (last 90 days) from Google Sheets via MCP connector."""
        try:
            # For now, return empty list as transaction data is not implemented in MCP connector
            # This would need to be added to the unified MCP connector
            self.logger.info("Transaction data not yet implemented in MCP connector, using empty list")
            return []
        except Exception as e:
            self.logger.error(f"Failed to fetch transaction data via MCP: {e}")
            # Fallback to legacy connector
            try:
                self.logger.info("Falling back to legacy sheets connector for transaction data")
                end_date = datetime.now()
                start_date = end_date - timedelta(days=90)
                return await self.legacy_sheets_connector.get_transaction_data(start_date, end_date)
            except Exception as fallback_error:
                self.logger.error(f"Legacy connector also failed: {fallback_error}")
                return []
    
    async def _process_sku(self, sku_data: Dict, transaction_data: List[Dict], results: Dict) -> Optional[Dict]:
        """
        Process a single SKU through the complete reorder workflow.
        
        Returns:
            Dict with approval request data if approval is needed, None otherwise
        """
        sku = sku_data.get('sku', 'unknown')
        self.logger.info(f"Processing SKU: {sku}")
        
        # Step 2a: Run reorder policy to get recommendation
        sku_transactions = [t for t in transaction_data if t.get('sku') == sku]
        
        # Create inventory_item dict for the reorder policy
        inventory_item = {
            'sku': sku,
            'on_hand': sku_data.get('on_hand', 0),
            'reorder_point': sku_data.get('reorder_point', 0)
        }
        
        # Get vendor data (using default vendors if not available)
        vendors = self._get_vendor_data()
        
        reorder_decision = self.reorder_policy.evaluate_reorder_need(
            inventory_item=inventory_item,
            transactions=sku_transactions,
            vendors=vendors
        )
        
        self._log_action(sku, "reorder_evaluation", json.dumps(reorder_decision), "success")
        
        if not reorder_decision.get('needs_reorder', False):
            self.logger.info(f"SKU {sku}: No reorder needed")
            return None
        
        results["reorders_recommended"] += 1
        self.logger.info(f"SKU {sku}: Reorder recommended - Qty: {reorder_decision['qty']}, Vendor: {reorder_decision['vendor']}")
        
        # Step 2b: Generate LLM rationale
        rationale_context = {
            "sku": sku,
            "on_hand": sku_data.get('on_hand', 0),
            "weekly_demand": reorder_decision.get('weekly_demand', 0),
            "stockout_date": reorder_decision.get('stockout_date', 'unknown'),
            "best_vendor": {
                "name": reorder_decision.get('vendor', 'Unknown'),
                "EOQ": reorder_decision.get('qty', 0),
                "TotalCost": reorder_decision.get('total_cost', 0)
            },
            "last_90d_stats": {
                "avg_daily": reorder_decision.get('avg_daily', 0),
                "stddev": reorder_decision.get('stddev', 0.5)  # Default stddev if not available
            }
        }
        
        try:
            rationale = generate_rationale(rationale_context)
            self.logger.info(f"SKU {sku}: Generated LLM rationale")
        except Exception as e:
            self.logger.warning(f"SKU {sku}: Failed to generate rationale: {e}")
            rationale = {
                "paragraph": f"Reorder recommended for {sku} based on inventory analysis.",
                "bullets": ["Automated decision based on forecasting models"]
            }
        
        # Step 2c: Create or update Notion reorder page
        notion_page_id = await self._update_notion_page(sku, reorder_decision, rationale)
        
        # Step 2d: Auto-order decision logic
        total_cost = reorder_decision.get('total_cost', float('inf'))
        vendor_trust_score = self._get_vendor_trust_score(reorder_decision.get('vendor', ''))
        
        should_auto_order = (
            total_cost < self.auto_order_threshold and 
            vendor_trust_score >= self.vendor_trust_threshold
        )
        
        if should_auto_order and not self.dry_run:
            # Auto place order
            order_result = await self._place_auto_order(sku, reorder_decision)
            if order_result.get('success'):
                results["auto_orders_placed"] += 1
                # Update Notion as Ordered
                await self._mark_notion_as_ordered(notion_page_id, order_result.get('order_id'))
                # Update Google Sheet
                await self._update_sheet_status(sku, "ordered", order_result.get('order_id'))
                self.logger.info(f"SKU {sku}: Auto order placed - Order ID: {order_result.get('order_id')}")
                return None  # No approval needed
            else:
                # Auto order failed, add to batch approval
                reason = "auto_order_failed"
        else:
            # Add to batch approval
            reason = "dry_run" if self.dry_run else f"cost=${total_cost:.2f} > ${self.auto_order_threshold} or trust={vendor_trust_score:.2f} < {self.vendor_trust_threshold}"
        
        # Return approval request data for batch processing
        self.logger.info(f"SKU {sku}: Added to batch approval ({reason})")
        return {
            "sku": sku,
            "reorder_decision": reorder_decision,
            "rationale": rationale,
            "notion_page_id": notion_page_id,
            "reason": reason
        }
    
    def _get_vendor_trust_score(self, vendor: str) -> float:
        """Get vendor trust score (mock implementation)."""
        # In production, this would query a vendor database
        vendor_scores = {
            "vendor_a": 0.95,
            "vendor_b": 0.85,
            "vendor_c": 0.75,
            "default": 0.8
        }
        return vendor_scores.get(vendor.lower(), vendor_scores["default"])
    
    def _get_vendor_data(self) -> List[Dict]:
        """Get vendor data for reorder policy evaluation."""
        # Expanded vendor data with more realistic variety - in production this would come from a database or API
        all_vendors = [
            {
                'vendor_id': 'V001',
                'vendor_name': 'Acme Supplies',
                'name': 'Acme Supplies',
                'price_per_unit': 12.50,
                'unit_cost': 12.50,  # Keep for backward compatibility
                'holding_cost_percentage': 0.20,
                'order_cost': 50.0,
                'lead_time': 7
            },
            {
                'vendor_id': 'V002',
                'vendor_name': 'Global Parts',
                'name': 'Global Parts',
                'price_per_unit': 15.80,  # Higher price to avoid always being selected
                'unit_cost': 15.80,  # Keep for backward compatibility
                'holding_cost_percentage': 0.25,
                'order_cost': 75.0,
                'lead_time': 10
            },
            {
                'vendor_id': 'V003',
                'vendor_name': 'Quick Ship',
                'name': 'Quick Ship',
                'price_per_unit': 13.20,
                'unit_cost': 13.20,  # Keep for backward compatibility
                'holding_cost_percentage': 0.15,
                'order_cost': 30.0,
                'lead_time': 3
            },
            {
                'vendor_id': 'V004',
                'vendor_name': 'Industrial Supply Co',
                'name': 'Industrial Supply Co',
                'price_per_unit': 11.25,
                'unit_cost': 11.25,
                'holding_cost_percentage': 0.22,
                'order_cost': 65.0,
                'lead_time': 8
            },
            {
                'vendor_id': 'V005',
                'vendor_name': 'Premium Parts Ltd',
                'name': 'Premium Parts Ltd',
                'price_per_unit': 16.75,
                'unit_cost': 16.75,
                'holding_cost_percentage': 0.18,
                'order_cost': 40.0,
                'lead_time': 5
            },
            {
                'vendor_id': 'V006',
                'vendor_name': 'Budget Components',
                'name': 'Budget Components',
                'price_per_unit': 9.95,
                'unit_cost': 9.95,
                'holding_cost_percentage': 0.30,
                'order_cost': 85.0,
                'lead_time': 14
            },
            {
                'vendor_id': 'V007',
                'vendor_name': 'Express Logistics',
                'name': 'Express Logistics',
                'price_per_unit': 14.60,
                'unit_cost': 14.60,
                'holding_cost_percentage': 0.12,
                'order_cost': 25.0,
                'lead_time': 2
            },
            {
                'vendor_id': 'V008',
                'vendor_name': 'Reliable Vendors Inc',
                'name': 'Reliable Vendors Inc',
                'price_per_unit': 10.85,
                'unit_cost': 10.85,
                'holding_cost_percentage': 0.28,
                'order_cost': 55.0,
                'lead_time': 12
            }
        ]
        
        # Return a random subset of 3-4 vendors to simulate realistic vendor options per evaluation
        import random
        random.seed(hash(str(datetime.now().date())))  # Consistent per day but varies
        num_vendors = random.randint(3, 5)
        return random.sample(all_vendors, num_vendors)
    
    async def _update_notion_page(self, sku: str, reorder_decision: Dict, rationale: Dict) -> str:
        """Create or update Notion reorder page via MCP connector."""
        try:
            # Create ReorderRequest object for MCP connector
            from src.connectors.unified_mcp_connector import ReorderRequest
            
            reorder_request = ReorderRequest(
                sku=sku,
                quantity=reorder_decision.get('qty', 0),
                vendor=reorder_decision.get('vendor', ''),
                cost=reorder_decision.get('total_cost', 0),
                rationale=rationale.get('paragraph', '')
            )
            
            page_id = self.mcp_connector.create_reorder_page(reorder_request)
            self._log_action(sku, "notion_page_created", f"Page ID: {page_id}", "success")
            return page_id
            
        except Exception as e:
            self.logger.error(f"Failed to update Notion page via MCP for {sku}: {e}")
            # Fallback to legacy connector
            try:
                self.logger.info("Falling back to legacy notion connector")
                
                # Call legacy connector with the correct arguments
                page_id = self.legacy_notion_connector.create_reorder_page(
                    sku=sku,
                    qty=reorder_decision.get('qty', 0),
                    vendor_name=reorder_decision.get('vendor', ''),
                    total_cost=reorder_decision.get('total_cost', 0),
                    eoq=reorder_decision.get('qty', 0),  # Use qty as EOQ if not available
                    forecast_text=f"Forecast: {reorder_decision.get('forecast_text', 'Automated forecast based on demand analysis')}",
                    evidence_list=rationale.get('bullets', ['Automated reorder recommendation'])
                )
                
                self._log_action(sku, "notion_page_created", f"Page ID: {page_id}", "success")
                return page_id
            except Exception as fallback_error:
                self.logger.error(f"Legacy notion connector also failed: {fallback_error}")
                self._log_action(sku, "notion_page_error", str(e), "error")
                return ""
    
    async def _mark_notion_as_ordered(self, page_id: str, order_id: str):
        """Mark Notion page as ordered with order ID via MCP connector."""
        try:
            self.mcp_connector.update_notion_page(page_id, {"status": "ordered", "order_id": order_id})
            self.logger.info(f"Notion page {page_id} marked as ordered via MCP")
        except Exception as e:
            self.logger.error(f"Failed to mark Notion page as ordered via MCP: {e}")
            # Fallback to legacy connector
            try:
                self.logger.info("Falling back to legacy notion connector")
                await self.legacy_notion_connector.update_page_status(page_id, "ordered", {"order_id": order_id})
                self.logger.info(f"Notion page {page_id} marked as ordered via legacy connector")
            except Exception as fallback_error:
                self.logger.error(f"Legacy notion connector also failed: {fallback_error}")
    
    async def _place_auto_order(self, sku: str, reorder_decision: Dict) -> Dict:
        """Place automatic order via supplier connector."""
        try:
            order_result = await self.supplier_connector.place_order(
                vendor_id=reorder_decision.get('vendor', ''),
                sku=sku,
                qty=reorder_decision.get('qty', 0)
            )
            
            if order_result.get('order_id'):
                self._log_action(
                    sku, "auto_order_placed", 
                    f"Order ID: {order_result['order_id']}", 
                    "success",
                    order_id=order_result['order_id'],
                    cost=reorder_decision.get('total_cost', 0),
                    vendor=reorder_decision.get('vendor', '')
                )
                return {"success": True, "order_id": order_result['order_id']}
            else:
                self._log_action(sku, "auto_order_failed", "No order ID returned", "error")
                return {"success": False, "error": "No order ID returned"}
                
        except Exception as e:
            error_msg = f"Auto order failed: {str(e)}"
            self._log_action(sku, "auto_order_failed", error_msg, "error")
            return {"success": False, "error": error_msg}
    
    def _send_batch_approval_email(self, approval_requests: List[Dict]):
        """Send a single batch approval email for multiple reorder requests."""
        if not approval_requests:
            return
        
        self.logger.info(f"Sending batch approval email for {len(approval_requests)} reorder requests")
        
        # Create batch email subject
        subject = f"Batch Reorder Approval Required - {len(approval_requests)} Items"
        
        # Create batch HTML body
        html_body = self._create_batch_email_html(approval_requests)
        
        # Create batch ReorderRequest object for webhook handling
        from src.connectors.unified_mcp_connector import ReorderRequest
        batch_request = ReorderRequest(
            sku="BATCH",
            quantity=sum(req["reorder_decision"]["qty"] for req in approval_requests),
            vendor="MULTIPLE",
            cost=sum(req["reorder_decision"]["total_cost"] for req in approval_requests),
            rationale=f"Batch approval for {len(approval_requests)} items",
            urgency="medium",
            auto_approve=False
        )
        
        # Generate batch token for webhook handling
        import uuid
        batch_token = str(uuid.uuid4())
        
        # Store batch approval data
        from src.webhook.app import store_pending_approval
        batch_action_data = {
            'sku': 'BATCH',
            'action_type': 'batch_reorder',
            'vendor': 'MULTIPLE',  # Required field for pending actions manager
            'quantity': sum(req["reorder_decision"]["qty"] for req in approval_requests),
            'total_cost': sum(req["reorder_decision"]["total_cost"] for req in approval_requests),
            'rationale': f"Batch approval for {len(approval_requests)} items",
            'items': [
                {
                    'sku': req["sku"],
                    'vendor': req["reorder_decision"]["vendor"],
                    'quantity': req["reorder_decision"]["qty"],
                    'total_cost': req["reorder_decision"]["total_cost"],
                    'notion_page_id': req["notion_page_id"]
                }
                for req in approval_requests
            ]
        }
        
        if not store_pending_approval(batch_token, batch_action_data):
            self.logger.error("Failed to store batch pending approval")
            return
        
        # Create batch approval/rejection URLs
        base_url = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
        approve_params = urlencode({
            "token": batch_token,
            "secret": self.webhook_secret
        })
        reject_params = urlencode({
            "token": batch_token,
            "secret": self.webhook_secret
        })
        
        approve_url = f"{base_url}/webhook/approve-batch?{approve_params}"
        reject_url = f"{base_url}/webhook/reject-batch?{reject_params}"
        
        # Send via MCP connector
        try:
            html_body = self._create_batch_email_html(approval_requests)
            message_id = self.mcp_connector.send_approval_email(
                reorder_request=batch_request,
                approve_url=approve_url,
                reject_url=reject_url,
                notion_page_id="BATCH",
                custom_html=html_body
            )
            
            if message_id:
                self.logger.info(f"Batch approval email sent successfully for {len(approval_requests)} items, Message ID: {message_id}")
            else:
                self.logger.error(f"Failed to send batch approval email for {len(approval_requests)} items")
                
        except Exception as e:
            self.logger.error(f"Error sending batch approval email: {e}")
    
    def _create_batch_email_html(self, approval_requests: List[Dict]) -> str:
        """Create HTML body for batch approval email."""
        total_cost = sum(req["reorder_decision"]["total_cost"] for req in approval_requests)
        
        # Debug logging for batch email generation
        self.logger.info(f"DEBUG BATCH: approval_requests count: {len(approval_requests)}")
        for i, req in enumerate(approval_requests):
            self.logger.info(f"DEBUG BATCH req[{i}]: reorder_decision keys: {list(req['reorder_decision'].keys())}")
            self.logger.info(f"DEBUG BATCH req[{i}]: total_cost value: {req['reorder_decision'].get('total_cost', 'NOT_FOUND')}")
        self.logger.info(f"DEBUG BATCH: calculated total_cost: {total_cost}")
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .summary {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .item {{ border: 1px solid #dee2e6; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .item-header {{ font-weight: bold; color: #495057; margin-bottom: 10px; }}
                .rationale {{ background-color: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; }}
                .buttons {{ text-align: center; margin: 20px 0; }}
                .approve-btn {{ background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 0 10px; }}
                .reject-btn {{ background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 0 10px; }}
                .cost {{ font-weight: bold; color: #28a745; }}
                .vendor {{ color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🛒 Batch Reorder Approval Required</h2>
                <p>The following {len(approval_requests)} items require approval for reordering:</p>
            </div>
            
            <div class="summary">
                <h3>📊 Batch Summary</h3>
                <p><strong>Total Items:</strong> {len(approval_requests)}</p>
                <p><strong>Total Cost:</strong> <span class="cost">${total_cost:.2f}</span></p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        for i, req in enumerate(approval_requests, 1):
            reorder_decision = req["reorder_decision"]
            rationale = req["rationale"]
            
            html += f"""
            <div class="item">
                <div class="item-header">
                    {i}. SKU: {req["sku"]} | Qty: {reorder_decision["qty"]} | 
                    <span class="vendor">Vendor: {reorder_decision["vendor"]}</span> | 
                    <span class="cost">Cost: ${reorder_decision["total_cost"]:.2f}</span>
                </div>
                
                <div class="rationale">
                    <h4>📝 Rationale:</h4>
                    <p>{rationale.get("paragraph", "No rationale provided")}</p>
                    <ul>
            """
            
            for bullet in rationale.get("bullets", []):
                html += f"<li>{bullet}</li>"
            
            html += """
                    </ul>
                </div>
            </div>
            """
        
        html += f"""
            <div class="buttons">
                <p><strong>Choose an action for all items:</strong></p>
                <a href="{{approve_url}}" class="approve-btn">✅ Approve All</a>
                <a href="{{reject_url}}" class="reject-btn">❌ Reject All</a>
            </div>
            
            <p><em>Note: This is an automated batch approval request. Individual item approvals can be handled through the Notion dashboard.</em></p>
        </body>
        </html>
        """
        
        return html

    def _send_approval_email(self, sku: str, reorder_decision: Dict, rationale: Dict, notion_page_id: str):
        """Send approval email with rationale and approve/reject links."""
        try:
            # Get manager email from environment
            manager_email = os.getenv('MANAGER_EMAIL', 'manager@company.com')
            
            # Generate unique token for this approval request
            import uuid
            token = str(uuid.uuid4())
            
            # Store pending action data
            action_data = {
                'sku': sku,
                'action_type': 'reorder',
                'vendor': reorder_decision.get('vendor', 'Unknown Vendor'),
                'quantity': reorder_decision.get('qty', 0),
                'total_cost': reorder_decision.get('total_cost', 0),
                'rationale': rationale.get('paragraph', ''),
                'notion_page_id': notion_page_id or ''
            }
            
            # Import and use the store function from webhook app
            from src.webhook.app import store_pending_approval
            if not store_pending_approval(token, action_data):
                self.logger.error(f"Failed to store pending action for {sku}")
                return
            
            # Create approval/rejection URLs with token and secret
            base_url = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
            approve_params = urlencode({
                "token": token,
                "secret": self.webhook_secret
            })
            reject_params = urlencode({
                "token": token,
                "secret": self.webhook_secret
            })
            
            approve_url = f"{base_url}/webhook/approve?{approve_params}"
            reject_url = f"{base_url}/webhook/reject?{reject_params}"
            
            # Create email subject
            subject = f"Approval Required: Reorder {sku} ({reorder_decision.get('qty', 0)} units)"
            
            # Create email body HTML
            vendor = reorder_decision.get('vendor', 'Unknown Vendor')
            total_cost = reorder_decision.get('total_cost', 0)
            
            # Debug logging for email generation
            self.logger.info(f"DEBUG EMAIL: reorder_decision keys: {list(reorder_decision.keys())}")
            self.logger.info(f"DEBUG EMAIL: reorder_decision content: {reorder_decision}")
            self.logger.info(f"DEBUG EMAIL: extracted total_cost: {total_cost}")
            
            rationale_paragraph = rationale.get('paragraph', '')
            rationale_bullets = rationale.get('bullets', [])
            evidence_summary = reorder_decision.get('evidence_summary', '')
            
            bullets_html = ""
            if rationale_bullets:
                bullets_html = "<ul>" + "".join([f"<li>{bullet}</li>" for bullet in rationale_bullets]) + "</ul>"
            
            html_body = f"""
            <h2>Inventory Replenishment Request</h2>
            <p><strong>SKU:</strong> {sku}</p>
            <p><strong>Recommended Quantity:</strong> {reorder_decision.get('qty', 0)} units</p>
            <p><strong>Vendor:</strong> {vendor}</p>
            <p><strong>Total Cost:</strong> ${total_cost:.2f}</p>
            
            <h3>AI Rationale</h3>
            <p>{rationale_paragraph}</p>
            {bullets_html}
            
            <h3>Evidence Summary</h3>
            <p>{evidence_summary}</p>
            
            <p><strong>Notion Page:</strong> <a href="https://notion.so/{notion_page_id}">View Details</a></p>
            """
            
            # Create ReorderRequest object for MCP connector
            from src.connectors.unified_mcp_connector import ReorderRequest
            
            # Extract unit cost from best vendor data (price_per_unit)
            # The cost field in ReorderRequest should be unit cost, not total cost
            unit_cost = 0
            if 'best_vendor' in reorder_decision:
                unit_cost = reorder_decision['best_vendor'].get('price_per_unit', 0)
            elif 'price_per_unit' in reorder_decision:
                unit_cost = reorder_decision.get('price_per_unit', 0)
            
            reorder_request = ReorderRequest(
                sku=sku,
                quantity=reorder_decision.get('qty', 0),
                vendor=vendor,
                cost=unit_cost,  # Use unit cost, not total cost
                rationale=rationale_paragraph,
                urgency=reorder_decision.get('urgency', 'medium'),
                auto_approve=False
            )
            
            # Send the email via MCP connector for Gmail integration
            self.logger.info("Using MCP connector for Gmail approval email")
            
            # Send email using MCP connector
            message_id = self.mcp_connector.send_approval_email(
                reorder_request=reorder_request,
                approve_url=approve_url,
                reject_url=reject_url,
                notion_page_id=notion_page_id or ""
            )
            
            if message_id:
                self._log_action(sku, "approval_email_sent", f"Sent via MCP Gmail, Message ID: {message_id}, Notion page: {notion_page_id}", "success")
            else:
                self._log_action(sku, "approval_email_error", "Failed to send via MCP Gmail", "error")
            
        except Exception as e:
            error_msg = f"Failed to send approval email: {str(e)}"
            self.logger.error(error_msg)
            self._log_action(sku, "approval_email_error", error_msg, "error")
    
    async def _update_sheet_status(self, sku: str, status: str, order_id: str = ""):
        """Update Google Sheet with order status and ID via MCP connector."""
        try:
            # For now, this functionality is not implemented in MCP connector
            # We'll use the legacy connector as fallback
            self.logger.info("Sheet status update not yet implemented in MCP connector, using legacy")
            await self.legacy_sheets_connector.update_item_status(sku, status, order_id)
            self._log_action(sku, "sheet_updated", f"Status: {status}, Order ID: {order_id}", "success")
        except Exception as e:
            error_msg = f"Failed to update sheet: {str(e)}"
            self.logger.error(error_msg)
            self._log_action(sku, "sheet_update_error", error_msg, "error")

def main():
    """Entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(description="Inventory Intelligence Tool (IIT) Agent")
    parser.add_argument("--run-once", action="store_true", help="Run a single cycle and exit")
    parser.add_argument("--dry-run", action="store_true", help="Run without placing actual orders")
    parser.add_argument("--interval", type=int, default=3600, help="Check interval in seconds (default: 3600)")
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = InventoryAgent(dry_run=args.dry_run)
    
    async def run_agent():
        """Run the agent with specified parameters."""
        if args.run_once:
            # Single cycle
            results = await agent.run_cycle()
            print(f"\n=== Cycle Results ===")
            print(json.dumps(results, indent=2))
        else:
            # Continuous loop
            agent.logger.info(f"Starting continuous agent loop (interval: {args.interval}s)")
            try:
                while True:
                    await agent.run_cycle()
                    agent.logger.info(f"Sleeping for {args.interval} seconds...")
                    await asyncio.sleep(args.interval)
            except KeyboardInterrupt:
                agent.logger.info("Agent stopped by user")
            except Exception as e:
                agent.logger.error(f"Agent error: {str(e)}")
                raise
    
    # Run the agent
    asyncio.run(run_agent())

if __name__ == "__main__":
    main()