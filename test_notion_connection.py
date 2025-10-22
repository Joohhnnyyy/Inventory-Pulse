#!/usr/bin/env python3
"""
Test script to verify Notion API connection and database access.
"""

import os
import sys
from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError

# Load environment variables
load_dotenv()

def test_notion_connection():
    """Test the Notion API connection and database access."""
    
    print("🔍 Testing Notion API Connection...")
    print("=" * 50)
    
    # Check environment variables
    notion_token = os.getenv('NOTION_TOKEN')
    notion_db_id = os.getenv('NOTION_DB_ID')
    
    print(f"NOTION_TOKEN: {'✅ Set' if notion_token and notion_token != 'your_notion_integration_token_here' else '❌ Not set or placeholder'}")
    print(f"NOTION_DB_ID: {'✅ Set' if notion_db_id and notion_db_id != 'your_notion_database_id_here' else '❌ Not set or placeholder'}")
    
    if not notion_token or notion_token == 'your_notion_integration_token_here':
        print("\n❌ NOTION_TOKEN is not properly configured.")
        print("Please set your Notion integration token in the .env file.")
        return False
    
    if not notion_db_id or notion_db_id == 'your_notion_database_id_here':
        print("\n❌ NOTION_DB_ID is not properly configured.")
        print("Please set your Notion database ID in the .env file.")
        return False
    
    try:
        # Initialize Notion client
        print("\n🔗 Initializing Notion client...")
        notion = Client(auth=notion_token)
        
        # Test basic API access
        print("📋 Testing API access...")
        user = notion.users.me()
        print(f"✅ Connected as: {user.get('name', 'Unknown')} ({user.get('type', 'Unknown')})")
        
        # Test database access
        print(f"\n📊 Testing database access (ID: {notion_db_id})...")
        database = notion.databases.retrieve(database_id=notion_db_id)
        
        print(f"✅ Database found: {database.get('title', [{}])[0].get('plain_text', 'Untitled')}")
        print(f"   Created: {database.get('created_time', 'Unknown')}")
        print(f"   Last edited: {database.get('last_edited_time', 'Unknown')}")
        
        # Show database properties
        properties = database.get('properties', {})
        print(f"\n📝 Database Properties ({len(properties)} found):")
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get('type', 'unknown')
            print(f"   • {prop_name}: {prop_type}")
        
        # Test querying the database
        print(f"\n🔍 Testing database query...")
        query_result = notion.databases.query(
            database_id=notion_db_id,
            page_size=5  # Limit to 5 results for testing
        )
        
        pages = query_result.get('results', [])
        print(f"✅ Query successful: Found {len(pages)} pages (showing max 5)")
        
        if pages:
            print("\n📄 Sample pages:")
            for i, page in enumerate(pages[:3], 1):  # Show first 3 pages
                page_id = page.get('id', 'Unknown')
                created_time = page.get('created_time', 'Unknown')
                print(f"   {i}. Page ID: {page_id[:8]}... (Created: {created_time[:10]})")
        else:
            print("   (No pages found in database)")
        
        print("\n✅ Notion connection test completed successfully!")
        return True
        
    except APIResponseError as e:
        print(f"\n❌ Notion API Error: {e}")
        if e.status == 401:
            print("   This usually means the NOTION_TOKEN is invalid or expired.")
        elif e.status == 404:
            print("   This usually means the database ID is incorrect or the integration doesn't have access.")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_notion_connection()
    sys.exit(0 if success else 1)