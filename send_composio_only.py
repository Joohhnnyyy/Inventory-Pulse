#!/usr/bin/env python3
"""
Send email using ONLY Composio Gmail Integration
From: anshjohnson69@gmail.com
To: johnsonansh32@gmail.com
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from src.connectors.composio_email_connector import ComposioEmailConnector

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
        connector = ComposioEmailConnector(demo_mode=False)
        
        # Email content
        subject = f"🔧 Composio-Only Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        html_body = f"""
        <html>
        <body>
            <h2>🔧 Composio-Only Email Delivery</h2>
            
            <div style="margin: 20px 0; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107;">
                <h3>📧 Email Details</h3>
                <p><strong>From:</strong> {sender}</p>
                <p><strong>To:</strong> {recipient}</p>
                <p><strong>Sent:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Method:</strong> Composio Gmail Integration ONLY</p>
                <p><strong>Connection ID:</strong> {os.getenv('COMPOSIO_GMAIL_CONNECTION_ID')}</p>
            </div>
            
            <p>Hello!</p>
            
            <p>This email was sent using <strong>ONLY</strong> the Composio Gmail integration. 
            No direct OAuth tokens or alternative methods were used.</p>
            
            <div style="margin: 20px 0; padding: 15px; background-color: #d1ecf1; border-left: 4px solid #17a2b8;">
                <h3>🔧 Composio Integration Details</h3>
                <ul>
                    <li><strong>Service:</strong> Composio Gmail</li>
                    <li><strong>API Key:</strong> {os.getenv('COMPOSIO_API_KEY')[:10]}...</li>
                    <li><strong>Connection:</strong> {os.getenv('COMPOSIO_GMAIL_CONNECTION_ID')}</li>
                    <li><strong>Account:</strong> anshjohnson69@gmail.com</li>
                    <li><strong>Mode:</strong> Production</li>
                </ul>
            </div>
            
            <div style="margin: 20px 0; padding: 15px; background-color: #d4edda; border-left: 4px solid #28a745;">
                <h3>✅ System Capabilities</h3>
                <p>The inventory management system can now:</p>
                <ul>
                    <li>✅ Send approval emails via Composio</li>
                    <li>✅ Process webhook responses</li>
                    <li>✅ Update Notion databases</li>
                    <li>✅ Sync with Google Sheets</li>
                    <li>✅ Generate LLM-powered recommendations</li>
                </ul>
            </div>
            
            <div style="margin: 20px 0; padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6; text-align: center;">
                <p><strong>Action Buttons (Demo)</strong></p>
                <a href="http://localhost:8000/webhook/approve?demo=true" 
                   style="display: inline-block; margin: 5px; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">
                   ✅ APPROVE
                </a>
                <a href="http://localhost:8000/webhook/reject?demo=true" 
                   style="display: inline-block; margin: 5px; padding: 10px 20px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px;">
                   ❌ REJECT
                </a>
            </div>
            
            <p>Best regards,<br>
            <strong>Ansh Johnson</strong><br>
            Inventory Management System</p>
            
            <hr>
            <p><small>
                Message ID: composio_{timestamp}<br>
                Sent via: Composio Gmail Integration<br>
                Timestamp: {timestamp}
            </small></p>
        </body>
        </html>
        """
        
        # Send via Composio ONLY
        print("📤 Sending email via Composio...")
        
        result = connector.send_approval_email(
            to=recipient,
            subject=subject,
            html_body=html_body,
            approve_link="http://localhost:8000/webhook/approve?composio=true",
            reject_link="http://localhost:8000/webhook/reject?composio=true"
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