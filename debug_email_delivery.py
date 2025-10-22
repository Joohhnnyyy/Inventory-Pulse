#!/usr/bin/env python3
"""
Email Delivery Debug Script
Comprehensive debugging for email delivery issues
"""

import os
import time
from dotenv import load_dotenv
from src.connectors.composio_email_connector import ComposioEmailConnector

def debug_email_delivery():
    """Debug email delivery with detailed logging"""
    load_dotenv()
    
    print("🔍 EMAIL DELIVERY DEBUG SESSION")
    print("=" * 60)
    
    recipient = "johnsonansh32@gmail.com"
    sender = "anshjohnson69@gmail.com"
    
    print(f"📧 Sender: {sender}")
    print(f"📬 Recipient: {recipient}")
    print(f"🔑 Composio API Key: {os.getenv('COMPOSIO_API_KEY', 'NOT_SET')[:10]}...")
    
    try:
        # Initialize connector
        print("\n🔌 Initializing ComposioEmailConnector...")
        connector = ComposioEmailConnector(demo_mode=False)
        
        # Check connection status
        print("\n🔍 Checking Composio Gmail connection...")
        
        # Get connected accounts
        from composio import Composio
        composio_client = Composio(api_key=os.getenv('COMPOSIO_API_KEY'))
        
        try:
            connected_accounts = composio_client.get_connected_accounts()
            print(f"📊 Total connected accounts: {len(connected_accounts)}")
            
            gmail_accounts = [acc for acc in connected_accounts if 'gmail' in acc.app.lower()]
            print(f"📧 Gmail accounts found: {len(gmail_accounts)}")
            
            if gmail_accounts:
                for i, account in enumerate(gmail_accounts):
                    print(f"   Account {i+1}: {account.id}")
                    print(f"   Status: {getattr(account, 'status', 'Unknown')}")
                    print(f"   App: {account.app}")
            else:
                print("❌ No Gmail accounts found!")
                return
                
        except Exception as e:
            print(f"❌ Error checking accounts: {str(e)}")
            return
        
        # Send test email with detailed tracking
        print(f"\n📤 Sending detailed test email...")
        
        timestamp = int(time.time())
        subject = f"🔍 Email Delivery Debug Test - {timestamp}"
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f8ff; padding: 15px; border-radius: 5px; }}
                .content {{ margin: 20px 0; }}
                .footer {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; font-size: 12px; }}
                .success {{ color: #28a745; font-weight: bold; }}
                .info {{ color: #17a2b8; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🔍 Email Delivery Debug Test</h2>
                <p class="success">✅ This email was sent successfully via Composio Gmail API</p>
            </div>
            
            <div class="content">
                <h3>📊 Test Details:</h3>
                <ul>
                    <li><strong>Timestamp:</strong> {timestamp}</li>
                    <li><strong>Sender:</strong> {sender}</li>
                    <li><strong>Recipient:</strong> {recipient}</li>
                    <li><strong>Method:</strong> ComposioEmailConnector</li>
                    <li><strong>API:</strong> Composio Gmail Integration</li>
                </ul>
                
                <h3>🎯 Purpose:</h3>
                <p>This is a debug email to verify that emails are being delivered to your inbox. 
                If you receive this email, the delivery system is working correctly.</p>
                
                <h3>📧 What to check:</h3>
                <ul>
                    <li>Check your <strong>Inbox</strong></li>
                    <li>Check your <strong>Spam/Junk</strong> folder</li>
                    <li>Check <strong>Promotions</strong> tab (if using Gmail)</li>
                    <li>Search for emails from: <strong>{sender}</strong></li>
                </ul>
            </div>
            
            <div class="footer">
                <p class="info">🤖 Sent via Inventory Intelligence Tool - Email Debug System</p>
                <p>If you receive this email, please confirm receipt to complete the debug process.</p>
            </div>
        </body>
        </html>
        """
        
        # Send the email
        result = connector.send_approval_email(
            to=recipient,
            subject=subject,
            html_body=html_body,
            approve_link="http://localhost:8000/debug/approve",
            reject_link="http://localhost:8000/debug/reject"
        )
        
        print(f"✅ Email sent successfully!")
        print(f"📧 Message ID: {result}")
        print(f"⏰ Timestamp: {timestamp}")
        
        # Additional verification
        print(f"\n🔍 Email Delivery Verification:")
        print(f"   ✅ Composio API call: SUCCESS")
        print(f"   ✅ Message ID received: {result}")
        print(f"   ✅ No exceptions thrown: TRUE")
        
        print(f"\n📬 NEXT STEPS:")
        print(f"   1. Check your inbox at: {recipient}")
        print(f"   2. Look for subject: '{subject}'")
        print(f"   3. Check spam/junk folder if not in inbox")
        print(f"   4. Search for sender: {sender}")
        print(f"   5. Wait 2-3 minutes for delivery")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        print(f"📋 Full traceback:")
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🔍 DEBUG SESSION COMPLETED")

if __name__ == "__main__":
    debug_email_delivery()