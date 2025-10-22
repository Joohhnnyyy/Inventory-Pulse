#!/usr/bin/env python3
"""
Simple Email Debug - Focus on delivery
"""

import os
import time
from dotenv import load_dotenv
from src.connectors.composio_email_connector import ComposioEmailConnector

def send_debug_email():
    """Send a simple debug email with tracking"""
    load_dotenv()
    
    print("🔍 SIMPLE EMAIL DEBUG")
    print("=" * 40)
    
    recipient = "johnsonansh32@gmail.com"
    sender = "anshjohnson69@gmail.com"
    
    print(f"📧 From: {sender}")
    print(f"📬 To: {recipient}")
    
    try:
        # Initialize connector
        print("\n🔌 Initializing email connector...")
        connector = ComposioEmailConnector(demo_mode=False)
        
        # Create timestamp for tracking
        timestamp = int(time.time())
        
        # Simple, clear email
        subject = f"✅ Email Test #{timestamp}"
        
        html_body = f"""
        <h2>📧 Email Delivery Test</h2>
        <p><strong>Test ID:</strong> {timestamp}</p>
        <p><strong>Time:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>From:</strong> {sender}</p>
        <p><strong>To:</strong> {recipient}</p>
        
        <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3>✅ SUCCESS!</h3>
            <p>If you're reading this email, the delivery system is working correctly!</p>
        </div>
        
        <p><strong>Next steps:</strong></p>
        <ul>
            <li>Reply to this email to confirm receipt</li>
            <li>Check if previous emails are in spam folder</li>
            <li>Add {sender} to your contacts</li>
        </ul>
        
        <hr>
        <small>Sent via Composio Gmail API - Test ID: {timestamp}</small>
        """
        
        print(f"📤 Sending email...")
        print(f"   Subject: {subject}")
        
        # Send email
        result = connector.send_approval_email(
            to=recipient,
            subject=subject,
            html_body=html_body,
            approve_link="http://localhost:8000/test/approve",
            reject_link="http://localhost:8000/test/reject"
        )
        
        print(f"\n✅ EMAIL SENT SUCCESSFULLY!")
        print(f"📧 Message ID: {result}")
        print(f"🕐 Timestamp: {timestamp}")
        print(f"📬 Recipient: {recipient}")
        
        print(f"\n🔍 TROUBLESHOOTING TIPS:")
        print(f"   1. Check INBOX first")
        print(f"   2. Check SPAM/JUNK folder")
        print(f"   3. Check PROMOTIONS tab (Gmail)")
        print(f"   4. Search for: {sender}")
        print(f"   5. Search for: Test #{timestamp}")
        print(f"   6. Wait 2-5 minutes for delivery")
        
        print(f"\n📧 If still no email, possible issues:")
        print(f"   - Email might be blocked by recipient's server")
        print(f"   - Gmail might be rate limiting")
        print(f"   - Check Gmail account settings")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    send_debug_email()