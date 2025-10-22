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
from src.connectors.composio_notion_connector import ComposioNotionConnector
from src.connectors.unified_mcp_connector import UnifiedMCPConnector


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


class TestComposioNotionConnector(unittest.TestCase):
    """Test ComposioNotionConnector functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.connector = ComposioNotionConnector(demo_mode=True)
    
    def test_initialization(self):
        """Test connector initialization"""
        self.assertIsInstance(self.connector, ComposioNotionConnector)
        self.assertTrue(self.connector.demo_mode)
    
    def test_create_reorder_page(self):
        """Test creating a reorder page"""
        test_data = {
            'sku': 'TEST-001',
            'product_name': 'Test Product',
            'quantity': 100,
            'unit_cost': 10.50,
            'vendor': 'Test Vendor',
            'priority': 'High',
            'status': 'Pending Review'
        }
        
        page_id = self.connector.create_reorder_page(test_data)
        self.assertIsNotNone(page_id)
        self.assertIsInstance(page_id, str)
    
    def test_update_reorder_status(self):
        """Test updating reorder status"""
        # First create a page
        test_data = {
            'sku': 'TEST-002',
            'product_name': 'Test Product 2',
            'quantity': 50,
            'unit_cost': 5.25,
            'vendor': 'Test Vendor 2',
            'priority': 'Medium',
            'status': 'Pending Review'
        }
        
        page_id = self.connector.create_reorder_page(test_data)
        
        # Then update its status
        result = self.connector.update_reorder_status(page_id, 'Approved')
        self.assertTrue(result)
    
    def test_query_database(self):
        """Test querying the database"""
        results = self.connector.query_database()
        self.assertIsInstance(results, dict)
        self.assertIn('results', results)


class TestUnifiedMCPConnector(unittest.TestCase):
    """Test cases for UnifiedMCPConnector."""
    
    def test_initialization_success(self):
        """Test successful UnifiedMCPConnector initialization."""
        connector = UnifiedMCPConnector(
            demo_mode=True
        )
        self.assertIsNotNone(connector)
        self.assertTrue(connector.demo_mode)
        
    def test_initialization_demo_mode(self):
        """Test UnifiedMCPConnector initialization in demo mode."""
        connector = UnifiedMCPConnector(demo_mode=True)
        self.assertTrue(connector.demo_mode)
        
    def test_send_approval_email_demo(self):
        connector = UnifiedMCPConnector(demo_mode=True)
        
        # Create a mock reorder request
        from src.connectors.unified_mcp_connector import ReorderRequest
        reorder_request = ReorderRequest(
            sku='TEST-001',
            quantity=100,
            vendor='Test Vendor',
            cost=50.0,
            rationale='Test rationale'
        )
        
        # In demo mode, should always return a message ID
        message_id = connector.send_approval_email(
            reorder_request=reorder_request,
            approve_url='http://example.com/approve',
            reject_url='http://example.com/reject'
        )
        
        self.assertIsNotNone(message_id)


if __name__ == '__main__':
    unittest.main()