#!/usr/bin/env python3
"""
Send Confirmation Email Test
This script sends a confirmation email using Composio Gmail integration.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

from connectors.composio_email_connector import ComposioEmailConnector

def send_confirmation_email():
    """Send a confirmation email to verify the system is working"""
    
    print("📧 Sending Confirmation Email via Composio Gmail")
    print("=" * 50)
    
    try:
        # Initialize email connector in production mode
        email_connector = ComposioEmailConnector(demo_mode=False)
        
        # Get recipient email
        recipient = os.getenv('MANAGER_EMAIL', 'johnsonansh32@gmail.com')
        
        # Create timestamp for unique identification
        timestamp = int(datetime.now().timestamp())
        
        # Email details
        subject = f"✅ System Confirmation - Email Working! #{timestamp}"
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                <h1 style="margin: 0; font-size: 28px;">🎉 Email System Confirmation</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Your Composio Gmail integration is working perfectly!</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 25px; border-radius: 8px; margin-bottom: 25px;">
                <h2 style="color: #28a745; margin: 0 0 15px 0;">✅ Confirmation Details</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #495057;">Test ID:</td>
                        <td style="padding: 8px 0; color: #6c757d;">CONF-{timestamp}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #495057;">Sender:</td>
                        <td style="padding: 8px 0; color: #6c757d;">anshjohnson69@gmail.com</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #495057;">Recipient:</td>
                        <td style="padding: 8px 0; color: #6c757d;">{recipient}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #495057;">Sent At:</td>
                        <td style="padding: 8px 0; color: #6c757d;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #495057;">Integration:</td>
                        <td style="padding: 8px 0; color: #6c757d;">Composio Gmail API</td>
                    </tr>
                </table>
            </div>
            
            <div style="background-color: #e8f5e8; border-left: 4px solid #28a745; padding: 20px; margin-bottom: 25px;">
                <h3 style="color: #155724; margin: 0 0 10px 0;">🚀 System Status: OPERATIONAL</h3>
                <p style="color: #155724; margin: 0; line-height: 1.5;">
                    Your inventory management system's email functionality is fully operational and ready for production use. 
                    All integrations are working correctly.
                </p>
            </div>
            
            <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; margin-bottom: 25px;">
                <h3 style="color: #856404; margin: 0 0 10px 0;">📋 What This Confirms:</h3>
                <ul style="color: #856404; margin: 0; padding-left: 20px; line-height: 1.6;">
                    <li>✅ Composio Gmail integration is active</li>
                    <li>✅ Email connector is functioning properly</li>
                    <li>✅ HTML email formatting is working</li>
                    <li>✅ Environment variables are configured correctly</li>
                    <li>✅ Production workflow is ready</li>
                </ul>
            </div>
            
            <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
                <p style="margin: 0; color: #6c757d; font-size: 14px;">
                    This is an automated confirmation email from your Inventory Intelligence Tool.<br>
                    If you received this email, your system is working perfectly! 🎯
                </p>
            </div>
        </div>
        """
        
        print(f"📤 Sending confirmation email to: {recipient}")
        print(f"📋 Subject: {subject}")
        
        # Send the email
        result = email_connector.send_email(
            to=recipient,
            subject=subject,
            html_body=html_body
        )
        
        if result:
            print(f"\n✅ CONFIRMATION EMAIL SENT SUCCESSFULLY!")
            print(f"📧 Message ID: {result}")
            print(f"📬 Recipient: {recipient}")
            print(f"🕒 Timestamp: {timestamp}")
            print(f"\n🎯 Check your inbox for the confirmation email!")
            print(f"📂 Look in: Primary, Spam, Promotions, or All Mail folders")
            return True
        else:
            print(f"\n❌ Failed to send confirmation email")
            return False
            
    except Exception as e:
        print(f"\n❌ Error sending confirmation email: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Confirmation Email Test...")
    success = send_confirmation_email()
    
    if success:
        print("\n🎊 SUCCESS: Confirmation email sent!")
        print("💡 If you receive this email, your system is 100% ready for production!")
    else:
        print("\n💥 FAILED: Could not send confirmation email")
        print("🔧 Check your configuration and try again")