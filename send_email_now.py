#!/usr/bin/env python3
"""
Send email from anshjohnson69@gmail.com to johnsonansh32@gmail.com
Using the working Composio Gmail integration
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from src.connectors.composio_email_connector import ComposioEmailConnector

# Load environment variables
load_dotenv()

def send_email():
    """Send email using Composio Gmail integration"""
    
    print("📧 Sending Email via Composio Gmail Integration")
    print("=" * 60)
    
    # Email details
    sender = "anshjohnson69@gmail.com"
    recipient = "johnsonansh32@gmail.com"
    timestamp = int(datetime.now().timestamp())
    
    print(f"📤 From: {sender}")
    print(f"📥 To: {recipient}")
    print(f"🕒 Timestamp: {timestamp}")
    print("-" * 60)
    
    try:
        # Initialize Composio connector in production mode
        connector = ComposioEmailConnector(demo_mode=False)
        
        # Email content
        subject = f"📧 Email from Ansh - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        html_body = f"""
        <html>
        <body>
            <h2>📧 Email from Ansh Johnson</h2>
            
            <div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #007bff;">
                <p><strong>From:</strong> anshjohnson69@gmail.com</p>
                <p><strong>To:</strong> johnsonansh32@gmail.com</p>
                <p><strong>Sent:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Method:</strong> Composio Gmail Integration</p>
            </div>
            
            <p>Hello!</p>
            
            <p>This email was sent using the inventory management system's Gmail integration. 
            The system is now fully operational and ready for production use.</p>
            
            <div style="margin: 20px 0; padding: 15px; background-color: #d4edda; border-left: 4px solid #28a745;">
                <h3>✅ System Status</h3>
                <ul>
                    <li>Gmail Integration: <strong>Active</strong></li>
                    <li>Email Delivery: <strong>Working</strong></li>
                    <li>Connection ID: <strong>{os.getenv('COMPOSIO_GMAIL_CONNECTION_ID')}</strong></li>
                    <li>Production Mode: <strong>Enabled</strong></li>
                </ul>
            </div>
            
            <p>The inventory management system can now:</p>
            <ul>
                <li>Send approval emails for inventory decisions</li>
                <li>Process webhook responses</li>
                <li>Update Notion databases</li>
                <li>Sync with Google Sheets</li>
            </ul>
            
            <p>Best regards,<br>
            <strong>Ansh Johnson</strong><br>
            Inventory Management System</p>
            
            <hr>
            <p><small>Message ID: email_{timestamp} | Sent via Composio Gmail Integration</small></p>
        </body>
        </html>
        """
        
        # Send the email
        print("🚀 Sending email...")
        
        result = connector.send_approval_email(
            to=recipient,
            subject=subject,
            html_body=html_body,
            approve_link="http://localhost:8000/webhook/approve?demo=true",
            reject_link="http://localhost:8000/webhook/reject?demo=true"
        )
        
        print(f"✅ Email sent successfully!")
        print(f"📧 Message ID: {result}")
        print(f"📬 Subject: {subject}")
        print(f"📥 Check inbox: {recipient}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return None

def main():
    """Main function"""
    print("🎯 Email Send Request")
    print("=" * 60)
    
    result = send_email()
    
    if result:
        print("\n" + "=" * 60)
        print("🎉 EMAIL SENT SUCCESSFULLY!")
        print("=" * 60)
        print(f"✅ Message delivered with ID: {result}")
        print("📋 Next Steps:")
        print("   1. Check johnsonansh32@gmail.com inbox")
        print("   2. Look in Primary, Promotions, or Updates tabs")
        print("   3. Check spam folder if not found")
        print("   4. Email should arrive within 1-2 minutes")
    else:
        print("\n❌ Email sending failed")

if __name__ == "__main__":
    main()