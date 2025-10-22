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
from src.connectors.notion_connector import NotionConnector
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
pending_manager = PendingActionsManager()
supplier_connector = SupplierConnector()
notion_connector = NotionConnector()
sheets_connector = SheetsConnector()

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
            sku=sku,
            quantity=quantity,
            vendor=vendor
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

if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        "src.webhook.app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )