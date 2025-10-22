"""
Test module for ReplenishmentPolicy class.
"""

import pytest
import sys
import os
from unittest.mock import Mock

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.policies.replenishment_policy import ReplenishmentPolicy

class TestConfig:
    """Mock configuration for testing."""
    def __init__(self):
        self.inventory_threshold_percentage = 20.0
        self.safety_stock_multiplier = 1.2
        self.default_lead_time_days = 7
        self.holding_cost_rate = 0.25
        self.order_cost = 50.0
        self.service_level = 0.95

@pytest.fixture
def config():
    """Provide test configuration."""
    return TestConfig()

@pytest.fixture
def policy(config):
    """Provide ReplenishmentPolicy instance."""
    return ReplenishmentPolicy(config)

@pytest.fixture
def sample_item():
    """Provide sample inventory item."""
    return {
        'id': 'TEST001',
        'name': 'Test Item',
        'current_stock': 10,
        'minimum_stock': 20,
        'maximum_stock': 100,
        'supplier': 'Test Supplier',
        'supplier_email': 'test@supplier.com',
        'unit_cost': 15.00,
        'status': 'active',
        'priority': 'normal',
        'annual_demand': 1200,
        'average_daily_demand': 3.3,
        'demand_std_deviation': 1.0,
        'lead_time_days': 5
    }

class TestReplenishmentPolicy:
    """Test cases for ReplenishmentPolicy."""
    
    def test_initialization(self, config):
        """Test policy initialization."""
        policy = ReplenishmentPolicy(config)
        assert policy.config == config
        assert policy.threshold_percentage == 0.2
        assert policy.safety_stock_multiplier == 1.2
        assert policy.lead_time_days == 7
    
    def test_identify_low_stock_below_minimum(self, policy):
        """Test identification of items below minimum stock."""
        inventory_data = [
            {
                'id': 'ITEM001',
                'name': 'Low Stock Item',
                'current_stock': 5,
                'minimum_stock': 20,
                'maximum_stock': 100,
                'status': 'active'
            }
        ]
        
        low_stock_items = policy.identify_low_stock(inventory_data)
        assert len(low_stock_items) == 1
        assert low_stock_items[0]['id'] == 'ITEM001'
    
    def test_identify_low_stock_below_threshold(self, policy):
        """Test identification of items below percentage threshold."""
        inventory_data = [
            {
                'id': 'ITEM002',
                'name': 'Threshold Item',
                'current_stock': 15,  # 15% of 100 max stock
                'minimum_stock': 10,
                'maximum_stock': 100,
                'status': 'active'
            }
        ]
        
        low_stock_items = policy.identify_low_stock(inventory_data)
        assert len(low_stock_items) == 1
        assert low_stock_items[0]['id'] == 'ITEM002'
    
    def test_identify_low_stock_adequate_levels(self, policy):
        """Test that adequate stock levels are not flagged."""
        inventory_data = [
            {
                'id': 'ITEM003',
                'name': 'Adequate Stock Item',
                'current_stock': 50,
                'minimum_stock': 20,
                'maximum_stock': 100,
                'status': 'active'
            }
        ]
        
        low_stock_items = policy.identify_low_stock(inventory_data)
        assert len(low_stock_items) == 0
    
    def test_identify_low_stock_inactive_items(self, policy):
        """Test that inactive items are not flagged."""
        inventory_data = [
            {
                'id': 'ITEM004',
                'name': 'Inactive Item',
                'current_stock': 5,
                'minimum_stock': 20,
                'maximum_stock': 100,
                'status': 'inactive'
            }
        ]
        
        low_stock_items = policy.identify_low_stock(inventory_data)
        assert len(low_stock_items) == 0
    
    def test_calculate_order_quantity_basic(self, policy, sample_item):
        """Test basic order quantity calculation."""
        # Item with current stock below minimum
        sample_item['current_stock'] = 10
        sample_item['minimum_stock'] = 20
        sample_item['maximum_stock'] = 100
        
        quantity = policy.calculate_order_quantity(sample_item)
        
        # Should order enough to reach maximum stock
        expected_quantity = 100 - 10  # 90
        assert quantity >= expected_quantity
    
    def test_calculate_order_quantity_with_minimum_order(self, policy, sample_item):
        """Test order quantity with minimum order quantity."""
        sample_item['current_stock'] = 95
        sample_item['minimum_stock'] = 20
        sample_item['maximum_stock'] = 100
        sample_item['minimum_order_quantity'] = 50
        
        quantity = policy.calculate_order_quantity(sample_item)
        
        # Should respect minimum order quantity
        assert quantity >= 50
    
    def test_should_expedite_order_critical_stock(self, policy, sample_item):
        """Test expedite decision for critically low stock."""
        sample_item['current_stock'] = 5  # Below 50% of minimum (20)
        sample_item['minimum_stock'] = 20
        
        should_expedite = policy.should_expedite_order(sample_item)
        assert should_expedite is True
    
    def test_should_expedite_order_critical_item(self, policy, sample_item):
        """Test expedite decision for critical items."""
        sample_item['current_stock'] = 15
        sample_item['minimum_stock'] = 20
        sample_item['is_critical'] = True
        
        should_expedite = policy.should_expedite_order(sample_item)
        assert should_expedite is True
    
    def test_should_expedite_order_high_priority(self, policy, sample_item):
        """Test expedite decision for high priority items."""
        sample_item['current_stock'] = 15
        sample_item['minimum_stock'] = 20
        sample_item['priority'] = 'high'
        
        should_expedite = policy.should_expedite_order(sample_item)
        assert should_expedite is True
    
    def test_should_expedite_order_normal_conditions(self, policy, sample_item):
        """Test expedite decision under normal conditions."""
        sample_item['current_stock'] = 15
        sample_item['minimum_stock'] = 20
        sample_item['priority'] = 'normal'
        sample_item['is_critical'] = False
        
        should_expedite = policy.should_expedite_order(sample_item)
        assert should_expedite is False
    
    def test_get_reorder_recommendations(self, policy):
        """Test comprehensive reorder recommendations."""
        inventory_data = [
            {
                'id': 'ITEM001',
                'name': 'Low Stock Item',
                'current_stock': 5,
                'minimum_stock': 20,
                'maximum_stock': 100,
                'unit_cost': 10.0,
                'status': 'active',
                'priority': 'normal'
            },
            {
                'id': 'ITEM002',
                'name': 'Adequate Stock Item',
                'current_stock': 50,
                'minimum_stock': 20,
                'maximum_stock': 100,
                'unit_cost': 15.0,
                'status': 'active',
                'priority': 'normal'
            }
        ]
        
        recommendations = policy.get_reorder_recommendations(inventory_data)
        
        assert recommendations['total_items_analyzed'] == 2
        assert recommendations['items_needing_reorder'] == 1
        assert len(recommendations['reorder_items']) == 1
        assert recommendations['reorder_items'][0]['item']['id'] == 'ITEM001'
        assert recommendations['total_estimated_cost'] > 0

if __name__ == "__main__":
    pytest.main([__file__])