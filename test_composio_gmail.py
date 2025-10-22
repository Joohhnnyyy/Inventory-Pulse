#!/usr/bin/env python3
"""
Composio Gmail Test Script
Tests the ComposioEmailConnector in production mode using Gmail credentials
"""

from src.connectors.composio_email_connector import ComposioEmailConnector
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    print("🚀 Composio Gmail Test - Starting...")
    print("=" * 50)
    
    try:
        # Initialize Composio connector in PRODUCTION mode
        print("📧 Initializing ComposioEmailConnector in PRODUCTION mode...")
        connector = ComposioEmailConnector(demo_mode=False)
        print("✅ ComposioEmailConnector initialized successfully!")
        
        # Get recipient email
        recipient = os.getenv('MANAGER_EMAIL', 'johnsonansh32@gmail.com')
        subject = '🚀 Composio Gmail Test - PRODUCTION MODE'
        
        # Create email body
        email_body = """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2e7d32;">🚀 Composio Gmail Test - PRODUCTION</h2>
            <p>This email is sent via <strong>ComposioEmailConnector</strong> in production mode.</p>
            
            <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>🔧 Configuration:</strong></p>
                <ul>
                    <li><strong>Connector:</strong> ComposioEmailConnector</li>
                    <li><strong>Mode:</strong> Production (Real Gmail)</li>
                    <li><strong>Sender:</strong> anshjohnson69@gmail.com</li>
                    <li><strong>Recipient:</strong> johnsonansh32@gmail.com</li>
                    <li><strong>API:</strong> Composio Gmail Integration</li>
                </ul>
            </div>
            
            <div style="background-color: #f1f8e9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="color: #2e7d32;">
                    <strong>✅ SUCCESS!</strong> If you receive this email, your Composio Gmail integration is working perfectly!
                </p>
            </div>
            
            <hr style="margin: 30px 0;">
            <p style="font-size: 12px; color: #666;">
                Automated test from Inventory Intelligence Tool via Composio
            </p>
        </div>
        """
        
        print(f"📤 Sending Composio Gmail test to: {recipient}")
        print(f"📋 Subject: {subject}")
        print("⏳ Processing via Composio API...")
        
        # Send the email using Composio
        result = connector.send_email(
            to=recipient,
            subject=subject,
            html_body=email_body
        )
        
        print("\n" + "=" * 50)
        print("🎉 COMPOSIO EMAIL SENT SUCCESSFULLY!")
        print("=" * 50)
        print(f"✅ Message ID: {result}")
        print(f"📧 Recipient: {recipient}")
        print(f"📤 Sender: anshjohnson69@gmail.com (via Composio)")
        print(f"📋 Subject: {subject}")
        print(f"🔗 API: Composio Gmail Integration")
        print("\n📱 Please check your Gmail inbox!")
        print("📂 Also check: Spam, Promotions, Updates folders")
        print("\n💡 This uses the SAME system as your production workflow!")
        
    except Exception as e:
        print("\n" + "=" * 50)
        print("❌ COMPOSIO EMAIL FAILED!")
        print("=" * 50)
        print(f"Error: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   • Check COMPOSIO_API_KEY in .env")
        print("   • Verify Gmail credentials")
        print("   • Check Composio dashboard")

if __name__ == "__main__":
    main()