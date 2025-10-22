"""
Notion Connector

Handles all interactions with Notion for reorder page creation and status updates.
Uses Notion REST API v1 to create and manage inventory replenishment records.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
import json

class NotionConnector:
    """
    Connector for Notion integration using REST API v1.
    
    Creates and manages reorder pages in a Notion database for inventory replenishment tracking.
    """
    
    def __init__(self, notion_token: Optional[str] = None, notion_db_id: Optional[str] = None):
        """
        Initialize the Notion connector.
        
        Args:
            notion_token: Notion integration token (or from NOTION_TOKEN env var)
            notion_db_id: Notion database ID (or from NOTION_DB_ID env var)
        """
        self.logger = logging.getLogger(__name__)
        
        # Get credentials from parameters or environment
        self.notion_token = notion_token or os.getenv('NOTION_TOKEN')
        self.notion_db_id = notion_db_id or os.getenv('NOTION_DB_ID')
        
        if not self.notion_token:
            raise ValueError("NOTION_TOKEN is required (set in environment or pass as parameter)")
        if not self.notion_db_id:
            raise ValueError("NOTION_DB_ID is required (set in environment or pass as parameter)")
        
        # Notion API configuration
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"  # Latest stable API version
        }
        
        self.logger.info("Notion connector initialized successfully")
    
    def create_reorder_page(self, sku: str, qty: int, vendor_name: str, total_cost: float, 
                           eoq: int, forecast_text: str, evidence_list: List[str]) -> str:
        """
        Create a new reorder page in Notion database.
        
        Args:
            sku: Stock Keeping Unit identifier
            qty: Quantity to order
            vendor_name: Name of the vendor/supplier
            total_cost: Total cost of the order
            eoq: Economic Order Quantity
            forecast_text: Demand forecast description
            evidence_list: List of evidence/reasons for the reorder
            
        Returns:
            str: Notion page URL or page ID
            
        Raises:
            Exception: If page creation fails
        """
        try:
            # Prepare evidence as rich text blocks
            evidence_blocks = []
            for evidence in evidence_list:
                evidence_blocks.append({
                    "text": {"content": f"• {evidence}"}
                })
            
            # Create page properties
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
                "Created Date": {
                    "date": {"start": datetime.now().isoformat()}
                },
                "Forecast": {
                    "rich_text": [{"text": {"content": forecast_text}}]
                },
                "Evidence": {
                    "rich_text": evidence_blocks
                }
            }
            
            # Create the page
            payload = {
                "parent": {"database_id": self.notion_db_id},
                "properties": properties
            }
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_msg = f"Failed to create Notion page: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                raise Exception(error_msg)
            
            page_data = response.json()
            page_id = page_data['id']
            page_url = page_data['url']
            
            self.logger.info(f"Created Notion reorder page for SKU {sku}: {page_url}")
            return page_url
            
        except Exception as e:
            self.logger.error(f"Error creating Notion reorder page for SKU {sku}: {str(e)}")
            raise
    
    def update_reorder_status(self, page_id: str, status: str, order_confirm: Optional[str] = None) -> bool:
        """
        Update the status of a reorder page.
        
        Args:
            page_id: Notion page ID to update
            status: New status (e.g., "Approved", "Rejected", "Ordered", "Delivered")
            order_confirm: Optional order confirmation details
            
        Returns:
            bool: True if update was successful
            
        Raises:
            Exception: If update fails
        """
        try:
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
            
            # Update the page
            payload = {"properties": properties}
            
            response = requests.patch(
                f"{self.base_url}/pages/{page_id}",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_msg = f"Failed to update Notion page: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                raise Exception(error_msg)
            
            self.logger.info(f"Updated Notion page {page_id} status to: {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating Notion page {page_id}: {str(e)}")
            raise


if __name__ == "__main__":
    """
    Example usage of the Notion connector.
    Creates a sample reorder page for demonstration.
    """
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize connector
        connector = NotionConnector()
        
        # Sample data for creating a reorder page
        sample_sku = "WIDGET-001"
        sample_qty = 100
        sample_vendor = "Acme Supplies Inc."
        sample_total_cost = 1250.00
        sample_eoq = 150
        sample_forecast = "Based on Q4 sales trends, expecting 25% increase in demand"
        sample_evidence = [
            "Current stock: 15 units (below minimum threshold of 50)",
            "Average monthly consumption: 45 units",
            "Lead time: 14 days",
            "Seasonal demand spike expected in December"
        ]
        
        print("Creating sample Notion reorder page...")
        page_url = connector.create_reorder_page(
            sku=sample_sku,
            qty=sample_qty,
            vendor_name=sample_vendor,
            total_cost=sample_total_cost,
            eoq=sample_eoq,
            forecast_text=sample_forecast,
            evidence_list=sample_evidence
        )
        
        print(f"✅ Successfully created reorder page: {page_url}")
        
        # Extract page ID from URL for status update demo
        page_id = page_url.split('/')[-1].split('-')[-1]
        
        print(f"\nUpdating page status to 'Approved'...")
        success = connector.update_reorder_status(
            page_id=page_id,
            status="Approved",
            order_confirm="PO-2024-001 submitted to vendor on " + datetime.now().strftime("%Y-%m-%d")
        )
        
        if success:
            print("✅ Successfully updated page status")
        else:
            print("❌ Failed to update page status")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nMake sure you have set the following environment variables:")
        print("- NOTION_TOKEN: Your Notion integration token")
        print("- NOTION_DB_ID: Your Notion database ID")