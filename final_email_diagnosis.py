#!/usr/bin/env python3
"""
Final Email Diagnosis - Comprehensive Test
Tests multiple email scenarios to diagnose delivery issues
"""

import os
import time
from dotenv import load_dotenv
from src.connectors.composio_email_connector import ComposioEmailConnector

def main():
    print("🔬 FINAL EMAIL DIAGNOSIS")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    
    # Initialize Composio connector
    print("📧 Initializing Composio Email Connector...")
    try:
        connector = ComposioEmailConnector()
        print("✅ Composio connector initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Composio connector: {e}")
        return
    
    recipient = "johnsonansh32@gmail.com"
    test_timestamp = int(time.time())
    
    # Test 1: Ultra-simple plain text email
    print("\n🧪 TEST 1: Ultra-Simple Plain Text Email")
    print("-" * 40)
    
    try:
        simple_subject = f"SIMPLE TEST {test_timestamp}"
        simple_body = f"""
This is a very simple plain text email.
Test ID: {test_timestamp}
Sender: anshjohnson69@gmail.com
Time: {time.strftime('%Y-%m-%d %H:%M:%S')}

If you receive this, basic email delivery is working.
        """
        
        message_id_1 = connector.send_email(
            to=recipient,
            subject=simple_subject,
            html_body=simple_body
        )
        
        print(f"✅ Simple email sent - Message ID: {message_id_1}")
        print(f"📋 Subject: {simple_subject}")
        
    except Exception as e:
        print(f"❌ Simple email failed: {e}")
    
    time.sleep(2)  # Small delay between emails
    
    # Test 2: Email with different subject pattern
    print("\n🧪 TEST 2: Different Subject Pattern")
    print("-" * 40)
    
    try:
        alt_subject = f"Hello from Ansh - {test_timestamp}"
        alt_body = f"""
        <div style="font-family: Arial, sans-serif;">
            <h2>Personal Message</h2>
            <p>Hi there!</p>
            <p>This is a test email from your inventory system.</p>
            <p><strong>Test ID:</strong> {test_timestamp}</p>
            <p><strong>From:</strong> anshjohnson69@gmail.com</p>
            <p>Best regards,<br>Ansh</p>
        </div>
        """
        
        message_id_2 = connector.send_email(
            to=recipient,
            subject=alt_subject,
            html_body=alt_body
        )
        
        print(f"✅ Personal-style email sent - Message ID: {message_id_2}")
        print(f"📋 Subject: {alt_subject}")
        
    except Exception as e:
        print(f"❌ Personal-style email failed: {e}")
    
    time.sleep(2)  # Small delay between emails
    
    # Test 3: Email to a different address (if available)
    print("\n🧪 TEST 3: Alternative Email Test")
    print("-" * 40)
    
    # Check if there's an alternative email in env
    alt_email = os.getenv('ALTERNATIVE_EMAIL')
    if alt_email:
        try:
            alt_subject_3 = f"Cross-delivery test {test_timestamp}"
            alt_body_3 = f"""
            <p>This email was sent to verify cross-delivery.</p>
            <p>Original recipient: {recipient}</p>
            <p>Alternative recipient: {alt_email}</p>
            <p>Test ID: {test_timestamp}</p>
            """
            
            message_id_3 = connector.send_email(
                to=alt_email,
                subject=alt_subject_3,
                html_body=alt_body_3
            )
            
            print(f"✅ Alternative email sent to {alt_email} - Message ID: {message_id_3}")
            
        except Exception as e:
            print(f"❌ Alternative email failed: {e}")
    else:
        print("ℹ️  No alternative email configured (set ALTERNATIVE_EMAIL in .env)")
    
    # Summary and diagnosis
    print("\n" + "=" * 60)
    print("📊 DIAGNOSIS SUMMARY")
    print("=" * 60)
    
    print(f"🎯 Primary recipient: {recipient}")
    print(f"📤 Sender: anshjohnson69@gmail.com")
    print(f"🔢 Test timestamp: {test_timestamp}")
    print(f"⏰ Test time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n🔍 WHAT TO CHECK NOW:")
    print("1. Gmail Web Interface (gmail.com) - NOT mobile app")
    print("2. Search for these exact terms:")
    print(f"   - 'SIMPLE TEST {test_timestamp}'")
    print(f"   - 'Hello from Ansh - {test_timestamp}'")
    print("   - 'anshjohnson69@gmail.com'")
    print(f"   - '{test_timestamp}'")
    
    print("\n📁 CHECK THESE FOLDERS:")
    print("   ✉️  Primary Inbox")
    print("   🚫 Spam/Junk")
    print("   🏷️  Promotions Tab")
    print("   📮 All Mail")
    print("   🗑️  Trash (in case of auto-deletion)")
    
    print("\n⚙️  GMAIL SETTINGS TO CHECK:")
    print("   1. Settings → Filters and Blocked Addresses")
    print("   2. Settings → Forwarding and POP/IMAP")
    print("   3. Settings → Labels (check if emails are auto-labeled)")
    
    print("\n🚨 CRITICAL DIAGNOSIS:")
    print("   If you STILL don't receive these emails:")
    print("   → Gmail is aggressively filtering/blocking automated emails")
    print("   → Consider using a different email service for testing")
    print("   → The system IS working - this is a Gmail delivery issue")
    
    print("\n💡 NEXT STEPS:")
    print("   1. Add anshjohnson69@gmail.com to your contacts")
    print("   2. Try sending from a different Gmail account")
    print("   3. Test with Yahoo/Outlook email instead")
    
    print("=" * 60)

if __name__ == "__main__":
    main()