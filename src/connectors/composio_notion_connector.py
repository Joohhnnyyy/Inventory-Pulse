"""
Composio-based Notion Connector for Notion integration

This module provides Notion functionality using Composio's Notion integration
instead of direct REST API calls. It supports both production and demo modes.
"""

import os
import uuid
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from composio import Composio
from composio.client.enums import Action

class ComposioNotionConnector:
    """
    Notion connector that uses Composio's Notion integration to manage pages and databases.
    Supports both production mode (actual Notion operations) and demo mode (file output).
    """
    
    def __init__(self, demo_mode=False, notion_db_id: Optional[str] = None):
        """
        Initialize the Composio Notion Connector
        
        Args:
            demo_mode (bool): If True, runs in demo mode without actual Notion operations
                             Default is False for production use
            notion_db_id (str): Notion database ID (or from NOTION_DB_ID env var)
        """
        self.demo_mode = demo_mode
        self.notion_db_id = notion_db_id or os.getenv('NOTION_DB_ID')
        self.notion_connected_account = None
        
        if not self.notion_db_id:
            raise ValueError("NOTION_DB_ID is required (set in environment or pass as parameter)")
        
        if not demo_mode:
            # Initialize Composio client
            self.composio_client = Composio()
            
            # Check for Notion integration and get connected account
            try:
                # First try connected accounts (these are the actual authenticated accounts)
                connected_accounts = self.composio_client.connected_accounts.get()
                for account in connected_accounts:
                    if account.appName.lower() == 'notion' and account.status == 'ACTIVE':
                        self.notion_connected_account = account.id
                        print(f"✅ Found active Notion connected account: {account.id}")
                        break
                            
                if not self.notion_connected_account:
                    raise ValueError("No active Notion connected account found")
                
                print(f"✅ Notion integration available via Composio")
                
            except Exception as e:
                print(f"❌ Error initializing Composio Notion integration: {str(e)}")
                raise
        else:
            print("📝 Running in demo mode - Notion operations will not be executed")

    def create_reorder_page(self, sku: str, qty: int, vendor_name: str, total_cost: float, 
                           eoq: int, forecast_text: str, evidence_list: List[str]) -> str:
        """
        Update an existing reorder page (does not create new pages)
        
        Args:
            sku: Product SKU
            qty: Quantity to reorder
            vendor_name: Supplier name
            total_cost: Total cost of the order
            eoq: Economic Order Quantity
            forecast_text: Forecast explanation
            evidence_list: List of evidence supporting the reorder decision
            
        Returns:
            str: URL of the updated page
        """
        if self.demo_mode:
            return self._create_demo_page(sku, qty, vendor_name, total_cost, eoq, forecast_text, evidence_list)
        
        try:
            # This method now only updates existing pages, does not create new ones
            # You need to provide an existing page_id to update
            raise NotImplementedError(
                "This method now only updates existing pages. "
                "Use update_reorder_status() with a valid page_id instead."
            )
            
        except Exception as e:
            print(f"❌ Error: This method no longer creates new pages: {str(e)}")
            raise

    def update_existing_page(self, page_id: str, sku: str, qty: int, vendor_name: str, 
                           total_cost: float, eoq: int, forecast_text: str, 
                           evidence_list: List[str]) -> str:
        """
        Update an existing Notion page with reorder information
        
        Args:
            page_id: Existing Notion page ID to update
            sku: Product SKU
            qty: Quantity to reorder
            vendor_name: Supplier name
            total_cost: Total cost of the order
            eoq: Economic Order Quantity
            forecast_text: Forecast explanation
            evidence_list: List of evidence supporting the reorder decision
            
        Returns:
            str: URL of the updated page
        """
        if self.demo_mode:
            return self._update_demo_page(page_id, "Updated", f"Updated with SKU {sku}")
        
        try:
            # Format evidence as a single text block
            evidence_text = "\n".join([f"• {evidence}" for evidence in evidence_list])
            
            # Prepare update properties for the existing page
            properties = {
                "SKU": {
                    "title": [{"text": {"content": sku}}]
                },
                "Quantity": {
                    "number": qty
                },
                "Vendor": {
                    "rich_text": [{"text": {"content": vendor_name}}]
                },
                "Total Cost": {
                    "number": total_cost
                },
                "EOQ": {
                    "number": eoq
                },
                "Status": {
                    "select": {"name": "Pending Approval"}
                },
                "Updated Date": {
                    "date": {"start": datetime.now().isoformat()}
                },
                "Forecast": {
                    "rich_text": [{"text": {"content": forecast_text}}]
                },
                "Evidence": {
                    "rich_text": [{"text": {"content": evidence_text}}]
                }
            }
            
            # Use Composio actions API to update the existing page
            result = self.composio_client.actions.execute(
                action=Action('NOTION_UPDATE_PAGE'),
                params={
                    "page_id": page_id,
                    "properties": properties
                },
                entity_id="default",
                connected_account=self.notion_connected_account
            )
            
            page_url = result.get('url', f"notion://page/{page_id}")
            print(f"✅ Updated Notion page for SKU {sku}: {page_url}")
            return page_url
            
        except Exception as e:
            print(f"❌ Error updating Notion page for SKU {sku}: {str(e)}")
            raise

    def update_reorder_status(self, page_id: str, status: str, order_confirm: Optional[str] = None) -> bool:
        """
        Update the status of a reorder page
        
        Args:
            page_id: Notion page ID to update
            status: New status (e.g., "Approved", "Rejected", "Ordered", "Delivered")
            order_confirm: Optional order confirmation details
            
        Returns:
            bool: True if update was successful
        """
        if self.demo_mode:
            return self._update_demo_page(page_id, status, order_confirm)
        
        try:
            # Prepare update properties
            properties = {
                "Status": {
                    "select": {"name": status}
                }
            }
            
            # Add order confirmation if provided
            if order_confirm:
                properties["Order Confirmation"] = {
                    "rich_text": [{"text": {"content": order_confirm}}]
                }
                properties["Updated Date"] = {
                    "date": {"start": datetime.now().isoformat()}
                }
            
            # Use Composio actions API to update the page
            result = self.composio_client.actions.execute(
                action=Action('NOTION_UPDATE_PAGE'),
                params={
                    "page_id": page_id,
                    "properties": properties
                },
                entity_id="default",
                connected_account=self.notion_connected_account
            )
            
            print(f"✅ Updated Notion page {page_id} status to: {status}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating Notion page {page_id}: {str(e)}")
            raise

    def _create_demo_page(self, sku: str, qty: int, vendor_name: str, total_cost: float, 
                         eoq: int, forecast_text: str, evidence_list: List[str]) -> str:
        """
        Create a demo page (save to file instead of creating in Notion)
        
        Returns:
            str: Demo page URL
        """
        page_id = f"demo_page_{int(datetime.now().timestamp())}"
        
        # Create demo directory if it doesn't exist
        demo_dir = Path("demo/notion_pages")
        demo_dir.mkdir(parents=True, exist_ok=True)
        
        # Create demo page data
        page_data = {
            "page_id": page_id,
            "database_id": self.notion_db_id,
            "sku": sku,
            "quantity": qty,
            "vendor": vendor_name,
            "total_cost": total_cost,
            "eoq": eoq,
            "status": "Pending Approval",
            "created_date": datetime.now().isoformat(),
            "forecast": forecast_text,
            "evidence": evidence_list,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save to demo file
        demo_file = demo_dir / f"{page_id}.json"
        import json
        with open(demo_file, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, indent=2, ensure_ascii=False)
        
        demo_url = f"demo://notion/page/{page_id}"
        print(f"📝 Demo Notion page saved to: {demo_file}")
        return demo_url

    def _update_demo_page(self, page_id: str, status: str, order_confirm: Optional[str] = None) -> bool:
        """
        Update a demo page (update file instead of updating in Notion)
        
        Returns:
            bool: True if update was successful
        """
        demo_dir = Path("demo/notion_pages")
        demo_file = demo_dir / f"{page_id}.json"
        
        if not demo_file.exists():
            print(f"❌ Demo page file not found: {demo_file}")
            return False
        
        try:
            # Load existing data
            import json
            with open(demo_file, 'r', encoding='utf-8') as f:
                page_data = json.load(f)
            
            # Update the data
            page_data["status"] = status
            page_data["updated_date"] = datetime.now().isoformat()
            
            if order_confirm:
                page_data["order_confirmation"] = order_confirm
            
            # Save updated data
            with open(demo_file, 'w', encoding='utf-8') as f:
                json.dump(page_data, f, indent=2, ensure_ascii=False)
            
            print(f"📝 Demo page updated: {demo_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating demo page: {str(e)}")
            return False


# Test the connector if run directly
if __name__ == "__main__":
    # Test in demo mode first
    print("🧪 Testing Composio Notion Connector...")
    
    connector = ComposioNotionConnector(demo_mode=True)
    
    # Test creating a page
    page_url = connector.create_reorder_page(
        sku="TEST-001",
        qty=50,
        vendor_name="Test Vendor Inc.",
        total_cost=500.00,
        eoq=75,
        forecast_text="Test forecast for demo purposes",
        evidence_list=[
            "Test evidence 1: Stock below threshold",
            "Test evidence 2: Seasonal demand increase",
            "Test evidence 3: Lead time considerations"
        ]
    )
    
    print(f"✅ Demo page created: {page_url}")
    
    # Extract page ID for status update test
    page_id = page_url.split('/')[-1]
    
    # Test updating the page
    success = connector.update_reorder_status(
        page_id=page_id,
        status="Approved",
        order_confirm="Test order confirmation - PO-DEMO-001"
    )
    
    print(f"✅ Demo page update: {'Success' if success else 'Failed'}")