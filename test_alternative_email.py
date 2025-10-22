#!/usr/bin/env python3
"""
Alternative Email Delivery Test
Try different methods to ensure email delivery
"""

import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from src.connectors.composio_email_connector import ComposioEmailConnector

def test_direct_gmail_smtp():
    """Test direct Gmail SMTP without any wrapper"""
    load_dotenv()
    
    print("🔍 TESTING DIRECT GMAIL SMTP")
    print("=" * 50)
    
    # Gmail SMTP settings
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.getenv('GMAIL_EMAIL', 'anshjohnson69@gmail.com')
    sender_password = os.getenv('GMAIL_APP_PASSWORD', 'twph hsai maot llid')
    recipient = "johnsonansh32@gmail.com"
    
    print(f"📧 Sender: {sender_email}")
    print(f"📬 Recipient: {recipient}")
    print(f"🔑 Password: {'*' * len(sender_password)}")
    
    try:
        # Create message
        timestamp = int(time.time())
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚨 DIRECT SMTP TEST #{timestamp}"
        msg['From'] = sender_email
        msg['To'] = recipient
        
        # HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="background-color: #ff6b6b; color: white; padding: 20px; border-radius: 10px;">
                <h2>🚨 URGENT: Direct SMTP Email Test</h2>
                <p><strong>This email was sent via DIRECT Gmail SMTP (not Composio)</strong></p>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>📊 Test Details:</h3>
                <ul>
                    <li><strong>Method:</strong> Direct Gmail SMTP</li>
                    <li><strong>Server:</strong> smtp.gmail.com:587</li>
                    <li><strong>Test ID:</strong> {timestamp}</li>
                    <li><strong>Time:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
            </div>
            
            <div style="background-color: #28a745; color: white; padding: 15px; border-radius: 5px;">
                <h3>✅ SUCCESS!</h3>
                <p>If you receive this email, direct SMTP is working!</p>
                <p><strong>This bypasses all Composio integrations.</strong></p>
            </div>
            
            <div style="margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
                <p><strong>🔍 What this means:</strong></p>
                <ul>
                    <li>Gmail SMTP credentials are correct</li>
                    <li>Email delivery path is working</li>
                    <li>Issue might be with Composio integration</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        print(f"\n📤 Connecting to Gmail SMTP...")
        
        # Connect and send
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        
        print(f"✅ SMTP connection successful!")
        print(f"📧 Sending email...")
        
        text = msg.as_string()
        server.sendmail(sender_email, recipient, text)
        server.quit()
        
        print(f"\n🎉 DIRECT SMTP EMAIL SENT SUCCESSFULLY!")
        print(f"📧 Test ID: {timestamp}")
        print(f"📬 Check your inbox for: 'DIRECT SMTP TEST #{timestamp}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct SMTP failed: {str(e)}")
        return False

def test_composio_with_different_content():
    """Test Composio with very simple content"""
    print(f"\n🔍 TESTING COMPOSIO WITH SIMPLE CONTENT")
    print("=" * 50)
    
    try:
        connector = ComposioEmailConnector(demo_mode=False)
        timestamp = int(time.time())
        
        # Very simple email
        result = connector.send_approval_email(
            to="johnsonansh32@gmail.com",
            subject=f"Simple Test {timestamp}",
            html_body=f"<h1>Test {timestamp}</h1><p>Simple test email.</p>",
            approve_link="http://test.com/approve",
            reject_link="http://test.com/reject"
        )
        
        print(f"✅ Composio simple email sent: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Composio simple test failed: {str(e)}")
        return False

def main():
    """Run all email tests"""
    print("🚀 COMPREHENSIVE EMAIL DELIVERY TEST")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Direct SMTP
    results['direct_smtp'] = test_direct_gmail_smtp()
    
    # Test 2: Simple Composio
    results['composio_simple'] = test_composio_with_different_content()
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    for test, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test}: {status}")
    
    if results['direct_smtp']:
        print(f"\n🎯 RECOMMENDATION:")
        print(f"   Direct SMTP is working - check your inbox!")
        print(f"   If you receive the DIRECT SMTP email but not Composio emails,")
        print(f"   the issue is with the Composio integration.")
    else:
        print(f"\n⚠️  ISSUE IDENTIFIED:")
        print(f"   Gmail SMTP credentials or connection issue")
        print(f"   Check Gmail app password and account settings")

if __name__ == "__main__":
    main()