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

from composio_core import ComposioToolSet, WorkspaceType
from dotenv import load_dotenv
import os

# Import all our modules
from .connectors.sheets_connector import SheetsConnector
from .connectors.notion_connector import NotionConnector
from .connectors.email_connector import EmailConnector
from .connectors.supplier_connector import SupplierConnector
# Import Composio connectors for production use
from .connectors.composio_email_connector import ComposioEmailConnector
from .connectors.composio_notion_connector import ComposioNotionConnector
from .policies.reorder_policy import ReorderPolicy
from .models.llm_rationale import generate_rationale
from .utils.logger import setup_logger
from .utils.config import Config

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
        
        # Initialize connectors
        self.sheets_connector = SheetsConnector()
        
        # Use Composio connectors for production (default mode)
        self.notion_connector = ComposioNotionConnector(demo_mode=False)
        self.email_connector = ComposioEmailConnector(demo_mode=False)
        
        # Keep legacy connectors as fallback
        self.legacy_notion_connector = NotionConnector()
        self.legacy_email_connector = EmailConnector()
        
        self.supplier_connector = SupplierConnector()
        
        # Initialize policies
        self.reorder_policy = ReorderPolicy()
        
        # Initialize Composio toolset
        self.composio_api_key = os.getenv("COMPOSIO_API_KEY", "ak_7KV1PgJT2x0XIC_wqejz")
        self.webhook_secret = os.getenv("WEBHOOK_SECRET", "ed999b5c-aea7-44a8-b910-cae4b47cfb46")
        
        try:
            self.toolset = ComposioToolSet(
                workspace_config=WorkspaceType.Host(),
                api_key=self.composio_api_key
            )
            self.logger.info("Composio toolset initialized successfully")
        except Exception as e:
            self.logger.warning(f"Composio initialization failed: {e}. Continuing without Composio.")
            self.toolset = None
        
        # Initialize logging database
        self._init_logging_db()
        
        self.logger.info(f"Inventory Agent initialized (dry_run={dry_run})")
    
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
           e. Else send approval email with rationale and approve/reject links
        3. Update Google Sheet with status and order ID if placed
        4. Log actions into local SQLite or CSV
        
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
            "errors": [],
            "cycle_duration_seconds": 0
        }
        
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
                    await self._process_sku(sku_data, transaction_data, results)
                    results["processed_skus"] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing SKU {sku_data.get('sku', 'unknown')}: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
                    self._log_action(sku_data.get('sku', 'unknown'), "process_error", error_msg, "error")
            
            # Step 3: Final summary
            cycle_duration = time.time() - cycle_start
            results["cycle_duration_seconds"] = round(cycle_duration, 2)
            
            self.logger.info(f"=== Cycle Complete in {cycle_duration:.2f}s ===")
            self.logger.info(f"Processed: {results['processed_skus']} SKUs")
            self.logger.info(f"Reorders recommended: {results['reorders_recommended']}")
            self.logger.info(f"Auto orders placed: {results['auto_orders_placed']}")
            self.logger.info(f"Approval emails sent: {results['approval_emails_sent']}")
            
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
        """Fetch current inventory data from Google Sheets."""
        try:
            return await self.sheets_connector.get_inventory_data()
        except Exception as e:
            self.logger.error(f"Failed to fetch inventory data: {e}")
            return []
    
    async def _fetch_transaction_data(self) -> List[Dict]:
        """Fetch recent transaction data (last 90 days) from Google Sheets."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            return await self.sheets_connector.get_transaction_data(start_date, end_date)
        except Exception as e:
            self.logger.error(f"Failed to fetch transaction data: {e}")
            return []
    
    async def _process_sku(self, sku_data: Dict, transaction_data: List[Dict], results: Dict):
        """Process a single SKU through the complete reorder workflow."""
        sku = sku_data.get('sku', 'unknown')
        self.logger.info(f"Processing SKU: {sku}")
        
        # Step 2a: Run reorder policy to get recommendation
        sku_transactions = [t for t in transaction_data if t.get('sku') == sku]
        reorder_decision = self.reorder_policy.evaluate_reorder_need(
            sku=sku,
            on_hand=sku_data.get('on_hand', 0),
            transactions=sku_transactions
        )
        
        self._log_action(sku, "reorder_evaluation", json.dumps(reorder_decision), "success")
        
        if not reorder_decision.get('needs_reorder', False):
            self.logger.info(f"SKU {sku}: No reorder needed")
            return
        
        results["reorders_recommended"] += 1
        self.logger.info(f"SKU {sku}: Reorder recommended - Qty: {reorder_decision['qty']}, Vendor: {reorder_decision['vendor']}")
        
        # Step 2b: Generate LLM rationale
        rationale_context = {
            "sku": sku,
            "on_hand": sku_data.get('on_hand', 0),
            "weekly_demand": reorder_decision.get('weekly_demand', 0),
            "stockout_date": reorder_decision.get('stockout_date', 'unknown'),
            "best_vendor": reorder_decision.get('vendor', 'unknown'),
            "last_90d_stats": {
                "total_transactions": len(sku_transactions),
                "avg_daily_demand": reorder_decision.get('avg_daily', 0)
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
            else:
                # Auto order failed, send approval email
                await self._send_approval_email(sku, reorder_decision, rationale, notion_page_id)
                results["approval_emails_sent"] += 1
        else:
            # Step 2e: Send approval email
            await self._send_approval_email(sku, reorder_decision, rationale, notion_page_id)
            results["approval_emails_sent"] += 1
            reason = "dry_run" if self.dry_run else f"cost=${total_cost:.2f} > ${self.auto_order_threshold} or trust={vendor_trust_score:.2f} < {self.vendor_trust_threshold}"
            self.logger.info(f"SKU {sku}: Approval email sent ({reason})")
    
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
    
    async def _update_notion_page(self, sku: str, reorder_decision: Dict, rationale: Dict) -> str:
        """Create or update Notion reorder page."""
        try:
            page_data = {
                "sku": sku,
                "recommended_qty": reorder_decision.get('qty', 0),
                "vendor": reorder_decision.get('vendor', ''),
                "total_cost": reorder_decision.get('total_cost', 0),
                "rationale_paragraph": rationale.get('paragraph', ''),
                "rationale_bullets": rationale.get('bullets', []),
                "evidence_summary": reorder_decision.get('evidence_summary', ''),
                "status": "pending_approval",
                "created_at": datetime.now().isoformat()
            }
            
            page_id = await self.notion_connector.create_reorder_page(page_data)
            self._log_action(sku, "notion_page_created", f"Page ID: {page_id}", "success")
            return page_id
            
        except Exception as e:
            self.logger.error(f"Failed to update Notion page for {sku}: {e}")
            self._log_action(sku, "notion_page_error", str(e), "error")
            return ""
    
    async def _mark_notion_as_ordered(self, page_id: str, order_id: str):
        """Mark Notion page as ordered with order ID."""
        try:
            await self.notion_connector.update_page_status(page_id, "ordered", {"order_id": order_id})
            self.logger.info(f"Notion page {page_id} marked as ordered")
        except Exception as e:
            self.logger.error(f"Failed to mark Notion page as ordered: {e}")
    
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
    
    async def _send_approval_email(self, sku: str, reorder_decision: Dict, rationale: Dict, notion_page_id: str):
        """Send approval email with rationale and approve/reject links."""
        try:
            # Get manager email from environment
            manager_email = os.getenv('MANAGER_EMAIL', 'manager@company.com')
            
            # Create approval/rejection URLs with webhook secret
            base_url = os.getenv("WEBHOOK_BASE_URL", "https://your-webhook-domain.com")
            approve_params = urlencode({
                "action": "approve",
                "sku": sku,
                "page_id": notion_page_id,
                "secret": self.webhook_secret
            })
            reject_params = urlencode({
                "action": "reject", 
                "sku": sku,
                "page_id": notion_page_id,
                "secret": self.webhook_secret
            })
            
            approve_url = f"{base_url}/webhook/approval?{approve_params}"
            reject_url = f"{base_url}/webhook/approval?{reject_params}"
            
            # Create email subject
            subject = f"Approval Required: Reorder {sku} ({reorder_decision.get('qty', 0)} units)"
            
            # Create email body HTML
            vendor = reorder_decision.get('vendor', 'Unknown Vendor')
            total_cost = reorder_decision.get('total_cost', 0)
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
            
            # Send the email with correct parameters
            await self.email_connector.send_approval_email(
                to=manager_email,
                subject=subject,
                html_body=html_body,
                approve_link=approve_url,
                reject_link=reject_url
            )
            
            self._log_action(sku, "approval_email_sent", f"Sent to {manager_email}, Notion page: {notion_page_id}", "success")
            
        except Exception as e:
            error_msg = f"Failed to send approval email: {str(e)}"
            self.logger.error(error_msg)
            self._log_action(sku, "approval_email_error", error_msg, "error")
    
    async def _update_sheet_status(self, sku: str, status: str, order_id: str = ""):
        """Update Google Sheet with order status and ID."""
        try:
            await self.sheets_connector.update_item_status(sku, status, order_id)
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