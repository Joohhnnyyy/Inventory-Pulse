#!/usr/bin/env python3
"""
Reset Composio Gmail Integration
This script will help reset and re-authenticate the Gmail account with Composio
"""

import os
from dotenv import load_dotenv
from composio import Composio, Action
import json

def main():
    print("🔄 COMPOSIO GMAIL RESET & RE-SETUP")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize Composio client
        composio_api_key = os.getenv('COMPOSIO_API_KEY')
        if not composio_api_key:
            print("❌ COMPOSIO_API_KEY not found in .env file!")
            return
            
        print(f"🔑 Using Composio API Key: {composio_api_key[:10]}...")
        composio_client = Composio(api_key=composio_api_key)
        
        print("\n📋 STEP 1: Checking current connected accounts...")
        
        # Get all connected accounts
        connected_accounts = composio_client.get_connected_accounts()
        
        print(f"📊 Found {len(connected_accounts)} connected accounts:")
        
        gmail_accounts = []
        for account in connected_accounts:
            print(f"   • Account ID: {account.id}")
            print(f"     App: {account.appName}")
            print(f"     Status: {account.status}")
            print(f"     Created: {account.createdAt}")
            
            if account.appName.lower() == 'gmail':
                gmail_accounts.append(account)
                print(f"     ✅ Gmail account found!")
            print()
        
        print(f"\n📧 Found {len(gmail_accounts)} Gmail accounts")
        
        if gmail_accounts:
            print("\n🗑️  STEP 2: Disconnecting existing Gmail accounts...")
            for gmail_account in gmail_accounts:
                try:
                    print(f"   Disconnecting account: {gmail_account.id}")
                    # Note: Composio doesn't have a direct disconnect method in the Python SDK
                    # We'll need to use the web interface or API directly
                    print(f"   ⚠️  Account {gmail_account.id} needs manual disconnection")
                    print(f"   🌐 Go to: https://app.composio.dev/apps/gmail")
                    print(f"   📋 Disconnect account ID: {gmail_account.id}")
                except Exception as e:
                    print(f"   ❌ Error disconnecting {gmail_account.id}: {str(e)}")
        
        print("\n🔗 STEP 3: Setting up new Gmail connection...")
        print("   📋 Follow these steps:")
        print("   1. Go to: https://app.composio.dev/apps/gmail")
        print("   2. Click 'Connect Account'")
        print("   3. Authenticate with anshjohnson69@gmail.com")
        print("   4. Grant all required permissions")
        print("   5. Copy the new connection ID")
        
        print("\n🔧 STEP 4: After connecting, update your .env file:")
        print("   Add or update: COMPOSIO_GMAIL_CONNECTION_ID=<new_connection_id>")
        
        print("\n✅ Manual steps required:")
        print("   1. Visit Composio dashboard")
        print("   2. Disconnect old Gmail connections")
        print("   3. Connect fresh Gmail account")
        print("   4. Update .env with new connection ID")
        print("   5. Run test script to verify")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("🔧 Troubleshooting:")
        print("   • Check COMPOSIO_API_KEY in .env")
        print("   • Verify internet connection")
        print("   • Check Composio service status")

if __name__ == "__main__":
    main()