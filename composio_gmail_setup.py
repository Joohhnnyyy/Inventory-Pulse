#!/usr/bin/env python3
"""
Composio Gmail Setup & Reset
Using correct Composio SDK methods
"""

import os
from dotenv import load_dotenv
from composio import ComposioToolSet, App
import json

def main():
    print("🔄 COMPOSIO GMAIL SETUP & RESET")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize Composio toolset
        composio_api_key = os.getenv('COMPOSIO_API_KEY')
        if not composio_api_key:
            print("❌ COMPOSIO_API_KEY not found in .env file!")
            return
            
        print(f"🔑 Using Composio API Key: {composio_api_key[:10]}...")
        
        # Initialize toolset
        toolset = ComposioToolSet(api_key=composio_api_key)
        
        print("\n📋 STEP 1: Checking Gmail app status...")
        
        # Try to get Gmail connected accounts
        try:
            # Get entity (user) information
            entity = toolset.client.connected_accounts.get()
            print(f"✅ Connected to Composio successfully")
            
            # List connected accounts
            accounts = entity
            print(f"📊 Account information retrieved")
            
        except Exception as e:
            print(f"⚠️  Could not retrieve account info: {str(e)}")
        
        print("\n🔗 STEP 2: Gmail Connection Instructions")
        print("=" * 60)
        
        print("📋 To reset and reconnect Gmail account:")
        print()
        print("1. 🌐 Visit Composio Dashboard:")
        print("   https://app.composio.dev/")
        print()
        print("2. 🔐 Login with your Composio account")
        print()
        print("3. 📧 Navigate to Gmail App:")
        print("   https://app.composio.dev/apps/gmail")
        print()
        print("4. 🗑️  Disconnect existing connections:")
        print("   • Look for any existing Gmail connections")
        print("   • Click 'Disconnect' on old connections")
        print()
        print("5. ➕ Add new Gmail connection:")
        print("   • Click 'Connect Account' or '+ Add Account'")
        print("   • Authenticate with: anshjohnson69@gmail.com")
        print("   • Grant all required permissions:")
        print("     ✅ Read emails")
        print("     ✅ Send emails") 
        print("     ✅ Manage drafts")
        print("     ✅ Access Gmail API")
        print()
        print("6. 📋 Copy the Connection ID:")
        print("   • After successful connection")
        print("   • Copy the generated connection ID")
        print("   • It looks like: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'")
        print()
        print("7. 🔧 Update .env file:")
        print("   • Add: COMPOSIO_GMAIL_CONNECTION_ID=<your_new_connection_id>")
        print("   • Save the file")
        
        print("\n🧪 STEP 3: Test the new connection")
        print("=" * 60)
        print("After completing the above steps, run:")
        print("   python test_new_gmail_connection.py")
        
        print("\n📝 Current .env Gmail settings:")
        gmail_conn_id = os.getenv('COMPOSIO_GMAIL_CONNECTION_ID')
        if gmail_conn_id:
            print(f"   COMPOSIO_GMAIL_CONNECTION_ID: {gmail_conn_id}")
        else:
            print("   COMPOSIO_GMAIL_CONNECTION_ID: ❌ Not set")
        
        print(f"   COMPOSIO_API_KEY: ✅ Set ({composio_api_key[:10]}...)")
        
        print("\n🎯 Next Steps:")
        print("1. Complete the manual Gmail connection steps above")
        print("2. Update your .env file with the new connection ID")
        print("3. Run the test script to verify the connection")
        print("4. Send test emails to confirm delivery")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   • Verify COMPOSIO_API_KEY in .env")
        print("   • Check internet connection")
        print("   • Visit https://app.composio.dev/ to manage connections manually")

if __name__ == "__main__":
    main()