#!/usr/bin/env python3
"""
Populate Google Sheets with Dummy Inventory Data - Simplified Version

This script adds sample inventory data to the specified Google Sheets spreadsheet
without using the Config class to avoid validation issues.
"""

import os
from datetime import datetime, timedelta
import random

try:
    import gspread
    from google.oauth2.service_account import Credentials
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure you have installed all requirements: pip install -r requirements.txt")
    exit(1)

# Load environment variables
load_dotenv()

# Get configuration from environment
CREDENTIALS_PATH = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON', './credentials/inventory-intelligence-tool-fea822c40c58.json')
SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', '1Hjo8J3sw1v53aWjDSX0bdRIvfcG50cYW9V9E21-m8gs')

# Dummy inventory data
DUMMY_INVENTORY_DATA = [
    {
        'SKU': 'OFFICE-001',
        'Description': 'A4 Copy Paper - 500 sheets',
        'OnHand': 45,
        'Unit': 'ream',
        'LeadTimeDays': 3,
        'MinOrderQty': 20,
        'VendorIDs': 'VENDOR-001, VENDOR-002',
        'AutoOrderThreshold': 500.00,
        'TrustScore': 95
    },
    {
        'SKU': 'OFFICE-002', 
        'Description': 'Black Ink Cartridge HP 305XL',
        'OnHand': 8,
        'Unit': 'piece',
        'LeadTimeDays': 5,
        'MinOrderQty': 5,
        'VendorIDs': 'VENDOR-003',
        'AutoOrderThreshold': 300.00,
        'TrustScore': 88
    },
    {
        'SKU': 'OFFICE-003',
        'Description': 'Ballpoint Pens Blue - Pack of 10',
        'OnHand': 25,
        'Unit': 'pack',
        'LeadTimeDays': 2,
        'MinOrderQty': 10,
        'VendorIDs': 'VENDOR-001',
        'AutoOrderThreshold': 150.00,
        'TrustScore': 92
    },
    {
        'SKU': 'CLEAN-001',
        'Description': 'Multi-Surface Cleaner 500ml',
        'OnHand': 12,
        'Unit': 'bottle',
        'LeadTimeDays': 7,
        'MinOrderQty': 12,
        'VendorIDs': 'VENDOR-004, VENDOR-005',
        'AutoOrderThreshold': 200.00,
        'TrustScore': 85
    },
    {
        'SKU': 'CLEAN-002',
        'Description': 'Paper Towels - 6 Roll Pack',
        'OnHand': 18,
        'Unit': 'pack',
        'LeadTimeDays': 4,
        'MinOrderQty': 8,
        'VendorIDs': 'VENDOR-004',
        'AutoOrderThreshold': 120.00,
        'TrustScore': 90
    },
    {
        'SKU': 'TECH-001',
        'Description': 'USB-C Cable 2m',
        'OnHand': 6,
        'Unit': 'piece',
        'LeadTimeDays': 10,
        'MinOrderQty': 5,
        'VendorIDs': 'VENDOR-006',
        'AutoOrderThreshold': 250.00,
        'TrustScore': 78
    },
    {
        'SKU': 'TECH-002',
        'Description': 'Wireless Mouse Optical',
        'OnHand': 4,
        'Unit': 'piece',
        'LeadTimeDays': 8,
        'MinOrderQty': 3,
        'VendorIDs': 'VENDOR-006, VENDOR-007',
        'AutoOrderThreshold': 180.00,
        'TrustScore': 82
    },
    {
        'SKU': 'BREAK-001',
        'Description': 'Coffee Beans 1kg Premium Blend',
        'OnHand': 22,
        'Unit': 'kg',
        'LeadTimeDays': 5,
        'MinOrderQty': 10,
        'VendorIDs': 'VENDOR-008',
        'AutoOrderThreshold': 400.00,
        'TrustScore': 96
    },
    {
        'SKU': 'BREAK-002',
        'Description': 'Tea Bags Earl Grey - Box of 100',
        'OnHand': 15,
        'Unit': 'box',
        'LeadTimeDays': 6,
        'MinOrderQty': 6,
        'VendorIDs': 'VENDOR-008, VENDOR-009',
        'AutoOrderThreshold': 80.00,
        'TrustScore': 89
    },
    {
        'SKU': 'SAFETY-001',
        'Description': 'First Aid Kit Standard',
        'OnHand': 3,
        'Unit': 'kit',
        'LeadTimeDays': 14,
        'MinOrderQty': 2,
        'VendorIDs': 'VENDOR-010',
        'AutoOrderThreshold': 150.00,
        'TrustScore': 94
    }
]

# Sample transaction data for the last 30 days
def generate_transaction_data():
    """Generate sample transaction data for the last 30 days."""
    transactions = []
    skus = [item['SKU'] for item in DUMMY_INVENTORY_DATA]
    
    # Generate 50 random transactions over the last 30 days
    for i in range(50):
        # Random date in the last 30 days
        days_ago = random.randint(0, 30)
        transaction_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        # Random SKU and quantity
        sku = random.choice(skus)
        quantity = random.randint(1, 10)
        transaction_type = random.choice(['OUT', 'IN', 'ADJUSTMENT'])
        
        transactions.append({
            'Date': transaction_date,
            'SKU': sku,
            'Type': transaction_type,
            'Quantity': quantity if transaction_type == 'IN' else -quantity,
            'Reference': f'TXN-{i+1:04d}',
            'Notes': f'Sample {transaction_type.lower()} transaction'
        })
    
    # Sort by date
    transactions.sort(key=lambda x: x['Date'])
    return transactions

class SheetsPopulator:
    """Populates Google Sheets with dummy data."""
    
    def __init__(self):
        """Initialize the sheets populator."""
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
            
            # Check credentials file
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(f"Credentials file not found: {CREDENTIALS_PATH}")
            
            # Load credentials
            credentials = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scope)
            self.client = gspread.authorize(credentials)
            
            # Open the spreadsheet
            self.spreadsheet = self.client.open_by_key(SPREADSHEET_ID)
            print(f"✅ Connected to Google Sheets: {self.spreadsheet.title}")
            
        except Exception as e:
            print(f"❌ Failed to initialize Google Sheets client: {e}")
            raise
    
    def create_inventory_worksheet(self):
        """Create or update the Inventory worksheet with dummy data."""
        try:
            # Try to get existing worksheet or create new one
            try:
                worksheet = self.spreadsheet.worksheet("Inventory")
                print("📋 Found existing 'Inventory' worksheet")
                # Clear existing data
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(title="Inventory", rows=100, cols=10)
                print("📋 Created new 'Inventory' worksheet")
            
            # Prepare headers
            headers = ['SKU', 'Description', 'OnHand', 'Unit', 'LeadTimeDays', 
                      'MinOrderQty', 'VendorIDs', 'AutoOrderThreshold', 'TrustScore']
            
            # Prepare data rows
            data_rows = []
            for item in DUMMY_INVENTORY_DATA:
                row = [item[header] for header in headers]
                data_rows.append(row)
            
            # Write headers and data
            all_data = [headers] + data_rows
            worksheet.update('A1', all_data)
            
            print(f"✅ Added {len(DUMMY_INVENTORY_DATA)} inventory items to 'Inventory' worksheet")
            return True
            
        except Exception as e:
            print(f"❌ Error creating inventory worksheet: {e}")
            return False
    
    def create_transactions_worksheet(self):
        """Create or update the Transactions worksheet with dummy data."""
        try:
            # Generate transaction data
            transactions = generate_transaction_data()
            
            # Try to get existing worksheet or create new one
            try:
                worksheet = self.spreadsheet.worksheet("Transactions")
                print("📋 Found existing 'Transactions' worksheet")
                # Clear existing data
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(title="Transactions", rows=100, cols=10)
                print("📋 Created new 'Transactions' worksheet")
            
            # Prepare headers
            headers = ['Date', 'SKU', 'Type', 'Quantity', 'Reference', 'Notes']
            
            # Prepare data rows
            data_rows = []
            for txn in transactions:
                row = [txn[header] for header in headers]
                data_rows.append(row)
            
            # Write headers and data
            all_data = [headers] + data_rows
            worksheet.update('A1', all_data)
            
            print(f"✅ Added {len(transactions)} transactions to 'Transactions' worksheet")
            return True
            
        except Exception as e:
            print(f"❌ Error creating transactions worksheet: {e}")
            return False
    
    def populate_sheets(self):
        """Populate the Google Sheets with all dummy data."""
        print("🚀 Starting to populate Google Sheets with dummy data...")
        print(f"📊 Spreadsheet URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        
        success = True
        
        # Create inventory data
        if not self.create_inventory_worksheet():
            success = False
        
        # Create transaction data
        if not self.create_transactions_worksheet():
            success = False
        
        if success:
            print("\n🎉 Successfully populated Google Sheets with dummy data!")
            print(f"🔗 View your spreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
            print("\n📋 Data Summary:")
            print(f"   • {len(DUMMY_INVENTORY_DATA)} inventory items")
            print(f"   • 50 sample transactions")
            print("   • Ready for inventory management testing!")
        else:
            print("\n❌ Some errors occurred while populating the sheets")
        
        return success

def main():
    """Main function to run the sheets population."""
    try:
        print(f"📁 Using credentials: {CREDENTIALS_PATH}")
        print(f"📊 Target spreadsheet ID: {SPREADSHEET_ID}")
        
        populator = SheetsPopulator()
        success = populator.populate_sheets()
        
        if success:
            print("\n✨ Your Google Sheets is now ready for testing the inventory system!")
        else:
            print("\n⚠️  Please check the errors above and try again.")
            exit(1)
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main()