"""
Unified MCP Connector for Inventory Intelligence Tool (IIT)

This module provides a unified connector that integrates Gmail, Notion, and Google Sheets
operations through the MCP (Model Context Protocol) interface, replacing individual
connector classes with a single, cohesive integration point.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

from src.connectors.mcp_client import SyncComposioMCPClient, ComposioMCPClient

logger = logging.getLogger(__name__)

@dataclass
class InventoryItem:
    """Represents an inventory item with all necessary fields"""
    sku: str
    current_stock: int
    reorder_point: int
    reorder_quantity: int
    vendor: str
    cost: float
    description: str = ""
    category: str = ""
    last_updated: Optional[str] = None

@dataclass
class ReorderRequest:
    """Represents a reorder request with all necessary information"""
    sku: str
    quantity: int
    vendor: str
    cost: float
    rationale: str
    urgency: str = "medium"
    auto_approve: bool = False

class UnifiedMCPConnector:
    """
    Unified MCP Connector for IIT System
    
    Provides a single interface for all external integrations:
    - Gmail: Email notifications and approval workflows
    - Notion: Reorder page creation and management
    - Google Sheets: Inventory data reading and status updates
    """
    
    def __init__(self, demo_mode: bool = False):
        """
        Initialize the unified MCP connector
        
        Args:
            demo_mode: If True, operates in demo mode without actual API calls
        """
        self.demo_mode = demo_mode
        self.logger = logging.getLogger(__name__)
        
        # MCP server configuration - use remote Composio server
        self.mcp_server_url = os.getenv(
            "MCP_SERVER_URL", 
            "https://backend.composio.dev/v3/mcp/46756fc9-c9eb-4c7e-befb-48bbcc5237eb/mcp?user_id=pg-test-ff446a18-1872-4af1-a75b-99f52098cf11"
        )
        
        # Initialize MCP client
        self.mcp_client = None
        self._initialize_mcp_client()
        
        # Configuration from environment
        self.spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
        self.notion_db_id = os.getenv("NOTION_DB_ID")
        self.manager_email = os.getenv("MANAGER_EMAIL")
        
        self.logger.info(f"Unified MCP Connector initialized (demo_mode={demo_mode})")
    
    def _initialize_mcp_client(self):
        """Initialize the MCP client connection"""
        try:
            if not self.demo_mode:
                self.mcp_client = SyncComposioMCPClient(self.mcp_server_url)
                self.mcp_client.connect()
                self.logger.info("MCP client connected successfully")
            else:
                self.logger.info("Running in demo mode - MCP client not initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP client: {e}")
            if not self.demo_mode:
                raise
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def disconnect(self):
        """Disconnect from MCP server"""
        if self.mcp_client:
            try:
                self.mcp_client.disconnect()
                self.logger.info("MCP client disconnected")
            except Exception as e:
                self.logger.error(f"Error disconnecting MCP client: {e}")
    
    # ==================== GOOGLE SHEETS OPERATIONS ====================
    
    async def read_inventory_data(self) -> List[InventoryItem]:
        """
        Read inventory data from Google Sheets
        
        Returns:
            List of InventoryItem objects
        """
        if self.demo_mode:
            return self._get_demo_inventory_data()

        try:
            self.logger.info("Reading inventory data from Google Sheets via MCP...")
            
            # Use async client to avoid event loop conflicts
            async_client = ComposioMCPClient(self.mcp_server_url)
            await async_client.connect()
            
            try:
                result = await async_client.execute_tool(
                    "GOOGLESHEETS_BATCH_GET",
                    {
                        "spreadsheet_id": self.spreadsheet_id,
                        "ranges": ["Inventory!A:J"]  # Use the Inventory sheet instead of Sheet1
                    }
                )
            finally:
                await async_client.disconnect()
            
            # Handle the MCP response format
            if result and not result.get("isError", True):
                content = result.get("content", [])
                if content and len(content) > 0:
                    # Parse the JSON content from the text response
                    import json
                    text_content = content[0].get("text", "")
                    if text_content:
                        data = json.loads(text_content)
                        if data.get("successful") and "data" in data:
                            value_ranges = data["data"].get("valueRanges", [])
                            if value_ranges and len(value_ranges) > 0:
                                first_range = value_ranges[0]
                                if "values" in first_range:
                                    rows = first_range["values"]
                                    self.logger.info(f"Retrieved {len(rows)} rows from Google Sheets")
                                    return self._parse_inventory_rows(rows)
            
            self.logger.warning("No data found in Google Sheets")
            return []
                
        except Exception as e:
            self.logger.error(f"Error reading inventory data: {e}")
            return []
    
    def update_inventory_status(self, sku: str, status: str, order_id: str = "") -> bool:
        """
        Update inventory status in Google Sheets
        
        Args:
            sku: Product SKU
            status: New status (e.g., "ORDERED", "DELIVERED")
            order_id: Optional order ID
            
        Returns:
            True if successful, False otherwise
        """
        if self.demo_mode:
            self.logger.info(f"[DEMO] Would update {sku} status to {status} (Order: {order_id})")
            return True
        
        try:
            # Find the row for this SKU and update status
            # This is a simplified implementation - you may need to adjust based on your sheet structure
            result = self.mcp_client.execute_tool(
                "GOOGLESHEETS_UPDATE_RANGE",
                {
                    "spreadsheet_id": self.spreadsheet_id,
                    "range": f"Inventory!I{self._find_sku_row(sku)}",  # Assuming status is in column I
                    "values": [[status]],
                    "value_input_option": "RAW"
                }
            )
            
            return result.get("success", False)
            
        except Exception as e:
            self.logger.error(f"Error updating inventory status: {e}")
            return False
    
    def _find_sku_row(self, sku: str) -> int:
        """Find the row number for a given SKU (simplified implementation)"""
        # This is a placeholder - implement actual SKU lookup logic
        return 2  # Default to row 2 for demo
    
    def _parse_inventory_rows(self, rows: List[List]) -> List[InventoryItem]:
        """Parse raw sheet rows into InventoryItem objects"""
        items = []
        if not rows or len(rows) < 2:  # Skip header row
            return items
        
        headers = rows[0]
        self.logger.info(f"Parsing {len(rows)-1} inventory rows with headers: {headers}")
        
        for i, row in enumerate(rows[1:], 1):
            if len(row) >= 4:  # Ensure minimum required columns
                try:
                    # Map the columns based on actual data format:
                    # ['SKU', 'Description', 'OnHand', 'Unit', 'LeadTimeDays', 'MinOrderQty', 'VendorIDs', 'AutoOrderThreshold', 'TrustScore']
                    sku = str(row[0]) if row[0] else f"UNKNOWN-{i}"
                    description = str(row[1]) if len(row) > 1 and row[1] else "Unknown Product"
                    current_stock = int(float(str(row[2]))) if len(row) > 2 and row[2] else 0
                    # Skip unit column (row[3]) as it's text, not numeric
                    lead_time_days = int(float(str(row[4]))) if len(row) > 4 and row[4] else 7
                    min_order_qty = int(float(str(row[5]))) if len(row) > 5 and row[5] else 10
                    vendor_ids = str(row[6]) if len(row) > 6 and row[6] else "Unknown Vendor"
                    auto_order_threshold = int(float(str(row[7]))) if len(row) > 7 and row[7] else 50
                    trust_score = float(str(row[8])) if len(row) > 8 and row[8] else 80.0
                    
                    # Use auto_order_threshold as reorder_point and min_order_qty as reorder_quantity
                    # Calculate cost based on trust_score (higher trust = lower cost)
                    cost = max(1.0, 100.0 - trust_score)
                    
                    item = InventoryItem(
                        sku=sku,
                        current_stock=current_stock,
                        reorder_point=auto_order_threshold,
                        reorder_quantity=min_order_qty,
                        vendor=vendor_ids,
                        cost=cost,
                        description=description,
                        category="General",
                        last_updated=datetime.now().isoformat()
                    )
                    
                    items.append(item)
                    self.logger.debug(f"Parsed item: {sku} - Stock: {current_stock}, Reorder Point: {auto_order_threshold}")
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Skipping invalid row {i} {row}: {e}")
                    continue
            else:
                self.logger.warning(f"Skipping row {i} with insufficient columns: {row}")
        
        self.logger.info(f"Successfully parsed {len(items)} inventory items")
        return items
    
    def _get_demo_inventory_data(self) -> List[InventoryItem]:
        """Return demo inventory data for testing with realistic variations"""
        return [
            InventoryItem(
                sku="SAFETY-001",
                current_stock=3,
                reorder_point=10,
                reorder_quantity=44,
                vendor="Safety First Equipment",
                cost=65.00,
                description="Safety Helmet",
                category="Safety Equipment"
            ),
            InventoryItem(
                sku="BREAK-002",
                current_stock=15,
                reorder_point=25,
                reorder_quantity=44,
                vendor="Industrial Supply Co",
                cost=12.50,
                description="Break Room Supplies",
                category="Office Supplies"
            ),
            InventoryItem(
                sku="BREAK-001",
                current_stock=22,
                reorder_point=30,
                reorder_quantity=44,
                vendor="Premium Office Solutions",
                cost=8.75,
                description="Break Room Equipment",
                category="Office Supplies"
            ),
            InventoryItem(
                sku="TECH-002",
                current_stock=4,
                reorder_point=12,
                reorder_quantity=44,
                vendor="TechSupply Corp",
                cost=320.00,
                description="Monitor Display",
                category="Electronics"
            ),
            InventoryItem(
                sku="TECH-001",
                current_stock=6,
                reorder_point=15,
                reorder_quantity=44,
                vendor="Digital Components Ltd",
                cost=850.00,
                description="Laptop Computer",
                category="Electronics"
            ),
            InventoryItem(
                sku="CLEAN-002",
                current_stock=18,
                reorder_point=35,
                reorder_quantity=44,
                vendor="CleanCorp Industries",
                cost=25.00,
                description="Cleaning Towels",
                category="Cleaning Supplies"
            ),
            InventoryItem(
                sku="CLEAN-001",
                current_stock=12,
                reorder_point=30,
                reorder_quantity=44,
                vendor="Professional Cleaning Co",
                cost=45.00,
                description="Industrial Soap",
                category="Cleaning Supplies"
            ),
            InventoryItem(
                sku="OFFICE-003",
                current_stock=25,
                reorder_point=40,
                reorder_quantity=44,
                vendor="Stationery World",
                cost=12.50,
                description="Office Pens",
                category="Office Supplies"
            ),
            InventoryItem(
                sku="OFFICE-002",
                current_stock=8,
                reorder_point=20,
                reorder_quantity=44,
                vendor="Office Furniture Plus",
                cost=245.00,
                description="Office Chair",
                category="Furniture"
            ),
            InventoryItem(
                sku="OFFICE-001",
                current_stock=35,
                reorder_point=50,
                reorder_quantity=44,
                vendor="Paper Solutions Co",
                cost=25.00,
                description="Office Paper A4",
                category="Office Supplies"
            )
        ]
    
    # ==================== NOTION OPERATIONS ====================
    
    def create_reorder_page(self, reorder_request: ReorderRequest) -> Optional[str]:
        """
        Create a reorder page in Notion
        
        Args:
            reorder_request: ReorderRequest object with all details
            
        Returns:
            Page ID if successful, None otherwise
        """
        if self.demo_mode:
            page_id = f"demo_page_{int(datetime.now().timestamp())}"
            self._save_demo_notion_page(page_id, reorder_request)
            return page_id
        
        try:
            # Check if NOTION_CREATE_NOTION_PAGE tool is available (correct tool name)
            available_tools = self.mcp_client.get_available_tools()
            if "NOTION_CREATE_NOTION_PAGE" not in available_tools:
                self.logger.error(f"Tool 'NOTION_CREATE_NOTION_PAGE' not available. Available tools: {available_tools}")
                return None
            
            # Create Notion page using MCP
            page_data = {
                "parent": {"database_id": self.notion_db_id},
                "properties": {
                    "SKU": {"title": [{"text": {"content": reorder_request.sku}}]},
                    "Quantity": {"number": reorder_request.quantity},
                    "Vendor": {"rich_text": [{"text": {"content": reorder_request.vendor}}]},
                    "Cost": {"number": reorder_request.cost},
                    "Status": {"select": {"name": "Pending Approval"}},
                    "Urgency": {"select": {"name": reorder_request.urgency.title()}},
                    "Auto Approve": {"checkbox": reorder_request.auto_approve}
                },
                "children": [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Reorder Rationale"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": reorder_request.rationale}}]
                        }
                    }
                ]
            }
            
            self.logger.info(f"Attempting to create Notion page for {reorder_request.sku} with data: {page_data}")
            
            result = self.mcp_client.execute_tool(
                "NOTION_CREATE_NOTION_PAGE",
                {"page_data": page_data}
            )
            
            self.logger.info(f"MCP tool result: {result}")
            
            if result and result.get("success"):
                page_id = result.get("data", {}).get("id")
                self.logger.info(f"Created Notion page for {reorder_request.sku}: {page_id}")
                return page_id
            else:
                error_msg = result.get('error') if result else "No result returned from MCP tool"
                self.logger.error(f"Failed to create Notion page: {error_msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating Notion page: {e}")
            return None
    
    def update_reorder_status(self, page_id: str, status: str, order_id: str = "") -> bool:
        """
        Update the status of a reorder page in Notion
        
        Args:
            page_id: Notion page ID
            status: New status
            order_id: Optional order ID
            
        Returns:
            True if successful, False otherwise
        """
        if self.demo_mode:
            self.logger.info(f"[DEMO] Would update Notion page {page_id} status to {status}")
            return True
        
        try:
            update_data = {
                "properties": {
                    "Status": {"select": {"name": status}}
                }
            }
            
            if order_id:
                update_data["properties"]["Order ID"] = {
                    "rich_text": [{"text": {"content": order_id}}]
                }
            
            result = self.mcp_client.execute_tool(
                "NOTION_UPDATE_PAGE",
                {
                    "page_id": page_id,
                    "page_data": update_data
                }
            )
            
            return result.get("success", False)
            
        except Exception as e:
            self.logger.error(f"Error updating Notion page status: {e}")
            return False
    
    def _save_demo_notion_page(self, page_id: str, reorder_request: ReorderRequest):
        """Save demo Notion page data to file"""
        demo_dir = "demo/notion_pages"
        os.makedirs(demo_dir, exist_ok=True)
        
        page_data = {
            "id": page_id,
            "sku": reorder_request.sku,
            "quantity": reorder_request.quantity,
            "vendor": reorder_request.vendor,
            "cost": reorder_request.cost,
            "rationale": reorder_request.rationale,
            "urgency": reorder_request.urgency,
            "auto_approve": reorder_request.auto_approve,
            "created_at": datetime.now().isoformat()
        }
        
        with open(f"{demo_dir}/{page_id}.json", "w") as f:
            json.dump(page_data, f, indent=2)
        
        self.logger.info(f"[DEMO] Saved Notion page data to {demo_dir}/{page_id}.json")
    
    # ==================== GMAIL OPERATIONS ====================
    
    def send_approval_email(self, reorder_request: ReorderRequest, 
                          approve_url: str, reject_url: str,
                          notion_page_id: str = "", custom_html: str = "") -> Optional[str]:
        """
        Send approval email for reorder request (individual or batch)
        
        Args:
            reorder_request: ReorderRequest object
            approve_url: URL for approval action
            reject_url: URL for rejection action
            notion_page_id: Optional Notion page ID for reference
            custom_html: Optional custom HTML body (for batch emails)
            
        Returns:
            Message ID if successful, None otherwise
        """
        if self.demo_mode:
            return self._save_demo_email(reorder_request, approve_url, reject_url, notion_page_id)
        
        try:
            # Check if manager_email is configured
            if not self.manager_email:
                self.logger.error("MANAGER_EMAIL not configured - cannot send approval email")
                return None
            
            # Prepare email content
            if reorder_request.sku == "BATCH":
                subject = f"Batch Reorder Approval Required - Multiple Items"
            else:
                subject = f"Reorder Approval Required: {reorder_request.sku}"
            
            # Use custom HTML if provided (for batch emails), otherwise generate standard HTML
            if custom_html:
                # Replace placeholders in custom HTML with actual URLs
                html_body = custom_html.replace("{approve_url}", approve_url).replace("{reject_url}", reject_url)
            else:
                html_body = self._generate_approval_email_html(
                    reorder_request, approve_url, reject_url, notion_page_id
                )
            
            self.logger.info(f"Sending email to: {self.manager_email}")
            self.logger.info(f"Subject: {subject}")
            
            # Send email using MCP
            result = self.mcp_client.execute_tool(
                "GMAIL_SEND_EMAIL",
                {
                    "recipient_email": self.manager_email,
                    "subject": subject,
                    "body": html_body,
                    "is_html": True
                }
            )
            
            self.logger.info(f"MCP Gmail result: {result}")
            
            if result and result.get("success"):
                message_id = result.get("data", {}).get("id", "unknown")
                if reorder_request.sku == "BATCH":
                    self.logger.info(f"Sent batch approval email: {message_id}")
                else:
                    self.logger.info(f"Sent approval email for {reorder_request.sku}: {message_id}")
                return message_id
            else:
                error_msg = result.get('error') if result else "No result returned"
                self.logger.error(f"Failed to send approval email: {error_msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error sending approval email: {e}")
            return None
    
    def _generate_approval_email_html(self, reorder_request: ReorderRequest,
                                    approve_url: str, reject_url: str,
                                    notion_page_id: str = "") -> str:
        """Generate HTML content for approval email"""
        total_cost = reorder_request.quantity * reorder_request.cost
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f8ff; padding: 20px; border-radius: 8px; }}
                .content {{ margin: 20px 0; }}
                .details {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
                .actions {{ margin: 30px 0; text-align: center; }}
                .btn {{ padding: 12px 24px; margin: 0 10px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                .approve {{ background-color: #28a745; color: white; }}
                .reject {{ background-color: #dc3545; color: white; }}
                .rationale {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🏭 Inventory Reorder Approval Required</h2>
                <p>A reorder request has been generated by the Inventory Intelligence Tool</p>
            </div>
            
            <div class="content">
                <div class="details">
                    <h3>📦 Reorder Details</h3>
                    <p><strong>SKU:</strong> {reorder_request.sku}</p>
                    <p><strong>Quantity:</strong> {reorder_request.quantity} units</p>
                    <p><strong>Vendor:</strong> {reorder_request.vendor}</p>
                    <p><strong>Unit Cost:</strong> ${reorder_request.cost:.2f}</p>
                    <p><strong>Total Cost:</strong> ${total_cost:.2f}</p>
                    <p><strong>Urgency:</strong> {reorder_request.urgency.title()}</p>
                </div>
                
                <div class="rationale">
                    <h4>🤖 AI Rationale</h4>
                    <p>{reorder_request.rationale}</p>
                </div>
                
                {f'<p><strong>📋 Notion Page:</strong> <a href="https://notion.so/{notion_page_id}">View Details</a></p>' if notion_page_id else ''}
            </div>
            
            <div class="actions">
                <h3>Please choose an action:</h3>
                <a href="{approve_url}" class="btn approve">✅ APPROVE ORDER</a>
                <a href="{reject_url}" class="btn reject">❌ REJECT ORDER</a>
            </div>
            
            <hr>
            <p><small>This email was generated automatically by the Inventory Intelligence Tool (IIT)</small></p>
        </body>
        </html>
        """
        
        return html
    
    def _save_demo_email(self, reorder_request: ReorderRequest,
                        approve_url: str, reject_url: str,
                        notion_page_id: str = "") -> str:
        """Save demo email to file"""
        demo_dir = "demo/outbox"
        os.makedirs(demo_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        message_id = f"msg_{hash(reorder_request.sku) % 1000000:06x}_{int(datetime.now().timestamp())}"
        filename = f"{timestamp}_{message_id}.html"
        
        html_content = self._generate_approval_email_html(
            reorder_request, approve_url, reject_url, notion_page_id
        )
        
        with open(f"{demo_dir}/{filename}", "w") as f:
            f.write(html_content)
        
        self.logger.info(f"[DEMO] Saved approval email to {demo_dir}/{filename}")
        return message_id
    
    # ==================== UTILITY METHODS ====================
    
    def get_available_tools(self) -> List[str]:
        """Get list of available MCP tools"""
        if self.demo_mode or not self.mcp_client:
            return ["DEMO_MODE"]
        
        try:
            return self.mcp_client.get_available_tools()
        except Exception as e:
            self.logger.error(f"Error getting available tools: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all integrations"""
        status = {
            "mcp_connected": False,
            "gmail_available": False,
            "notion_available": False,
            "sheets_available": False,
            "demo_mode": self.demo_mode
        }
        
        if self.demo_mode:
            status.update({
                "mcp_connected": True,
                "gmail_available": True,
                "notion_available": True,
                "sheets_available": True
            })
            return status
        
        if self.mcp_client:
            try:
                tools = self.mcp_client.get_available_tools()
                status["mcp_connected"] = True
                status["gmail_available"] = any("GMAIL" in tool for tool in tools)
                status["notion_available"] = any("NOTION" in tool for tool in tools)
                status["sheets_available"] = any("GOOGLESHEETS" in tool for tool in tools)
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
        
        return status