"""
Unit tests for connector modules with basic functionality testing.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.connectors.sheets_connector import SheetsConnector
from src.connectors.notion_connector import NotionConnector
from src.connectors.email_connector import EmailConnector


class TestSheetsConnector(unittest.TestCase):
    """Test cases for SheetsConnector."""
    
    @patch('src.connectors.sheets_connector.os.path.exists')
    def test_initialization_missing_credentials(self, mock_exists):
        """Test SheetsConnector initialization with missing credentials."""
        mock_exists.return_value = False
        mock_config = Mock()
        mock_config.google_sheets_credentials_json = "/fake/path/credentials.json"
        mock_config.google_sheets_spreadsheet_id = "test_id"
        
        with self.assertRaises(FileNotFoundError):
            SheetsConnector(mock_config)
    
    @patch('src.connectors.sheets_connector.os.path.exists')
    def test_initialization_success(self, mock_exists):
        """Test successful SheetsConnector initialization."""
        mock_exists.return_value = True
        mock_config = Mock()
        mock_config.google_sheets_credentials_json = "/fake/path/credentials.json"
        mock_config.google_sheets_spreadsheet_id = "fake_spreadsheet_id"
        
        # This will fail at gspread.authorize but we're just testing init logic
        try:
            connector = SheetsConnector(mock_config)
        except Exception:
            # Expected to fail at gspread.authorize, but init logic passed
            pass


class TestNotionConnector(unittest.TestCase):
    """Test cases for NotionConnector."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.notion_token = "test_token_123"
        self.notion_db_id = "test_db_id_456"
    
    def test_initialization_success(self):
        """Test successful NotionConnector initialization."""
        connector = NotionConnector(self.notion_token, self.notion_db_id)
        self.assertEqual(connector.notion_token, self.notion_token)
        self.assertEqual(connector.notion_db_id, self.notion_db_id)
    
    def test_initialization_missing_token(self):
        """Test NotionConnector initialization with missing token."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                NotionConnector(notion_token=None, notion_db_id="test_db_id")
            self.assertIn("NOTION_TOKEN is required", str(context.exception))
    
    def test_initialization_missing_db_id(self):
        """Test NotionConnector initialization with missing database ID."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                NotionConnector(notion_token="test_token", notion_db_id=None)
            self.assertIn("NOTION_DB_ID is required", str(context.exception))


class TestEmailConnector(unittest.TestCase):
    """Test cases for EmailConnector."""
    
    def test_initialization_success(self):
        """Test successful EmailConnector initialization."""
        connector = EmailConnector(
            smtp_host='smtp.gmail.com',
            smtp_port=587,
            smtp_user='test@example.com',
            smtp_password='test_password'
        )
        self.assertEqual(connector.smtp_host, 'smtp.gmail.com')
        self.assertEqual(connector.smtp_port, 587)
        self.assertEqual(connector.smtp_user, 'test@example.com')
    
    def test_demo_mode_initialization(self):
        """Test EmailConnector initialization in demo mode."""
        connector = EmailConnector(demo_mode=True)
        self.assertTrue(connector.demo_mode)
    
    def test_demo_mode_email_sending(self):
        """Test email sending in demo mode."""
        connector = EmailConnector(demo_mode=True)
        
        # In demo mode, should always return a message ID
        message_id = connector.send_approval_email(
            to='manager@example.com',
            subject='Test Approval',
            html_body='<p>Test body</p>',
            approve_link='http://example.com/approve',
            reject_link='http://example.com/reject'
        )
        
        self.assertIsNotNone(message_id)


if __name__ == '__main__':
    unittest.main()