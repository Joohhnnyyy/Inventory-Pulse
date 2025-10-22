"""
Email Connector

Handles email communications for inventory replenishment approval workflows.
Supports SMTP, Gmail API, and demo mode with file output fallback.
"""

import os
import logging
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
from pathlib import Path

class EmailConnector:
    """
    Connector for email communications with approval workflow support.
    
    Supports multiple sending methods:
    - SMTP (generic or Gmail)
    - Gmail API (if available)
    - Demo mode (writes to demo/outbox/ directory)
    """
    
    def __init__(self, smtp_host: Optional[str] = None, smtp_port: Optional[int] = None,
                 smtp_user: Optional[str] = None, smtp_password: Optional[str] = None,
                 app_host: Optional[str] = None, demo_mode: bool = False):
        """
        Initialize the email connector.
        
        Args:
            smtp_host: SMTP server hostname (or from GMAIL_SMTP_HOST env var)
            smtp_port: SMTP server port (or from GMAIL_SMTP_PORT env var)
            smtp_user: SMTP username (or from GMAIL_USER env var)
            smtp_password: SMTP password/token (or from GMAIL_PASSWORD_OR_TOKEN env var)
            app_host: Application host for webhook URLs (or from APP_HOST env var)
            demo_mode: If True, writes emails to demo/outbox/ instead of sending
        """
        self.logger = logging.getLogger(__name__)
        
        # Get configuration from parameters or environment
        self.smtp_host = smtp_host or os.getenv('GMAIL_SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(smtp_port or os.getenv('GMAIL_SMTP_PORT', '587'))
        self.smtp_user = smtp_user or os.getenv('GMAIL_USER')
        self.smtp_password = smtp_password or os.getenv('GMAIL_PASSWORD_OR_TOKEN')
        self.app_host = app_host or os.getenv('APP_HOST', 'http://localhost:8000')
        self.demo_mode = demo_mode
        
        # Validate configuration for non-demo mode
        if not self.demo_mode:
            if not self.smtp_user or not self.smtp_password:
                self.logger.warning("SMTP credentials not provided, falling back to demo mode")
                self.demo_mode = True
        
        # Ensure demo outbox directory exists if in demo mode
        if self.demo_mode:
            self.outbox_dir = Path("demo/outbox")
            self.outbox_dir.mkdir(parents=True, exist_ok=True)
        
        mode = "demo" if self.demo_mode else "SMTP"
        self.logger.info(f"Email connector initialized in {mode} mode")
    
    def send_approval_email(self, to: str, subject: str, html_body: str, 
                           approve_link: str, reject_link: str) -> str:
        """
        Send an approval email with approve/reject links.
        
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
            message_id = f"msg_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
            
            # Create complete HTML email with approval buttons
            complete_html = self._create_approval_email_template(
                html_body, approve_link, reject_link
            )
            
            if self.demo_mode:
                return self._write_demo_email(to, subject, complete_html, message_id)
            else:
                return self._send_smtp_email(to, subject, complete_html, message_id)
                
        except Exception as e:
            self.logger.error(f"Error sending approval email to {to}: {str(e)}")
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
            <p>If you have questions, please contact your system administrator.</p>
            <div class="timestamp">
                Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    def _send_smtp_email(self, to: str, subject: str, html_body: str, message_id: str) -> str:
        """
        Send email via SMTP.
        
        Args:
            to: Recipient email
            subject: Email subject
            html_body: HTML email content
            message_id: Unique message identifier
            
        Returns:
            str: Message ID
            
        Raises:
            Exception: If SMTP sending fails
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = self.smtp_user
            message['To'] = to
            message['Subject'] = subject
            message['Message-ID'] = f"<{message_id}@inventory-system>"
            
            # Add HTML content
            html_part = MIMEText(html_body, 'html')
            message.attach(html_part)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to, message.as_string())
            
            self.logger.info(f"Email sent successfully to {to} (Message ID: {message_id})")
            return message_id
            
        except Exception as e:
            self.logger.error(f"SMTP sending failed: {str(e)}")
            raise
    
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
    Example usage of the Email connector.
    Creates a sample approval email in demo mode.
    """
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize connector in demo mode
        connector = EmailConnector(demo_mode=True)
        
        # Sample approval email data
        recipient = os.getenv('MANAGER_EMAIL', 'manager@company.com')
        subject = "Approval Required: Reorder WIDGET-001 (100 units)"
        
        # Sample email body content
        email_body = """
        <h2>Inventory Replenishment Request</h2>
        <p><strong>Item:</strong> Premium Widget Model A</p>
        <p><strong>SKU:</strong> WIDGET-001</p>
        <p><strong>Current Stock:</strong> 15 units</p>
        <p><strong>Minimum Threshold:</strong> 50 units</p>
        <p><strong>Requested Quantity:</strong> 100 units</p>
        <p><strong>Vendor:</strong> Acme Supplies Inc.</p>
        <p><strong>Total Cost:</strong> $1,250.00</p>
        <p><strong>EOQ:</strong> 150 units</p>
        
        <h3>Forecast & Evidence</h3>
        <p><strong>Demand Forecast:</strong> Based on Q4 sales trends, expecting 25% increase in demand</p>
        <ul>
            <li>Current stock: 15 units (below minimum threshold of 50)</li>
            <li>Average monthly consumption: 45 units</li>
            <li>Lead time: 14 days</li>
            <li>Seasonal demand spike expected in December</li>
        </ul>
        """
        
        # Generate approval/rejection webhook URLs
        token = "abc123def456"  # In real implementation, this would be a secure token
        approve_url = f"{connector.app_host}/webhook/approve?token={token}"
        reject_url = f"{connector.app_host}/webhook/reject?token={token}"
        
        print("Sending sample approval email...")
        result = connector.send_approval_email(
            to=recipient,
            subject=subject,
            html_body=email_body,
            approve_link=approve_url,
            reject_link=reject_url
        )
        
        print(f"✅ Email processed successfully!")
        print(f"📁 Demo file saved to: {result}")
        print(f"🌐 Approve URL: {approve_url}")
        print(f"🌐 Reject URL: {reject_url}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nFor SMTP mode, make sure you have set:")
        print("- GMAIL_SMTP_HOST (default: smtp.gmail.com)")
        print("- GMAIL_SMTP_PORT (default: 587)")
        print("- GMAIL_USER: Your email address")
        print("- GMAIL_PASSWORD_OR_TOKEN: Your app password or token")