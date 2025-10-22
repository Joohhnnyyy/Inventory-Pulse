"""
Composio-based Notion Connector for Notion integration

This module provides Notion functionality using Composio's MCP (Model Context Protocol) server
instead of direct SDK calls. It supports both production and demo modes.
"""

import os
import uuid
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from src.connectors.mcp_client import SyncComposioMCPClient

class ComposioNotionConnector:
    """
    Notion connector that uses Composio's MCP server to manage pages and databases.
    Supports both production mode (actual Notion operations) and demo mode (file output).
    """
    
    def __init__(self, demo_mode=False, notion_db_id: Optional[str] = None, mcp_server_url: Optional[str] = None):
        """
        Initialize the Composio Notion Connector
        
        Args:
            demo_mode (bool): If True, runs in demo mode without actual Notion operations
                             Default is False for production use
            notion_db_id (str): Notion database ID (or from NOTION_DB_ID env var)
            mcp_server_url (str): Composio MCP server URL (or from COMPOSIO_MCP_URL env var)
        """
        self.demo_mode = demo_mode
        self.notion_db_id = notion_db_id or os.getenv('NOTION_DB_ID')
        self.mcp_server_url = mcp_server_url or os.getenv('COMPOSIO_MCP_URL')
        self.mcp_client = None
        
        if not self.notion_db_id:
            raise ValueError("NOTION_DB_ID is required (set in environment or pass as parameter)")
        
        if not demo_mode:
            if not self.mcp_server_url:
                raise ValueError("COMPOSIO_MCP_URL is required for production mode (set in environment or pass as parameter)")
            
            # Initialize MCP client
            try:
                self.mcp_client = SyncComposioMCPClient(self.mcp_server_url)
                self.mcp_client.connect()
                
                # Check if Notion tools are available
                available_tools = self.mcp_client.get_available_tools()
                notion_tools = [tool for tool in available_tools if 'notion' in tool.lower()]
                
                if not notion_tools:
                    raise ValueError("No Notion tools available in MCP server")
                
                print(f"✅ Connected to Composio MCP server with {len(notion_tools)} Notion tools")
                
            except Exception as e:
                print(f"❌ Error connecting to Composio MCP server: {str(e)}")
                raise
        else:
            print("📝 Running in demo mode - Notion operations will not be executed")

    def create_reorder_page(self, sku: str, qty: int, vendor_name: str, total_cost: float, 
                           eoq: int, forecast_text: str, evidence_list: List[str]) -> str:
        """
        Create a new Notion page with reorder information
        
        Args:
            sku: Product SKU
            qty: Quantity to reorder
            vendor_name: Supplier name
            total_cost: Total cost of the order
            eoq: Economic Order Quantity
            forecast_text: Forecast explanation
            evidence_list: List of evidence supporting the reorder decision
            
        Returns:
            str: URL of the created page
        """
        if self.demo_mode:
            return self._create_demo_page(sku, qty, vendor_name, total_cost, eoq, forecast_text, evidence_list)
        
        try:
            # Format evidence as a single text block
            evidence_text = "\n".join([f"• {evidence}" for evidence in evidence_list])
            
            # Use MCP client to call Notion insert row action
            response = self.mcp_client.execute_tool(
                tool_name="NOTION_INSERT_ROW_DATABASE",
                arguments={
                    "database_id": self.notion_db_id,
                    "properties": [
                        {
                            "name": "SKU (Product identifier)",
                            "type": "title",
                            "value": sku
                        },
                        {
                            "name": "Quantity(How many to order)",
                            "type": "number",
                            "value": str(qty)
                        },
                        {
                            "name": "Vendor (Text)",
                            "type": "rich_text",
                            "value": vendor_name
                        },
                        {
                            "name": "Total Cost (Currency)",
                            "type": "number",
                            "value": str(total_cost)
                        },
                        {
                            "name": "Status (Select)",
                            "type": "select",
                            "value": "Pending"
                        },
                        {
                            "name": "Priority (Select)",
                            "type": "select",
                            "value": "Medium"
                        },
                        {
                            "name": "Forecast (Text)",
                            "type": "rich_text",
                            "value": forecast_text
                        },
                        {
                            "name": "Evidence (Text)",
                            "type": "rich_text",
                            "value": evidence_text
                        },
                        {
                            "name": "Order Confirmation (Text)",
                            "type": "rich_text",
                            "value": ""
                        },
                        {
                            "name": "Supplier Contact (Email)",
                            "type": "email",
                            "value": "supplier@example.com"
                        }
                    ]
                }
            )
            
            # Check if the response is successful and extract the page URL
            if response:
                print(f"✅ Received response from MCP server for SKU {sku}")
                
                # Handle the actual MCP response structure
                if isinstance(response, dict):
                    # Check for content array structure (actual MCP response format)
                    if 'content' in response and isinstance(response['content'], list):
                        for item in response['content']:
                            if isinstance(item, dict) and 'text' in item:
                                try:
                                    import json
                                    parsed_response = json.loads(item['text'])
                                    
                                    # Check if the operation was successful
                                    if parsed_response.get('successfull', False) or parsed_response.get('successful', False):
                                        # Extract page ID from response_data
                                        if 'data' in parsed_response and 'response_data' in parsed_response['data']:
                                            response_data = parsed_response['data']['response_data']
                                            if 'id' in response_data:
                                                page_id = response_data['id']
                                                page_url = f"https://www.notion.so/{page_id.replace('-', '')}"
                                                print(f"✅ Successfully created page for SKU {sku}: {page_url}")
                                                return page_url
                                    
                                    # Check for error in parsed response
                                    if parsed_response.get('error'):
                                        raise Exception(f"MCP server error: {parsed_response['error']}")
                                        
                                except json.JSONDecodeError as e:
                                    print(f"⚠️ Failed to parse response text as JSON: {e}")
                                    continue
                    
                    # Fallback: Check for legacy response structure
                    elif 'data' in response and 'response_data' in response['data']:
                        response_data = response['data']['response_data']
                        if isinstance(response_data, dict) and 'id' in response_data:
                            page_id = response_data['id']
                            page_url = f"https://www.notion.so/{page_id.replace('-', '')}"
                            print(f"✅ Successfully created page for SKU {sku}: {page_url}")
                            return page_url
                        elif isinstance(response_data, str):
                            try:
                                import json
                                parsed_data = json.loads(response_data)
                                if 'id' in parsed_data:
                                    page_id = parsed_data['id']
                                    page_url = f"https://www.notion.so/{page_id.replace('-', '')}"
                                    print(f"✅ Successfully created page for SKU {sku}: {page_url}")
                                    return page_url
                            except json.JSONDecodeError:
                                pass
                    
                    # Check for error in response
                    if response.get('error'):
                        raise Exception(f"MCP server error: {response['error']}")
                
                # If we get here, the response format is unexpected but no error was detected
                print(f"⚠️ Unexpected response format but no error detected for SKU {sku}")
                return "https://www.notion.so/page-created-with-unknown-status"
            else:
                raise Exception("No response received from MCP server")
                
        except Exception as e:
            print(f"❌ Error creating Notion page for SKU {sku}: {str(e)}")
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
            
            # Prepare update properties for MCP client
            properties = [
                {
                    "name": "SKU (Product identifier)",
                    "type": "title",
                    "value": sku
                },
                {
                    "name": "Quantity(How many to order)",
                    "type": "number",
                    "value": str(qty)
                },
                {
                    "name": "Vendor (Text)",
                    "type": "rich_text",
                    "value": vendor_name
                },
                {
                    "name": "Total Cost (Currency)",
                    "type": "number",
                    "value": str(total_cost)
                },
                {
                    "name": "Status (Select)",
                    "type": "select",
                    "value": "Pending Approval"
                },
                {
                    "name": "Forecast (Text)",
                    "type": "rich_text",
                    "value": forecast_text
                },
                {
                    "name": "Evidence (Text)",
                    "type": "rich_text",
                    "value": evidence_text
                }
            ]
            
            # Use MCP client to update the existing page
            response = self.mcp_client.execute_tool(
                tool_name="NOTION_UPDATE_PAGE",
                arguments={
                    "page_id": page_id,
                    "properties": properties
                }
            )
            
            if response and response.get('success'):
                page_data = response.get('data', {})
                page_url = page_data.get('url', f"notion://page/{page_id}")
                print(f"✅ Updated Notion page for SKU {sku}: {page_url}")
                return page_url
            else:
                error_msg = response.get('error', 'Unknown error occurred')
                raise Exception(f"Failed to update page: {error_msg}")
            
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
            # Prepare update properties for MCP client - use Notion API format
            properties = {
                "Status (Select)": {
                    "select": {
                        "name": status
                    }
                }
            }
            
            # Add order confirmation if provided
            if order_confirm:
                properties["Order Confirmation (Text)"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": order_confirm
                            }
                        }
                    ]
                }
            
            # Use MCP client to update the page
            response = self.mcp_client.execute_tool(
                tool_name="NOTION_UPDATE_PAGE",
                arguments={
                    "page_id": page_id,
                    "properties": properties
                }
            )
            
            # Handle the actual MCP response structure for updates
            if response:
                print(f"✅ Received response from MCP server for page update {page_id}")
                
                if isinstance(response, dict):
                    # Check for content array structure (actual MCP response format)
                    if 'content' in response and isinstance(response['content'], list):
                        for item in response['content']:
                            if isinstance(item, dict) and 'text' in item:
                                try:
                                    import json
                                    parsed_response = json.loads(item['text'])
                                    
                                    # Check if the operation was successful
                                    if parsed_response.get('successfull', False) or parsed_response.get('successful', False):
                                        print(f"✅ Successfully updated page {page_id} status to: {status}")
                                        return True
                                    
                                    # Check for error in parsed response
                                    if parsed_response.get('error'):
                                        error_msg = parsed_response['error']
                                        print(f"❌ Failed to update Notion page {page_id}: {error_msg}")
                                        return False
                                        
                                except json.JSONDecodeError as e:
                                    print(f"⚠️ Failed to parse response text as JSON: {e}")
                                    continue
                    
                    # Fallback: Check for legacy response structure
                    elif response.get('success') or response.get('successfull', False):
                        print(f"✅ Successfully updated page {page_id} status to: {status}")
                        return True
                    elif response.get('error'):
                        error_msg = response['error']
                        print(f"❌ Failed to update Notion page {page_id}: {error_msg}")
                        return False
                
                # If we get here, assume success if no error was detected
                print(f"✅ Page update completed for {page_id} (response format unclear but no error)")
                return True
            else:
                print(f"❌ No response received from MCP server for page {page_id}")
                return False
            
        except Exception as e:
            print(f"❌ Error updating Notion page {page_id}: {str(e)}")
            return False

    def query_database(self, filter_properties: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """
        Query the Notion database to retrieve pages.
        
        Args:
            filter_properties: Optional filter criteria for the query
            limit: Maximum number of pages to retrieve (default: 100)
            
        Returns:
            List[Dict]: List of page objects from the database
        """
        if self.demo_mode:
            return self._query_demo_database(filter_properties, limit)
            
        try:
            # Prepare query parameters for MCP client
            query_params = {
                "database_id": self.notion_db_id,
                "page_size": min(limit, 100)  # Notion API limit is 100
            }
            
            # Add filter if provided
            if filter_properties:
                query_params["filter"] = filter_properties
            
            # Use MCP client to query the database
            response = self.mcp_client.execute_tool(
                tool_name="NOTION_QUERY_DATABASE",
                arguments=query_params
            )
            
            # Extract pages from the response
            if response and response.get('success'):
                data = response.get('data', {})
                # Try different possible response structures
                if 'results' in data:
                    return data['results']
                elif 'response_data' in data and 'results' in data['response_data']:
                    return data['response_data']['results']
                else:
                    print(f"Unexpected query response structure: {response}")
                    return []
            else:
                error_msg = response.get('error', 'Unknown error occurred')
                print(f"❌ Failed to query database: {error_msg}")
                return []
                
        except Exception as e:
            print(f"❌ Error querying Notion database: {str(e)}")
            return []

    def _query_demo_database(self, filter_properties: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """
        Query demo database (read from demo files)
        
        Returns:
            List[Dict]: List of demo page objects
        """
        demo_dir = Path("demo/notion_pages")
        if not demo_dir.exists():
            return []
            
        demo_pages = []
        for demo_file in demo_dir.glob("demo_page_*.json"):
            try:
                with open(demo_file, 'r') as f:
                    page_data = json.load(f)
                    # Convert demo format to Notion API format
                    notion_page = {
                        "id": page_data.get("page_id", ""),
                        "properties": {
                            "SKU (Product identifier)": {
                                "title": [{"text": {"content": page_data.get("sku", "")}}]
                            },
                            "Status (Select)": {
                                "select": {"name": page_data.get("status", "Pending Review")}
                            },
                            "Vendor (Text)": {
                                "rich_text": [{"text": {"content": page_data.get("vendor", "")}}]
                            },
                            "Quantity(How many to order)": {
                                "number": page_data.get("quantity", 0)
                            },
                            "Total Cost (Currency)": {
                                "number": page_data.get("total_cost", 0.0)
                            }
                        }
                    }
                    demo_pages.append(notion_page)
                    
                    if len(demo_pages) >= limit:
                        break
                        
            except Exception as e:
                print(f"Warning: Could not read demo file {demo_file}: {e}")
                continue
                
        return demo_pages

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