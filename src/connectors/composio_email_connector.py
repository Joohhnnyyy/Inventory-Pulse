#!/usr/bin/env python3
"""
Send email using ONLY Composio Gmail Integration
From: anshjohnson69@gmail.com
To: johnsonansh32@gmail.com
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from composio_email_connector_class import ComposioEmailConnector

# Load environment variables
load_dotenv()

def send_composio_email():
    """Send email using ONLY Composio Gmail integration"""
    
    print("🔧 Composio-Only Email Send")
    print("=" * 60)
    
    # Email details
    sender = "anshjohnson69@gmail.com"
    recipient = "johnsonansh32@gmail.com"
    timestamp = int(datetime.now().timestamp())
    
    print(f"📤 From: {sender}")
    print(f"📥 To: {recipient}")
    print(f"🔧 Method: Composio Gmail Integration ONLY")
    print(f"🆔 Connection ID: {os.getenv('COMPOSIO_GMAIL_CONNECTION_ID')}")
    print(f"🕒 Timestamp: {timestamp}")
    print("-" * 60)
    
    try:
        # Initialize ONLY Composio connector (no direct OAuth)
        print("🚀 Initializing Composio Gmail connector...")
        connector = ComposioEmailConnector(demo_mode=False)  # Set to True for testing without sending
        
        # Email content
        subject = f"🔧 Composio-Only Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        html_body = f"<p>This is a test email sent using Composio's Gmail integration.</p>"
        
        # Send via Composio ONLY
        print("📤 Sending email via Composio...")
        
        result = connector.send_email(
            to=recipient,
            subject=subject,
            html_body=html_body
        )
        
        print(f"✅ Email sent successfully via Composio!")
        print(f"📧 Message ID: {result}")
        print(f"📬 Subject: {subject}")
        print(f"📥 Recipient: {recipient}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error sending email via Composio: {str(e)}")
        return None

def main():
    """Main function"""
    print("🎯 Composio-Only Email Request")
    print("=" * 60)
    
    result = send_composio_email()
    
    if result:
        print("\n" + "=" * 60)
        print("🎉 COMPOSIO EMAIL SENT SUCCESSFULLY!")
        print("=" * 60)
        print(f"✅ Message delivered via Composio with ID: {result}")
        print(f"🔧 Method: Composio Gmail Integration ONLY")
        print(f"🆔 Connection: {os.getenv('COMPOSIO_GMAIL_CONNECTION_ID')}")
        print("\n📋 Next Steps:")
        print("   1. Check johnsonansh32@gmail.com inbox")
        print("   2. Look in Primary, Promotions, or Updates tabs")
        print("   3. Check spam folder if not found")
        print("   4. Email should arrive within 1-2 minutes")
        print("   5. Verify it shows 'Composio-Only' in subject")
    else:
        print("\n❌ Composio email sending failed")

if __name__ == "__main__":
    main()