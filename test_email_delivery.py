#!/usr/bin/env python3
"""
Email Delivery Test Script
Tests both email connectors and troubleshoots delivery issues
"""

from src.connectors.composio_email_connector_class import ComposioEmailConnector
from datetime import datetime
import time

def test_email_delivery():
    print('🧪 Testing Email Delivery to Multiple Recipients...')
    print('=' * 60)

    connector = ComposioEmailConnector(demo_mode=False)
    timestamp = datetime.now().strftime('%H:%M:%S')

    # Test emails to different recipients
    recipients = [
        'johnsonansh32@gmail.com',  # Original recipient
        'anshjohnson69@gmail.com'   # Send to self to test delivery
    ]

    results = []
    
    for i, recipient in enumerate(recipients, 1):
        print(f'\n📧 Test {i}: Sending to {recipient}')
        
        subject = f'🔍 DELIVERY TEST {i} - {timestamp}'
        html_body = f'''
        <div style="font-family: Arial, sans-serif;">
            <h2>📧 Email Delivery Test #{i}</h2>
            <p><strong>Recipient:</strong> {recipient}</p>
            <p><strong>Sent at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Test Purpose:</strong> Verify email delivery functionality</p>
            
            <div style="background: #e8f5e8; padding: 10px; border-radius: 5px;">
                <p>✅ If you receive this email, delivery is working for this recipient!</p>
            </div>
        </div>
        '''
        
        try:
            result = connector.send_email(
                to=recipient,
                subject=subject,
                html_body=html_body
            )
            print(f'   ✅ SUCCESS - Message ID: {result}')
            results.append((recipient, True, result))
            
            if recipient == 'anshjohnson69@gmail.com':
                print('   📱 Check anshjohnson69@gmail.com inbox (sender account)')
            else:
                print('   📱 Check johnsonansh32@gmail.com inbox (recipient account)')
                
        except Exception as e:
            print(f'   ❌ FAILED - Error: {str(e)}')
            results.append((recipient, False, str(e)))

    print('\n🔍 RESULTS SUMMARY:')
    print('-' * 40)
    for recipient, success, result in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f'{recipient}: {status}')
        if success:
            print(f'   Message ID: {result}')
        else:
            print(f'   Error: {result}')

    print('\n🔍 TROUBLESHOOTING CHECKLIST:')
    print('1. Check BOTH email accounts:')
    print('   - anshjohnson69@gmail.com (should receive Test 2)')
    print('   - johnsonansh32@gmail.com (should receive Test 1)')
    print('2. If Test 2 works but Test 1 doesn\'t, the issue is with the recipient')
    print('3. If both fail, the issue is with the sending configuration')
    print('4. If both work, check delivery timing and folders')
    print('5. Check ALL Gmail folders: Inbox, Spam, Promotions, Social, Updates')
    print('6. Search Gmail for: "from:anshjohnson69@gmail.com"')
    print('7. Check if emails are being filtered or forwarded')

if __name__ == "__main__":
    test_email_delivery()