#!/usr/bin/env python3
"""
Script to create sample data in your Notion inventory database.
Run this after setting up your database and integration to test the connection.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError

# Load environment variables
load_dotenv()

# Sample inventory data
SAMPLE_DATA = [
    {
        "sku": "WIDGET-001",
        "quantity": 100,
        "vendor": "Acme Supplies Inc.",
        "total_cost": 1250.00,
        "eoq": 150,
        "status": "Pending",
        "priority": "High",
        "forecast": "Based on Q4 sales trends, expecting 25% increase in demand for widgets",
        "evidence": "• Current stock: 15 units (below minimum threshold of 50)\n• Average monthly consumption: 45 units\n• Lead time: 14 days\n• Seasonal demand spike expected in December",
        "supplier_contact": "orders@acmesupplies.com"
    },
    {
        "sku": "GADGET-205",
        "quantity": 75,
        "vendor": "TechParts Ltd.",
        "total_cost": 890.50,
        "eoq": 100,
        "status": "Approved",
        "priority": "Medium",
        "forecast": "Steady demand with slight uptick in Q1 due to new product launches",
        "evidence": "• Current stock: 25 units\n• Monthly consumption: 30 units\n• Lead time: 10 days\n• New product integration requires additional inventory",
        "supplier_contact": "supply@techparts.com"
    },
    {
        "sku": "COMPONENT-X42",
        "quantity": 200,
        "vendor": "Industrial Components Co.",
        "total_cost": 2100.00,
        "eoq": 250,
        "status": "Ordered",
        "priority": "Critical",
        "forecast": "Critical component with high demand volatility",
        "evidence": "• Current stock: 5 units (CRITICAL LOW)\n• Monthly consumption: 60 units\n• Lead time: 21 days\n• Single supplier dependency",
        "supplier_contact": "orders@industrialcomp.com",
        "order_confirmation": "PO-2024-001 submitted on " + datetime.now().strftime("%Y-%m-%d")
    }
]

def create_sample_data():
    """Create sample inventory data in the Notion database."""
    
    print("🔧 Creating Sample Inventory Data...")
    print("=" * 50)
    
    # Check environment variables
    notion_token = os.getenv('NOTION_TOKEN')
    notion_db_id = os.getenv('NOTION_DB_ID')
    
    if not notion_token or notion_token == 'your_notion_integration_token_here':
        print("❌ NOTION_TOKEN is not properly configured.")
        return False
    
    if not notion_db_id or notion_db_id == 'your_notion_database_id_here':
        print("❌ NOTION_DB_ID is not properly configured.")
        return False
    
    try:
        # Initialize Notion client
        notion = Client(auth=notion_token)
        
        print(f"📊 Creating {len(SAMPLE_DATA)} sample records...")
        
        created_pages = []
        
        for i, item in enumerate(SAMPLE_DATA, 1):
            print(f"\n📝 Creating record {i}: {item['sku']}")
            
            # Prepare page properties
            properties = {
                "SKU": {
                    "title": [
                        {
                            "text": {
                                "content": item["sku"]
                            }
                        }
                    ]
                },
                "Quantity": {
                    "number": item["quantity"]
                },
                "Vendor": {
                    "rich_text": [
                        {
                            "text": {
                                "content": item["vendor"]
                            }
                        }
                    ]
                },
                "Total Cost": {
                    "number": item["total_cost"]
                },
                "EOQ": {
                    "number": item["eoq"]
                },
                "Status": {
                    "select": {
                        "name": item["status"]
                    }
                },
                "Priority": {
                    "select": {
                        "name": item["priority"]
                    }
                },
                "Forecast": {
                    "rich_text": [
                        {
                            "text": {
                                "content": item["forecast"]
                            }
                        }
                    ]
                },
                "Evidence": {
                    "rich_text": [
                        {
                            "text": {
                                "content": item["evidence"]
                            }
                        }
                    ]
                },
                "Supplier Contact": {
                    "email": item["supplier_contact"]
                }
            }
            
            # Add order confirmation if present
            if "order_confirmation" in item:
                properties["Order Confirmation"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": item["order_confirmation"]
                            }
                        }
                    ]
                }
            
            # Create the page
            page = notion.pages.create(
                parent={"database_id": notion_db_id},
                properties=properties
            )
            
            page_id = page["id"]
            page_url = page["url"]
            created_pages.append({
                "sku": item["sku"],
                "page_id": page_id,
                "url": page_url
            })
            
            print(f"   ✅ Created: {item['sku']} (Status: {item['status']}, Priority: {item['priority']})")
        
        print(f"\n🎉 Successfully created {len(created_pages)} sample records!")
        print("\n📋 Created Records:")
        for page in created_pages:
            print(f"   • {page['sku']}: {page['url']}")
        
        print(f"\n🔗 View your database: https://notion.so/{notion_db_id.replace('-', '')}")
        
        return True
        
    except APIResponseError as e:
        print(f"\n❌ Notion API Error: {e}")
        if e.status == 400:
            print("   This might mean some properties don't exist in your database.")
            print("   Make sure you've set up all required properties as described in the setup guide.")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def clear_sample_data():
    """Clear all sample data from the database (optional cleanup function)."""
    
    print("🧹 Clearing Sample Data...")
    print("=" * 30)
    
    notion_token = os.getenv('NOTION_TOKEN')
    notion_db_id = os.getenv('NOTION_DB_ID')
    
    if not notion_token or not notion_db_id:
        print("❌ Environment variables not configured.")
        return False
    
    try:
        notion = Client(auth=notion_token)
        
        # Query all pages
        query_result = notion.databases.query(database_id=notion_db_id)
        pages = query_result.get('results', [])
        
        print(f"Found {len(pages)} pages to delete...")
        
        for page in pages:
            page_id = page['id']
            sku = "Unknown"
            
            # Try to get SKU from title
            if 'properties' in page and 'SKU' in page['properties']:
                title_prop = page['properties']['SKU']
                if 'title' in title_prop and title_prop['title']:
                    sku = title_prop['title'][0]['text']['content']
            
            # Archive the page (Notion doesn't allow permanent deletion via API)
            notion.pages.update(page_id=page_id, archived=True)
            print(f"   🗑️ Archived: {sku}")
        
        print(f"\n✅ Archived {len(pages)} pages.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error clearing data: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        success = clear_sample_data()
    else:
        success = create_sample_data()
        
        if success:
            print("\n💡 Tips:")
            print("   • Check your Notion database to see the new records")
            print("   • Try different views (All Orders, Pending Orders, Status Board)")
            print("   • Test updating record statuses manually")
            print("   • Run 'python create_sample_data.py clear' to remove sample data")
    
    sys.exit(0 if success else 1)