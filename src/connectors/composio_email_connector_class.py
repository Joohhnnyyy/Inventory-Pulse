"""
Composio Email Connector

Handles email communications using Composio's Gmail integration for inventory replenishment approval workflows.
Supports both production mode (actual email sending) and demo mode (file output).
"""

import os
import logging
import uuid
from typing import Optional
from datetime import datetime
from pathlib import Path
from composio import Composio, Action


class ComposioEmailConnector:
    """
    Email connector that uses Composio's Gmail integration to send emails.
    Supports both production mode (actual Gmail operations) and demo mode (file output).
    """
    
    def __init__(self, demo_mode: bool = False):
        """
        Initialize the Composio Email Connector
        
        Args:
            demo_mode (bool): If True, runs in demo mode without sending actual emails
                             Default is False for production use
        """
        self.demo_mode = demo_mode
        self.logger = logging.getLogger(__name__)
        self.gmail_connected_account = None
        
        if not demo_mode:
            # Initialize Composio client
            try:
                self.composio_client = Composio()
                
                # Check for Gmail integration and get connected account
                connected_accounts = self.composio_client.connected_accounts.get()
                for account in connected_accounts:
                    if account.appName.lower() == 'gmail' and account.status == 'ACTIVE':
                        self.gmail_connected_account = account.id
                        self.logger.info(f"✅ Found active Gmail connected account: {account.id}")
                        break
                        
                if not self.gmail_connected_account:
                    raise ValueError("No active Gmail connected account found")
                
                self.logger.info("✅ Gmail integration available via Composio")
                
            except Exception as e:
                self.logger.error(f"❌ Error initializing Composio Gmail integration: {str(e)}")
                raise
        else:
            # Ensure demo outbox directory exists if in demo mode
            self.outbox_dir = Path("demo/outbox")
            self.outbox_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info("📝 Running in demo mode - emails will not be sent")

    def send_email(self, to: str, subject: str, html_body: str) -> str:
        """
        Send a simple email using Composio Gmail integration.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            html_body: HTML email body content
            
        Returns:
            str: Message ID or file path (in demo mode)
            
        Raises:
            Exception: If email sending fails
        """
        try:
            # Generate unique message ID
            message_id = f"composio_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
            
            if self.demo_mode:
                return self._write_demo_email(to, subject, html_body, message_id)
            else:
                return self._send_composio_email(to, subject, html_body, message_id)
                
        except Exception as e:
            self.logger.error(f"Error sending email to {to}: {str(e)}")
            raise

    def send_approval_email(self, to: str, subject: str, html_body: str, 
                           approve_link: str, reject_link: str) -> str:
        """
        Send an approval email with approve/reject links using Composio Gmail integration.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            html_body: HTML email body content
            approve_link: URL for approval action
            reject_link: URL for rejection action
            
        Returns:
            str: Message ID or file path (in demo mode)
            
        Raises:
            Exception: If email sending fails
        """
        try:
            # Generate unique message ID
            message_id = f"composio_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
            
            # Create complete HTML email with approval buttons
            complete_html = self._create_approval_email_template(
                html_body, approve_link, reject_link
            )
            
            if self.demo_mode:
                return self._write_demo_email(to, subject, complete_html, message_id)
            else:
                return self._send_composio_email(to, subject, complete_html, message_id)
                
        except Exception as e:
            self.logger.error(f"Error sending approval email to {to}: {str(e)}")
            raise

    def _send_composio_email(self, to: str, subject: str, html_body: str, message_id: str) -> str:
        """
        Send email via Composio Gmail integration.
        
        Args:
            to: Recipient email
            subject: Email subject
            html_body: HTML email content
            message_id: Unique message identifier
            
        Returns:
            str: Message ID
            
        Raises:
            Exception: If Composio sending fails
        """
        try:
            # Execute Gmail send action via Composio
            response = self.composio_client.actions.execute(
                action=Action.GMAIL_SEND_EMAIL,
                params={
                    "to": to,
                    "subject": subject,
                    "body": html_body,
                    "bodyType": "html"
                },
                entity_id="default",
                connected_account=self.gmail_connected_account
            )
            
            # Extract message ID from response
            if response and hasattr(response, 'data') and response.data:
                composio_message_id = response.data.get('id', message_id)
                self.logger.info(f"Email sent successfully to {to} via Composio (Message ID: {composio_message_id})")
                return composio_message_id
            else:
                self.logger.info(f"Email sent successfully to {to} via Composio (Message ID: {message_id})")
                return message_id
            
        except Exception as e:
            self.logger.error(f"Composio Gmail sending failed: {str(e)}")
            raise

    def _create_approval_email_template(self, body_content: str, approve_link: str, reject_link: str) -> str:
        """
        Create a complete HTML email template with approval buttons.
        
        Args:
            body_content: Main email content
            approve_link: Approval webhook URL
            reject_link: Rejection webhook URL
            
        Returns:
            str: Complete HTML email template
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inventory Replenishment Approval</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .email-container {{
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
            font-size: 24px;
        }}
        .content {{
            margin-bottom: 30px;
        }}
        .approval-buttons {{
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 6px;
        }}
        .btn {{
            display: inline-block;
            padding: 12px 30px;
            margin: 0 10px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            font-size: 16px;
            transition: all 0.3s ease;
        }}
        .btn-approve {{
            background-color: #28a745;
            color: white;
        }}
        .btn-approve:hover {{
            background-color: #218838;
        }}
        .btn-reject {{
            background-color: #dc3545;
            color: white;
        }}
        .btn-reject:hover {{
            background-color: #c82333;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            font-size: 12px;
            color: #6c757d;
        }}
        .timestamp {{
            font-size: 11px;
            color: #adb5bd;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🔄 Inventory Replenishment Request</h1>
        </div>
        
        <div class="content">
            {body_content}
        </div>
        
        <div class="approval-buttons">
            <h3>Action Required</h3>
            <p>Please review the request above and choose an action:</p>
            <a href="{approve_link}" class="btn btn-approve">✅ Approve Order</a>
            <a href="{reject_link}" class="btn btn-reject">❌ Reject Order</a>
        </div>
        
        <div class="footer">
            <p>This is an automated message from the Inventory Replenishment System.</p>
            <p>Sent via Composio Gmail Integration</p>
            <div class="timestamp">
                Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
            </div>
        </div>
    </div>
</body>
</html>
"""

    def _write_demo_email(self, to: str, subject: str, html_body: str, message_id: str) -> str:
        """
        Write email to demo/outbox/ directory for demo mode.
        
        Args:
            to: Recipient email
            subject: Email subject
            html_body: HTML email content
            message_id: Unique message identifier
            
        Returns:
            str: File path where email was saved
        """
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{message_id}.html"
            file_path = self.outbox_dir / filename
            
            # Create email metadata and content
            email_content = f"""<!--
EMAIL METADATA:
To: {to}
Subject: {subject}
Message-ID: {message_id}
Generated: {datetime.now().isoformat()}
Method: Composio Gmail Integration (Demo Mode)
-->

{html_body}
"""
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(email_content)
            
            self.logger.info(f"Demo email written to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to write demo email: {str(e)}")
            raise


if __name__ == "__main__":
    """
    Example usage of the Composio Email connector.
    Creates a sample email in demo mode.
    """
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize connector in demo mode
        connector = ComposioEmailConnector(demo_mode=True)
        
        # Sample email data
        recipient = "johnsonansh32@gmail.com"
        subject = "Test Email - Composio Gmail Integration"
        
        # Sample email body content
        html_body = """
        <h2>📧 Composio Gmail Integration Test</h2>
        <p>This is a test email sent using the <strong>ComposioEmailConnector</strong> class.</p>
        <p><strong>Integration:</strong> Composio Gmail</p>
        <p><strong>Mode:</strong> Demo (no actual email sent)</p>
        <p>If you see this in the demo folder, the integration is working correctly!</p>
        """
        
        print("Sending sample email via Composio...")
        result = connector.send_email(
            to=recipient,
            subject=subject,
            html_body=html_body
        )
        
        print(f"✅ Email processed successfully!")
        print(f"📁 Demo file saved to: {result}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")