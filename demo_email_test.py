#!/usr/bin/env python3
"""
Demo Email Test - Shows how demo mode works
"""

import sys
import os
sys.path.insert(0, 'src')

from connectors.composio_email_connector import ComposioEmailConnector

print("🧪 Testing Demo Mode Email Functionality")
print("=" * 50)

# Demo mode - saves to file instead of sending
connector = ComposioEmailConnector(demo_mode=True)

result = connector.send_email(
    to='johnsonansh32@gmail.com',
    subject='Demo Mode Test - Email Saved Locally',
    html_body='''
    <h2>This email was saved to demo/outbox/ folder!</h2>
    <p>Perfect for development and testing.</p>
    <p>You can view the HTML file to see exactly what would be sent.</p>
    '''
)

print(f"📁 Demo email saved: {result}")
print("📂 Check the demo/outbox/ folder to see the HTML file!")