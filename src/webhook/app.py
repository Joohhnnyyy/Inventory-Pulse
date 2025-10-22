"""
Approval Webhook Server for Inventory Intelligence Tool (IIT)

This FastAPI application handles approve/reject actions for pending reorder decisions.
It manages pending actions via SQLite database with JSON fallback and integrates
with the supplier connector and notification systems.

Usage:
    uvicorn src.webhook.app:app --host 0.0.0.0 --port 8080 --reload
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
import uvicorn

# Import our modules
from src.connectors.supplier_connector import SupplierConnector
from src.connectors.composio_notion_connector import ComposioNotionConnector
from src.connectors.sheets_connector import SheetsConnector
from src.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="IIT Approval Webhook",
    description="Handles approve/reject actions for inventory reorder decisions",
    version="1.0.0"
)

# Configuration
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "ed999b5c-aea7-44a8-b910-cae4b47cfb46")
DB_PATH = "demo/pending_actions.db"
JSON_FALLBACK_PATH = "demo/pending_actions.json"

class PendingActionsManager:
    """Manages pending approval actions with SQLite primary and JSON fallback"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.json_path = JSON_FALLBACK_PATH
        self.use_sqlite = self._init_sqlite()
        
        # Ensure demo directory exists
        os.makedirs("demo", exist_ok=True)
        
        if not self.use_sqlite:
            logger.warning("SQLite unavailable, using JSON fallback")
            self._init_json_fallback()
    
    def _init_sqlite(self) -> bool:
        """Initialize SQLite database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_actions (
                    token TEXT PRIMARY KEY,
                    sku TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    vendor TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    total_cost REAL NOT NULL,
                    rationale TEXT,
                    notion_page_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    status TEXT DEFAULT 'pending'
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("SQLite database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SQLite: {e}")
            return False
    
    def _init_json_fallback(self):
        """Initialize JSON fallback file"""
        if not os.path.exists(self.json_path):
            with open(self.json_path, 'w') as f:
                json.dump({}, f)
    
    def store_pending_action(self, token: str, action_data: Dict[str, Any]) -> bool:
        """Store a pending action"""
        try:
            # Add expiration (24 hours from now)
            expires_at = datetime.now() + timedelta(hours=24)
            
            if self.use_sqlite:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO pending_actions 
                    (token, sku, action_type, vendor, quantity, total_cost, 
                     rationale, notion_page_id, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    token,
                    action_data['sku'],
                    action_data['action_type'],
                    action_data['vendor'],
                    action_data['quantity'],
                    action_data['total_cost'],
                    action_data.get('rationale', ''),
                    action_data.get('notion_page_id', ''),
                    expires_at.isoformat()
                ))
                
                conn.commit()
                conn.close()
                
            else:
                # JSON fallback
                with open(self.json_path, 'r') as f:
                    data = json.load(f)
                
                data[token] = {
                    **action_data,
                    'expires_at': expires_at.isoformat(),
                    'status': 'pending'
                }
                
                with open(self.json_path, 'w') as f:
                    json.dump(data, f, indent=2)
            
            logger.info(f"Stored pending action for token: {token}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store pending action: {e}")
            return False
    
    def get_pending_action(self, token: str) -> Optional[Dict[str, Any]]:
        """Retrieve a pending action by token"""
        try:
            if self.use_sqlite:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM pending_actions 
                    WHERE token = ? AND status = 'pending' AND expires_at > ?
                """, (token, datetime.now().isoformat()))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                
            else:
                # JSON fallback
                with open(self.json_path, 'r') as f:
                    data = json.load(f)
                
                action = data.get(token)
                if action and action.get('status') == 'pending':
                    expires_at = datetime.fromisoformat(action['expires_at'])
                    if expires_at > datetime.now():
                        return action
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get pending action: {e}")
            return None
    
    def update_action_status(self, token: str, status: str) -> bool:
        """Update action status"""
        try:
            if self.use_sqlite:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE pending_actions 
                    SET status = ? 
                    WHERE token = ?
                """, (status, token))
                
                conn.commit()
                conn.close()
                
            else:
                # JSON fallback
                with open(self.json_path, 'r') as f:
                    data = json.load(f)
                
                if token in data:
                    data[token]['status'] = status
                    
                    with open(self.json_path, 'w') as f:
                        json.dump(data, f, indent=2)
            
            logger.info(f"Updated action status for token {token}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update action status: {e}")
            return False

# Initialize managers and connectors
from src.utils.config import Config

# Initialize configuration
config = Config()

# Initialize connectors
pending_manager = PendingActionsManager()
supplier_connector = SupplierConnector()
notion_connector = ComposioNotionConnector(demo_mode=True)
sheets_connector = SheetsConnector(config)

def generate_success_html(action: str, sku: str, details: str = "") -> str:
    """Generate success HTML response"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Action {action.title()}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .success {{ color: #28a745; }}
            .info {{ color: #17a2b8; }}
            h1 {{ color: #333; }}
            .details {{ background: #f8f9fa; padding: 15px; border-radius: 4px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="success">✅ Action {action.title()}</h1>
            <p>The reorder request for <strong>{sku}</strong> has been successfully <strong>{action}d</strong>.</p>
            {f'<div class="details"><strong>Details:</strong><br>{details}</div>' if details else ''}
            <p class="info">You can close this window. The inventory system has been updated accordingly.</p>
        </div>
    </body>
    </html>
    """

def generate_error_html(error_msg: str) -> str:
    """Generate error HTML response"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Error</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .error {{ color: #dc3545; }}
            h1 {{ color: #333; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="error">❌ Error</h1>
            <p>{error_msg}</p>
            <p>Please contact the system administrator if this error persists.</p>
        </div>
    </body>
    </html>
    """

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "IIT Approval Webhook"}

@app.get("/webhook/approve", response_class=HTMLResponse)
async def approve_action(
    token: str = Query(..., description="Approval token"),
    secret: str = Query(..., description="Webhook secret for security")
):
    """Handle approval of pending reorder action"""
    
    # Verify webhook secret
    if secret != WEBHOOK_SECRET:
        logger.warning(f"Invalid webhook secret for approve: {secret}")
        raise HTTPException(status_code=403, detail="Invalid webhook secret")
    
    # Get pending action
    action = pending_manager.get_pending_action(token)
    if not action:
        logger.warning(f"No pending action found for token: {token}")
        return HTMLResponse(
            generate_error_html("Invalid or expired approval token. The action may have already been processed or expired."),
            status_code=404
        )
    
    try:
        sku = action['sku']
        vendor = action['vendor']
        quantity = action['quantity']
        total_cost = action['total_cost']
        notion_page_id = action.get('notion_page_id')
        
        logger.info(f"Processing approval for SKU: {sku}, Vendor: {vendor}, Quantity: {quantity}")
        
        # 1. Place supplier order
        order_result = supplier_connector.place_order(
            vendor_id=vendor,
            sku=sku,
            qty=quantity
        )
        
        order_id = order_result.get('order_id', 'N/A')
        delivery_date = order_result.get('delivery_date', 'TBD')
        
        # 2. Update Notion page status
        if notion_page_id:
            try:
                notion_connector.update_page_properties(
                    page_id=notion_page_id,
                    properties={
                        "Status": {"select": {"name": "Ordered"}},
                        "Order ID": {"rich_text": [{"text": {"content": order_id}}]},
                        "Approved At": {"date": {"start": datetime.now().isoformat()}},
                        "Delivery Date": {"rich_text": [{"text": {"content": str(delivery_date)}}]}
                    }
                )
                logger.info(f"Updated Notion page {notion_page_id} with order details")
            except Exception as e:
                logger.error(f"Failed to update Notion page: {e}")
        
        # 3. Update Google Sheets
        try:
            sheets_connector.update_inventory_status(
                sku=sku,
                status="Ordered",
                order_id=order_id,
                order_date=datetime.now().strftime("%Y-%m-%d"),
                vendor=vendor,
                quantity=quantity,
                total_cost=total_cost
            )
            logger.info(f"Updated Google Sheets for SKU: {sku}")
        except Exception as e:
            logger.error(f"Failed to update Google Sheets: {e}")
        
        # 4. Mark action as completed
        pending_manager.update_action_status(token, "approved")
        
        # 5. Log the approval action
        logger.info(f"APPROVED: SKU={sku}, Vendor={vendor}, Quantity={quantity}, OrderID={order_id}, Cost=${total_cost}")
        
        # Generate success response
        details = f"""
        Order ID: {order_id}<br>
        Vendor: {vendor}<br>
        Quantity: {quantity}<br>
        Total Cost: ${total_cost:.2f}<br>
        Expected Delivery: {delivery_date}
        """
        
        return HTMLResponse(generate_success_html("approve", sku, details))
        
    except Exception as e:
        logger.error(f"Error processing approval: {e}")
        return HTMLResponse(
            generate_error_html(f"Failed to process approval: {str(e)}"),
            status_code=500
        )

@app.get("/webhook/reject", response_class=HTMLResponse)
async def reject_action(
    token: str = Query(..., description="Rejection token"),
    secret: str = Query(..., description="Webhook secret for security")
):
    """Handle rejection of pending reorder action"""
    
    # Verify webhook secret
    if secret != WEBHOOK_SECRET:
        logger.warning(f"Invalid webhook secret for reject: {secret}")
        raise HTTPException(status_code=403, detail="Invalid webhook secret")
    
    # Get pending action
    action = pending_manager.get_pending_action(token)
    if not action:
        logger.warning(f"No pending action found for token: {token}")
        return HTMLResponse(
            generate_error_html("Invalid or expired rejection token. The action may have already been processed or expired."),
            status_code=404
        )
    
    try:
        sku = action['sku']
        vendor = action['vendor']
        quantity = action['quantity']
        total_cost = action['total_cost']
        notion_page_id = action.get('notion_page_id')
        
        logger.info(f"Processing rejection for SKU: {sku}, Vendor: {vendor}, Quantity: {quantity}")
        
        # 1. Update Notion page status
        if notion_page_id:
            try:
                notion_connector.update_page_properties(
                    page_id=notion_page_id,
                    properties={
                        "Status": {"select": {"name": "Rejected"}},
                        "Rejected At": {"date": {"start": datetime.now().isoformat()}},
                        "Rejection Reason": {"rich_text": [{"text": {"content": "Manual rejection via webhook"}}]}
                    }
                )
                logger.info(f"Updated Notion page {notion_page_id} with rejection")
            except Exception as e:
                logger.error(f"Failed to update Notion page: {e}")
        
        # 2. Update Google Sheets
        try:
            sheets_connector.update_inventory_status(
                sku=sku,
                status="Rejected",
                order_id="",
                order_date="",
                vendor=vendor,
                quantity=0,
                total_cost=0
            )
            logger.info(f"Updated Google Sheets for rejected SKU: {sku}")
        except Exception as e:
            logger.error(f"Failed to update Google Sheets: {e}")
        
        # 3. Mark action as completed
        pending_manager.update_action_status(token, "rejected")
        
        # 4. Send recompute task to agent (for demo, write to logs)
        recompute_msg = {
            "action": "recompute",
            "sku": sku,
            "reason": "manual_rejection",
            "timestamp": datetime.now().isoformat(),
            "original_vendor": vendor,
            "original_quantity": quantity
        }
        
        # Write recompute task to demo file for agent to pick up
        recompute_file = "demo/recompute_tasks.json"
        try:
            if os.path.exists(recompute_file):
                with open(recompute_file, 'r') as f:
                    tasks = json.load(f)
            else:
                tasks = []
            
            tasks.append(recompute_msg)
            
            with open(recompute_file, 'w') as f:
                json.dump(tasks, f, indent=2)
            
            logger.info(f"Added recompute task for SKU: {sku}")
        except Exception as e:
            logger.error(f"Failed to write recompute task: {e}")
        
        # 5. Log the rejection action
        logger.info(f"REJECTED: SKU={sku}, Vendor={vendor}, Quantity={quantity}, Cost=${total_cost}")
        
        # Generate success response
        details = f"""
        Vendor: {vendor}<br>
        Quantity: {quantity}<br>
        Total Cost: ${total_cost:.2f}<br>
        A recompute task has been queued for alternative recommendations.
        """
        
        return HTMLResponse(generate_success_html("reject", sku, details))
        
    except Exception as e:
        logger.error(f"Error processing rejection: {e}")
        return HTMLResponse(
            generate_error_html(f"Failed to process rejection: {str(e)}"),
            status_code=500
        )

@app.get("/webhook/status/{token}")
async def get_action_status(token: str):
    """Get status of a pending action (for debugging)"""
    action = pending_manager.get_pending_action(token)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found or expired")
    
    return {
        "token": token,
        "sku": action['sku'],
        "status": action.get('status', 'pending'),
        "expires_at": action['expires_at']
    }

# Utility function to store pending action (called by agent_main.py)
def store_pending_approval(token: str, action_data: Dict[str, Any]) -> bool:
    """
    Utility function for agent_main.py to store pending actions
    
    Args:
        token: Unique token for the action
        action_data: Dictionary containing action details
    
    Returns:
        bool: Success status
    """
    return pending_manager.store_pending_action(token, action_data)

@app.get("/webhook/approve-batch", response_class=HTMLResponse)
async def approve_batch_action(
    token: str = Query(..., description="Batch approval token"),
    secret: str = Query(..., description="Webhook secret for security")
):
    """Handle batch approval of multiple reorder requests"""
    try:
        # Verify webhook secret
        if secret != WEBHOOK_SECRET:
            logger.warning(f"Invalid webhook secret for batch approval: {secret}")
            return generate_error_html("Invalid webhook secret")
        
        # Get pending batch action
        action = pending_actions.get_pending_action(token)
        if not action:
            logger.warning(f"Batch approval token not found or expired: {token}")
            return generate_error_html("Batch approval token not found or expired")
        
        if action.get('action_type') != 'batch_reorder':
            logger.warning(f"Invalid action type for batch approval: {action.get('action_type')}")
            return generate_error_html("Invalid action type for batch approval")
        
        logger.info(f"Processing batch approval for {len(action.get('items', []))} items")
        
        # Initialize connectors
        supplier_connector = SupplierConnector()
        notion_connector = ComposioNotionConnector()
        sheets_connector = SheetsConnector()
        
        approved_items = []
        failed_items = []
        
        # Process each item in the batch
        for item in action.get('items', []):
            sku = item['sku']
            try:
                # Place order with supplier
                order_result = supplier_connector.place_order(
                    sku=sku,
                    quantity=item['quantity'],
                    vendor=item['vendor']
                )
                
                if order_result.get('success'):
                    order_id = order_result.get('order_id', f"BATCH-{token[:8]}-{sku}")
                    
                    # Update Notion page status
                    if item.get('notion_page_id'):
                        notion_connector.update_reorder_status(
                            item['notion_page_id'], 
                            "ordered", 
                            order_id
                        )
                    
                    # Update Google Sheets status
                    sheets_connector.update_inventory_status(sku, "ordered", order_id)
                    
                    approved_items.append({
                        'sku': sku,
                        'order_id': order_id,
                        'quantity': item['quantity'],
                        'vendor': item['vendor']
                    })
                    
                    logger.info(f"Batch item approved and ordered: {sku} -> {order_id}")
                    
                else:
                    failed_items.append({
                        'sku': sku,
                        'error': order_result.get('error', 'Unknown error')
                    })
                    logger.error(f"Failed to place order for batch item {sku}: {order_result.get('error')}")
                    
            except Exception as e:
                failed_items.append({
                    'sku': sku,
                    'error': str(e)
                })
                logger.error(f"Exception processing batch item {sku}: {e}")
        
        # Update action status
        pending_actions.update_action_status(token, "approved")
        
        # Generate success response
        success_count = len(approved_items)
        failure_count = len(failed_items)
        total_cost = sum(item['total_cost'] for item in action.get('items', []))
        
        html_response = f"""
        <html>
        <head>
            <title>Batch Approval Processed</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f8f9fa; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .success {{ color: #28a745; }}
                .error {{ color: #dc3545; }}
                .summary {{ background-color: #e9ecef; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .item {{ margin: 10px 0; padding: 10px; border-left: 4px solid #007bff; background-color: #f8f9fa; }}
                .failed-item {{ border-left-color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="success">✅ Batch Approval Processed</h1>
                
                <div class="summary">
                    <h3>📊 Batch Summary</h3>
                    <p><strong>Total Items:</strong> {success_count + failure_count}</p>
                    <p><strong>Successfully Approved:</strong> <span class="success">{success_count}</span></p>
                    <p><strong>Failed:</strong> <span class="error">{failure_count}</span></p>
                    <p><strong>Total Cost:</strong> ${total_cost:.2f}</p>
                    <p><strong>Processed:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
        """
        
        if approved_items:
            html_response += """
                <h3 class="success">✅ Successfully Approved Items</h3>
            """
            for item in approved_items:
                html_response += f"""
                <div class="item">
                    <strong>SKU:</strong> {item['sku']} | 
                    <strong>Order ID:</strong> {item['order_id']} | 
                    <strong>Qty:</strong> {item['quantity']} | 
                    <strong>Vendor:</strong> {item['vendor']}
                </div>
                """
        
        if failed_items:
            html_response += """
                <h3 class="error">❌ Failed Items</h3>
            """
            for item in failed_items:
                html_response += f"""
                <div class="item failed-item">
                    <strong>SKU:</strong> {item['sku']} | 
                    <strong>Error:</strong> {item['error']}
                </div>
                """
        
        html_response += """
                <p><em>All approved orders have been placed with suppliers and inventory systems have been updated.</em></p>
            </div>
        </body>
        </html>
        """
        
        return html_response
        
    except Exception as e:
        logger.error(f"Error processing batch approval: {e}")
        return generate_error_html(f"Error processing batch approval: {str(e)}")

@app.get("/webhook/reject-batch", response_class=HTMLResponse)
async def reject_batch_action(
    token: str = Query(..., description="Batch rejection token"),
    secret: str = Query(..., description="Webhook secret for security")
):
    """Handle batch rejection of multiple reorder requests"""
    try:
        # Verify webhook secret
        if secret != WEBHOOK_SECRET:
            logger.warning(f"Invalid webhook secret for batch rejection: {secret}")
            return generate_error_html("Invalid webhook secret")
        
        # Get pending batch action
        action = pending_actions.get_pending_action(token)
        if not action:
            logger.warning(f"Batch rejection token not found or expired: {token}")
            return generate_error_html("Batch rejection token not found or expired")
        
        if action.get('action_type') != 'batch_reorder':
            logger.warning(f"Invalid action type for batch rejection: {action.get('action_type')}")
            return generate_error_html("Invalid action type for batch rejection")
        
        logger.info(f"Processing batch rejection for {len(action.get('items', []))} items")
        
        # Initialize connectors
        notion_connector = ComposioNotionConnector()
        sheets_connector = SheetsConnector()
        
        rejected_items = []
        
        # Process each item in the batch
        for item in action.get('items', []):
            sku = item['sku']
            try:
                # Update Notion page status
                if item.get('notion_page_id'):
                    notion_connector.update_reorder_status(
                        item['notion_page_id'], 
                        "rejected", 
                        ""
                    )
                
                # Update Google Sheets status
                sheets_connector.update_inventory_status(sku, "rejected", "")
                
                rejected_items.append({
                    'sku': sku,
                    'quantity': item['quantity'],
                    'vendor': item['vendor'],
                    'cost': item['total_cost']
                })
                
                logger.info(f"Batch item rejected: {sku}")
                
            except Exception as e:
                logger.error(f"Exception processing batch rejection for {sku}: {e}")
        
        # Update action status
        pending_actions.update_action_status(token, "rejected")
        
        # Generate response
        total_cost = sum(item['total_cost'] for item in action.get('items', []))
        
        html_response = f"""
        <html>
        <head>
            <title>Batch Rejection Processed</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f8f9fa; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .rejected {{ color: #dc3545; }}
                .summary {{ background-color: #f8d7da; padding: 20px; border-radius: 5px; margin: 20px 0; border: 1px solid #f5c6cb; }}
                .item {{ margin: 10px 0; padding: 10px; border-left: 4px solid #dc3545; background-color: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="rejected">❌ Batch Rejection Processed</h1>
                
                <div class="summary">
                    <h3>📊 Batch Summary</h3>
                    <p><strong>Total Items Rejected:</strong> {len(rejected_items)}</p>
                    <p><strong>Total Cost Saved:</strong> ${total_cost:.2f}</p>
                    <p><strong>Processed:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <h3 class="rejected">❌ Rejected Items</h3>
        """
        
        for item in rejected_items:
            html_response += f"""
            <div class="item">
                <strong>SKU:</strong> {item['sku']} | 
                <strong>Qty:</strong> {item['quantity']} | 
                <strong>Vendor:</strong> {item['vendor']} | 
                <strong>Cost:</strong> ${item['cost']:.2f}
            </div>
            """
        
        html_response += """
                <p><em>All rejected items have been marked in the inventory systems. No orders were placed.</em></p>
            </div>
        </body>
        </html>
        """
        
        return html_response
        
    except Exception as e:
        logger.error(f"Error processing batch rejection: {e}")
        return generate_error_html(f"Error processing batch rejection: {str(e)}")

if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        "src.webhook.app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )