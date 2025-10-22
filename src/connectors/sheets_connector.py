"""Google Sheets Connector

Handles all interactions with Google Sheets for inventory data management.
Reads inventory and transaction data from specified worksheets."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import gspread
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from src.utils.config import Config
except ImportError:
    # Fallback for when running as a module
    from utils.config import Config

class SheetsConnector:
    """Connector for Google Sheets integration."""
    
    def __init__(self, config: Config):
        """Initialize the Google Sheets connector."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.spreadsheet = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Sheets client."""
        try:
            # Define the scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets'
            ]
            
            # Check if credentials file exists
            credentials_path = self.config.google_sheets_credentials_json
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"Google Sheets credentials file not found at: {credentials_path}. "
                    f"Please ensure you have downloaded the service account JSON file "
                    f"and placed it at the specified path."
                )
            
            # Load credentials
            credentials = Credentials.from_service_account_file(
                credentials_path,
                scopes=scope
            )
            
            # Initialize client
            self.client = gspread.authorize(credentials)
            
            # Open the spreadsheet
            try:
                self.spreadsheet = self.client.open_by_key(self.config.google_sheets_spreadsheet_id)
                self.logger.info("Google Sheets client initialized successfully")
            except gspread.SpreadsheetNotFound:
                raise ValueError(
                    f"Spreadsheet with ID '{self.config.google_sheets_spreadsheet_id}' not found. "
                    f"Please check the spreadsheet ID and ensure the service account has access."
                )
            
        except GoogleAuthError as e:
            self.logger.error(f"Google authentication failed: {e}")
            raise ValueError(
                f"Google Sheets authentication failed: {e}. "
                f"Please check your credentials file and ensure it's valid."
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise
    
    def read_inventory(self) -> List[Dict[str, Any]]:
        """
        Read inventory data from the 'Inventory' worksheet.
        
        Expected columns:
        - SKU: Product identifier
        - Description: Product description  
        - OnHand: Current stock quantity
        - Unit: Unit of measurement
        - LeadTimeDays: Supplier lead time
        - MinOrderQty: Minimum order quantity
        - VendorIDs: Comma-separated vendor identifiers
        - AutoOrderThreshold: Monetary threshold for auto-ordering
        - TrustScore: Supplier reliability score (0-100)
        
        Returns:
            List of dictionaries containing inventory data
        """
        try:
            # Get the Inventory worksheet
            try:
                worksheet = self.spreadsheet.worksheet("Inventory")
            except gspread.WorksheetNotFound:
                raise ValueError(
                    "Worksheet 'Inventory' not found. Please ensure your spreadsheet "
                    "contains a worksheet named 'Inventory' with the required columns."
                )
            
            # Get all records
            records = worksheet.get_all_records()
            
            if not records:
                self.logger.warning("No inventory data found in the worksheet")
                return []
            
            # Validate and process records
            processed_records = []
            required_columns = ['SKU', 'Description', 'OnHand', 'Unit', 'LeadTimeDays', 
                              'MinOrderQty', 'VendorIDs', 'AutoOrderThreshold', 'TrustScore']
            
            for i, record in enumerate(records, start=2):  # Start at 2 (header is row 1)
                try:
                    # Check for required columns
                    missing_columns = [col for col in required_columns if col not in record]
                    if missing_columns:
                        self.logger.warning(
                            f"Row {i}: Missing columns {missing_columns}. Skipping row."
                        )
                        continue
                    
                    # Process and validate data
                    processed_record = {
                        'sku': str(record['SKU']).strip(),
                        'description': str(record['Description']).strip(),
                        'on_hand': self._safe_int_convert(record['OnHand'], f"Row {i} OnHand"),
                        'unit': str(record['Unit']).strip(),
                        'lead_time_days': self._safe_int_convert(record['LeadTimeDays'], f"Row {i} LeadTimeDays"),
                        'min_order_qty': self._safe_int_convert(record['MinOrderQty'], f"Row {i} MinOrderQty"),
                        'vendor_ids': [vid.strip() for vid in str(record['VendorIDs']).split(',') if vid.strip()],
                        'auto_order_threshold': self._safe_float_convert(record['AutoOrderThreshold'], f"Row {i} AutoOrderThreshold"),
                        'trust_score': self._safe_float_convert(record['TrustScore'], f"Row {i} TrustScore", 0, 100),
                        'row_number': i
                    }
                    
                    # Skip empty SKUs
                    if not processed_record['sku']:
                        continue
                        
                    processed_records.append(processed_record)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing row {i}: {e}. Skipping row.")
                    continue
            
            self.logger.info(f"Successfully read {len(processed_records)} inventory records")
            return processed_records
            
        except Exception as e:
            self.logger.error(f"Failed to read inventory data: {e}")
            raise
    
    def read_transactions(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Read transaction data from the 'Transactions' worksheet for a date range.
        
        Expected columns:
        - Date: Transaction date (YYYY-MM-DD format)
        - SKU: Product identifier
        - Qty: Quantity (positive for incoming, negative for outgoing)
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of dictionaries containing transaction data
        """
        try:
            # Get the Transactions worksheet
            try:
                worksheet = self.spreadsheet.worksheet("Transactions")
            except gspread.WorksheetNotFound:
                raise ValueError(
                    "Worksheet 'Transactions' not found. Please ensure your spreadsheet "
                    "contains a worksheet named 'Transactions' with the required columns."
                )
            
            # Parse date range
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError as e:
                raise ValueError(f"Invalid date format. Use YYYY-MM-DD format: {e}")
            
            # Get all records
            records = worksheet.get_all_records()
            
            if not records:
                self.logger.warning("No transaction data found in the worksheet")
                return []
            
            # Filter and process records
            processed_records = []
            required_columns = ['Date', 'SKU', 'Qty']
            
            for i, record in enumerate(records, start=2):  # Start at 2 (header is row 1)
                try:
                    # Check for required columns
                    missing_columns = [col for col in required_columns if col not in record]
                    if missing_columns:
                        self.logger.warning(
                            f"Row {i}: Missing columns {missing_columns}. Skipping row."
                        )
                        continue
                    
                    # Parse and validate date
                    date_str = str(record['Date']).strip()
                    if not date_str:
                        continue
                        
                    try:
                        transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        self.logger.warning(f"Row {i}: Invalid date format '{date_str}'. Expected YYYY-MM-DD.")
                        continue
                    
                    # Filter by date range
                    if not (start_dt <= transaction_date <= end_dt):
                        continue
                    
                    # Process record
                    sku = str(record['SKU']).strip()
                    if not sku:
                        continue
                    
                    qty = self._safe_float_convert(record['Qty'], f"Row {i} Qty")
                    if qty is None:
                        continue
                    
                    processed_record = {
                        'date': transaction_date.isoformat(),
                        'sku': sku,
                        'qty': qty,
                        'row_number': i
                    }
                    
                    processed_records.append(processed_record)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing transaction row {i}: {e}. Skipping row.")
                    continue
            
            self.logger.info(
                f"Successfully read {len(processed_records)} transaction records "
                f"between {start_date} and {end_date}"
            )
            return processed_records
            
        except Exception as e:
            self.logger.error(f"Failed to read transaction data: {e}")
            raise
    
    def _safe_int_convert(self, value: Any, field_name: str) -> Optional[int]:
        """Safely convert value to integer."""
        try:
            if value == '' or value is None:
                return 0
            return int(float(str(value)))  # Handle cases like "10.0"
        except (ValueError, TypeError):
            self.logger.warning(f"{field_name}: Could not convert '{value}' to integer. Using 0.")
            return 0
    
    def _safe_float_convert(self, value: Any, field_name: str, min_val: float = None, max_val: float = None) -> Optional[float]:
        """Safely convert value to float with optional range validation."""
        try:
            if value == '' or value is None:
                return 0.0
            
            float_val = float(str(value))
            
            # Range validation
            if min_val is not None and float_val < min_val:
                self.logger.warning(f"{field_name}: Value {float_val} below minimum {min_val}. Using {min_val}.")
                return min_val
            if max_val is not None and float_val > max_val:
                self.logger.warning(f"{field_name}: Value {float_val} above maximum {max_val}. Using {max_val}.")
                return max_val
                
            return float_val
        except (ValueError, TypeError):
            self.logger.warning(f"{field_name}: Could not convert '{value}' to float. Using 0.0.")
            return 0.0


if __name__ == "__main__":
    """
    Test the Google Sheets connector with sample data.
    """
    import sys
    import os
    
    # Add parent directory to path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    from src.utils.config import Config
    
    try:
        # Initialize config and connector
        config = Config()
        connector = SheetsConnector(config)
        
        # Test inventory reading
        print("Testing inventory data reading...")
        inventory_data = connector.read_inventory()
        print(f"Found {len(inventory_data)} inventory items")
        
        if inventory_data:
            print("\nSample inventory item:")
            print(inventory_data[0])
        
        # Test transaction reading (last 30 days)
        print("\nTesting transaction data reading...")
        from datetime import datetime, timedelta
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        transactions = connector.read_transactions(
            start_date.isoformat(), 
            end_date.isoformat()
        )
        print(f"Found {len(transactions)} transactions in the last 30 days")
        
        if transactions:
            print("\nSample transaction:")
            print(transactions[0])
            
    except Exception as e:
        print(f"Error testing connector: {e}")
        sys.exit(1)