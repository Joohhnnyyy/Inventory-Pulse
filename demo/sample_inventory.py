"""
Sample Inventory Demo

This script demonstrates how to set up and run the Inventory Replenishment Copilot
with sample data.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.agent_main import InventoryAgent
from src.utils.config import Config
from src.utils.logger import setup_logger

# Sample inventory data
SAMPLE_INVENTORY = [
    {
        'id': 'ITEM001',
        'name': 'Office Paper A4',
        'current_stock': 15,
        'minimum_stock': 50,
        'maximum_stock': 200,
        'supplier': 'Office Supplies Co.',
        'supplier_email': 'orders@officesupplies.com',
        'unit_cost': 5.99,
        'status': 'active',
        'priority': 'normal',
        'annual_demand': 2400,
        'average_daily_demand': 6.6,
        'demand_std_deviation': 2.1,
        'lead_time_days': 5
    },
    {
        'id': 'ITEM002', 
        'name': 'Printer Ink Cartridge',
        'current_stock': 3,
        'minimum_stock': 10,
        'maximum_stock': 50,
        'supplier': 'Tech Supplies Ltd.',
        'supplier_email': 'sales@techsupplies.com',
        'unit_cost': 29.99,
        'status': 'active',
        'priority': 'high',
        'annual_demand': 120,
        'average_daily_demand': 0.33,
        'demand_std_deviation': 0.15,
        'lead_time_days': 3,
        'is_critical': True
    },
    {
        'id': 'ITEM003',
        'name': 'Cleaning Supplies',
        'current_stock': 25,
        'minimum_stock': 20,
        'maximum_stock': 100,
        'supplier': 'Clean Pro Services',
        'supplier_email': 'orders@cleanpro.com',
        'unit_cost': 12.50,
        'status': 'active',
        'priority': 'normal',
        'annual_demand': 480,
        'average_daily_demand': 1.3,
        'demand_std_deviation': 0.4,
        'lead_time_days': 7
    }
]

class MockSheetsConnector:
    """Mock Google Sheets connector for demo purposes."""
    
    def __init__(self, config):
        self.config = config
        self.inventory_data = SAMPLE_INVENTORY.copy()
        self.logger = setup_logger(__name__)
    
    async def get_inventory_data(self):
        """Return sample inventory data."""
        self.logger.info("Fetching sample inventory data...")
        return self.inventory_data
    
    async def update_item_status(self, item_id: str, status: str):
        """Update item status in mock data."""
        for item in self.inventory_data:
            if item['id'] == item_id:
                item['status'] = status
                self.logger.info(f"Updated {item_id} status to {status}")
                return True
        return False

class MockNotionConnector:
    """Mock Notion connector for demo purposes."""
    
    def __init__(self, config):
        self.config = config
        self.records = []
        self.logger = setup_logger(__name__)
    
    async def create_replenishment_record(self, order_details):
        """Create mock replenishment record."""
        record_id = f"notion_record_{len(self.records) + 1}"
        self.records.append({
            'id': record_id,
            'order_details': order_details,
            'created_at': datetime.now()
        })
        
        item_name = order_details['item'].get('name', 'Unknown')
        self.logger.info(f"Created Notion record for {item_name}")
        return record_id

class MockEmailConnector:
    """Mock email connector for demo purposes."""
    
    def __init__(self, config):
        self.config = config
        self.sent_emails = []
        self.logger = setup_logger(__name__)
    
    async def send_replenishment_request(self, order_details):
        """Mock sending replenishment request email."""
        item = order_details['item']
        email_record = {
            'to': item.get('supplier_email', 'unknown@supplier.com'),
            'subject': f"Replenishment Request - {item.get('name', 'Unknown')}",
            'item_id': item.get('id'),
            'quantity': order_details.get('quantity'),
            'sent_at': datetime.now()
        }
        
        self.sent_emails.append(email_record)
        self.logger.info(f"Sent replenishment request email for {item.get('name', 'Unknown')}")
        return True

class DemoInventoryAgent(InventoryAgent):
    """Demo version of InventoryAgent with mock connectors."""
    
    def __init__(self, config=None):
        """Initialize demo agent with mock connectors."""
        self.config = config or self._create_demo_config()
        self.logger = setup_logger(__name__)
        
        # Use mock connectors instead of real ones
        self.sheets_connector = MockSheetsConnector(self.config)
        self.notion_connector = MockNotionConnector(self.config)
        self.email_connector = MockEmailConnector(self.config)
        
        # Initialize policies (these work with mock data)
        from src.policies.replenishment_policy import ReplenishmentPolicy
        self.replenishment_policy = ReplenishmentPolicy(self.config)
        
        self.logger.info("Demo Inventory Agent initialized with mock connectors")
    
    def _create_demo_config(self):
        """Create demo configuration."""
        class DemoConfig:
            def __init__(self):
                self.check_interval = 10  # 10 seconds for demo
                self.inventory_threshold_percentage = 20.0
                self.max_retry_attempts = 3
                self.safety_stock_multiplier = 1.2
                self.default_lead_time_days = 7
                self.holding_cost_rate = 0.25
                self.order_cost = 50.0
                self.service_level = 0.95
                self.company_name = "Demo Company"
        
        return DemoConfig()
    
    async def run_demo(self):
        """Run a single demo cycle instead of continuous loop."""
        self.logger.info("Starting Inventory Replenishment Demo")
        
        try:
            # Check inventory once
            await self.check_inventory()
            
            # Show results
            await self._show_demo_results()
            
        except Exception as e:
            self.logger.error(f"Demo error: {str(e)}")
            raise
    
    async def _show_demo_results(self):
        """Display demo results."""
        print("\n" + "="*60)
        print("DEMO RESULTS SUMMARY")
        print("="*60)
        
        # Show inventory analysis
        inventory_data = await self.sheets_connector.get_inventory_data()
        recommendations = self.replenishment_policy.get_reorder_recommendations(inventory_data)
        
        print(f"\nInventory Analysis:")
        print(f"- Total items analyzed: {recommendations['total_items_analyzed']}")
        print(f"- Items needing reorder: {recommendations['items_needing_reorder']}")
        print(f"- Total estimated cost: ${recommendations['total_estimated_cost']:.2f}")
        
        if recommendations['reorder_items']:
            print(f"\nReorder Recommendations:")
            for item_rec in recommendations['reorder_items']:
                item = item_rec['item']
                print(f"- {item['name']} (ID: {item['id']})")
                print(f"  Current Stock: {item['current_stock']}")
                print(f"  Minimum Stock: {item['minimum_stock']}")
                print(f"  Recommended Order: {item_rec['recommended_quantity']}")
                print(f"  Estimated Cost: ${item_rec['estimated_cost']:.2f}")
                print(f"  Priority: {item_rec['priority']}")
                if item_rec['is_expedited']:
                    print(f"  ⚠️  EXPEDITED ORDER REQUIRED")
                print()
        
        # Show Notion records
        print(f"Notion Records Created: {len(self.notion_connector.records)}")
        for record in self.notion_connector.records:
            item_name = record['order_details']['item']['name']
            print(f"- Record for {item_name} (ID: {record['id']})")
        
        # Show emails sent
        print(f"\nEmails Sent: {len(self.email_connector.sent_emails)}")
        for email in self.email_connector.sent_emails:
            print(f"- To: {email['to']}")
            print(f"  Subject: {email['subject']}")
            print(f"  Quantity: {email['quantity']}")
        
        print("\n" + "="*60)
        print("Demo completed successfully!")
        print("="*60)

async def main():
    """Run the demo."""
    print("Inventory Replenishment Copilot - Demo Mode")
    print("=" * 50)
    
    # Create and run demo agent
    demo_agent = DemoInventoryAgent()
    await demo_agent.run_demo()

if __name__ == "__main__":
    asyncio.run(main())