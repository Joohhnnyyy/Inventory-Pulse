"""
Unit tests for the EOQ optimizer module.

Tests cover:
- EOQ calculation with various scenarios
- Vendor cost calculation and comparison
- Vendor selection optimization
- Edge cases and error handling
"""

import unittest
import math
from src.policies.eoq_optimizer import (
    calculate_eoq,
    calculate_total_cost_for_vendor,
    select_best_vendor,
    compare_vendors
)


class TestEOQOptimizer(unittest.TestCase):
    """Test cases for EOQ optimization functions."""
    
    def setUp(self):
        """Set up test data with known expected outcomes."""
        # Standard test parameters
        self.annual_demand = 1000
        self.order_cost = 50
        self.holding_cost_per_unit = 2.5
        
        # Expected EOQ calculation: sqrt((2 * 1000 * 50) / 2.5) = sqrt(40000) = 200
        self.expected_eoq = 200
        
        # Test vendors with known cost characteristics
        self.vendor_a = {
            'vendor_id': 'V001',
            'vendor_name': 'Supplier A',
            'price_per_unit': 10.0,
            'order_cost': 50.0,
            'lead_time_days': 7,
            'holding_cost_percentage': 0.25  # 25% of unit price
        }
        
        self.vendor_b = {
            'vendor_id': 'V002',
            'vendor_name': 'Supplier B',
            'price_per_unit': 9.5,
            'order_cost': 75.0,
            'lead_time_days': 14,
            'holding_cost_percentage': 0.20  # 20% of unit price
        }
        
        # Additional vendor for comprehensive testing
        self.vendor_c = {
            'vendor_id': 'V003',
            'vendor_name': 'Supplier C',
            'price_per_unit': 11.0,
            'order_cost': 25.0,
            'lead_time_days': 5,
            'holding_cost_percentage': 0.30  # 30% of unit price
        }
        
        self.vendors_list = [self.vendor_a, self.vendor_b, self.vendor_c]

    def test_calculate_eoq_basic(self):
        """Test basic EOQ calculation with known values."""
        eoq = calculate_eoq(self.annual_demand, self.order_cost, self.holding_cost_per_unit)
        self.assertEqual(eoq, self.expected_eoq)

    def test_calculate_eoq_different_values(self):
        """Test EOQ calculation with different parameter values."""
        # Test case: D=2000, S=100, H=5
        # Expected: sqrt((2 * 2000 * 100) / 5) = sqrt(80000) = 282.84... -> 283 (rounded up)
        eoq = calculate_eoq(2000, 100, 5.0)
        expected = math.ceil(math.sqrt((2 * 2000 * 100) / 5.0))
        self.assertEqual(eoq, expected)

    def test_calculate_eoq_edge_cases(self):
        """Test EOQ calculation with edge cases."""
        # Zero demand
        self.assertEqual(calculate_eoq(0, 50, 2.5), 0)
        
        # Zero order cost
        self.assertEqual(calculate_eoq(1000, 0, 2.5), 0)
        
        # Zero holding cost
        self.assertEqual(calculate_eoq(1000, 50, 0), 0)
        
        # Negative values
        self.assertEqual(calculate_eoq(-1000, 50, 2.5), 0)
        self.assertEqual(calculate_eoq(1000, -50, 2.5), 0)
        self.assertEqual(calculate_eoq(1000, 50, -2.5), 0)

    def test_calculate_total_cost_vendor_a(self):
        """Test total cost calculation for Vendor A with known expected result."""
        total_cost = calculate_total_cost_for_vendor(self.annual_demand, self.vendor_a)
        
        # Manual calculation for Vendor A:
        # Price per unit: $10.0
        # Holding cost per unit: $10.0 * 0.25 = $2.5
        # EOQ: sqrt((2 * 1000 * 50) / 2.5) = 200
        # Purchase cost: 1000 * $10.0 = $10,000
        # Ordering cost: (1000 / 200) * $50 = $250
        # Holding cost: (200 / 2) * $2.5 = $250
        # Total: $10,000 + $250 + $250 = $10,500
        
        expected_total = 10500.0
        self.assertAlmostEqual(total_cost, expected_total, places=2)

    def test_calculate_total_cost_vendor_b(self):
        """Test total cost calculation for Vendor B with known expected result."""
        total_cost = calculate_total_cost_for_vendor(self.annual_demand, self.vendor_b)
        
        # Manual calculation for Vendor B:
        # Price per unit: $9.5
        # Holding cost per unit: $9.5 * 0.20 = $1.9
        # EOQ: sqrt((2 * 1000 * 75) / 1.9) = sqrt(78947.37) = 280.98... -> 281
        # Purchase cost: 1000 * $9.5 = $9,500
        # Ordering cost: (1000 / 281) * $75 = $266.90
        # Holding cost: (281 / 2) * $1.9 = $266.95
        # Total: $9,500 + $266.90 + $266.95 = $10,033.85
        
        # Calculate expected values
        holding_cost_per_unit = 9.5 * 0.20
        eoq = math.ceil(math.sqrt((2 * 1000 * 75) / holding_cost_per_unit))
        purchase_cost = 1000 * 9.5
        ordering_cost = (1000 / eoq) * 75
        holding_cost = (eoq / 2) * holding_cost_per_unit
        expected_total = purchase_cost + ordering_cost + holding_cost
        
        self.assertAlmostEqual(total_cost, expected_total, places=2)

    def test_calculate_total_cost_invalid_vendor(self):
        """Test total cost calculation with invalid vendor data."""
        # Missing required fields
        invalid_vendor = {'vendor_id': 'INVALID'}
        cost = calculate_total_cost_for_vendor(self.annual_demand, invalid_vendor)
        self.assertEqual(cost, float('inf'))
        
        # Negative price
        invalid_vendor = {
            'price_per_unit': -10.0,
            'order_cost': 50.0
        }
        cost = calculate_total_cost_for_vendor(self.annual_demand, invalid_vendor)
        self.assertEqual(cost, float('inf'))
        
        # Zero demand
        cost = calculate_total_cost_for_vendor(0, self.vendor_a)
        self.assertEqual(cost, float('inf'))

    def test_select_best_vendor_known_outcome(self):
        """Test vendor selection with known expected outcome."""
        # Based on our calculations:
        # Vendor A: ~$10,500
        # Vendor B: ~$10,034
        # Vendor C: will be calculated
        
        best_vendor = select_best_vendor(self.vendors_list, self.annual_demand)
        
        # Vendor B should be the best (lowest total cost)
        self.assertIsNotNone(best_vendor)
        self.assertEqual(best_vendor['vendor_id'], 'V002')
        self.assertEqual(best_vendor['vendor_name'], 'Supplier B')
        
        # Check that EOQ and cost information is included
        self.assertIn('eoq', best_vendor)
        self.assertIn('total_annual_cost', best_vendor)
        self.assertIn('cost_breakdown', best_vendor)
        
        # Validate cost breakdown structure
        breakdown = best_vendor['cost_breakdown']
        self.assertIn('purchase_cost', breakdown)
        self.assertIn('ordering_cost', breakdown)
        self.assertIn('holding_cost', breakdown)
        
        # Verify total cost matches breakdown sum
        total_from_breakdown = (breakdown['purchase_cost'] + 
                              breakdown['ordering_cost'] + 
                              breakdown['holding_cost'])
        self.assertAlmostEqual(best_vendor['total_annual_cost'], total_from_breakdown, places=2)

    def test_select_best_vendor_two_vendors_only(self):
        """Test vendor selection with only two vendors (A and B)."""
        two_vendors = [self.vendor_a, self.vendor_b]
        best_vendor = select_best_vendor(two_vendors, self.annual_demand)
        
        # Vendor B should still be better than Vendor A
        self.assertEqual(best_vendor['vendor_id'], 'V002')
        
        # Verify the EOQ is reasonable
        self.assertGreater(best_vendor['eoq'], 0)
        self.assertLess(best_vendor['eoq'], 1000)  # Should be reasonable for our demand

    def test_select_best_vendor_edge_cases(self):
        """Test vendor selection with edge cases."""
        # Empty vendor list
        result = select_best_vendor([], self.annual_demand)
        self.assertIsNone(result)
        
        # Zero demand
        result = select_best_vendor(self.vendors_list, 0)
        self.assertIsNone(result)
        
        # Invalid vendor data
        invalid_vendors = [
            {'vendor_id': 'INVALID1'},  # Missing required fields
            {'price_per_unit': -1, 'order_cost': 50}  # Invalid values
        ]
        result = select_best_vendor(invalid_vendors, self.annual_demand)
        self.assertIsNone(result)

    def test_compare_vendors_sorting(self):
        """Test that vendor comparison returns vendors sorted by cost."""
        comparison = compare_vendors(self.vendors_list, self.annual_demand)
        
        # Should return all valid vendors
        self.assertEqual(len(comparison), 3)
        
        # Should be sorted by total cost (ascending)
        for i in range(len(comparison) - 1):
            self.assertLessEqual(
                comparison[i]['total_annual_cost'],
                comparison[i + 1]['total_annual_cost']
            )
        
        # First vendor should be the same as select_best_vendor result
        best_vendor = select_best_vendor(self.vendors_list, self.annual_demand)
        self.assertEqual(comparison[0]['vendor_id'], best_vendor['vendor_id'])

    def test_compare_vendors_augmented_data(self):
        """Test that vendor comparison includes all augmented data."""
        comparison = compare_vendors(self.vendors_list, self.annual_demand)
        
        for vendor in comparison:
            # Check original vendor data is preserved
            self.assertIn('vendor_id', vendor)
            self.assertIn('vendor_name', vendor)
            self.assertIn('price_per_unit', vendor)
            self.assertIn('order_cost', vendor)
            
            # Check augmented data is added
            self.assertIn('eoq', vendor)
            self.assertIn('total_annual_cost', vendor)
            self.assertIn('cost_breakdown', vendor)
            
            # Validate EOQ is positive
            self.assertGreater(vendor['eoq'], 0)
            
            # Validate cost breakdown
            breakdown = vendor['cost_breakdown']
            total_calculated = (breakdown['purchase_cost'] + 
                              breakdown['ordering_cost'] + 
                              breakdown['holding_cost'])
            self.assertAlmostEqual(vendor['total_annual_cost'], total_calculated, places=2)

    def test_realistic_scenario_high_demand(self):
        """Test with realistic high-demand scenario."""
        high_demand = 10000  # 10,000 units per year
        
        best_vendor = select_best_vendor(self.vendors_list, high_demand)
        self.assertIsNotNone(best_vendor)
        
        # EOQ should scale appropriately with higher demand
        self.assertGreater(best_vendor['eoq'], self.expected_eoq)
        
        # Total cost should be significantly higher but proportional
        self.assertGreater(best_vendor['total_annual_cost'], 50000)  # Should be substantial

    def test_realistic_scenario_low_demand(self):
        """Test with realistic low-demand scenario."""
        low_demand = 100  # 100 units per year
        
        best_vendor = select_best_vendor(self.vendors_list, low_demand)
        self.assertIsNotNone(best_vendor)
        
        # EOQ should be smaller with lower demand
        self.assertLess(best_vendor['eoq'], self.expected_eoq)
        
        # Total cost should be lower but may have different vendor preference
        self.assertLess(best_vendor['total_annual_cost'], 5000)

    def test_vendor_cost_components_validation(self):
        """Test that cost components are calculated correctly."""
        vendor = self.vendor_a
        total_cost = calculate_total_cost_for_vendor(self.annual_demand, vendor)
        
        # Calculate components manually
        price_per_unit = vendor['price_per_unit']
        order_cost = vendor['order_cost']
        holding_cost_percentage = vendor['holding_cost_percentage']
        holding_cost_per_unit = price_per_unit * holding_cost_percentage
        
        eoq = calculate_eoq(self.annual_demand, order_cost, holding_cost_per_unit)
        
        purchase_cost = self.annual_demand * price_per_unit
        ordering_cost = (self.annual_demand / eoq) * order_cost
        holding_cost = (eoq / 2) * holding_cost_per_unit
        
        expected_total = purchase_cost + ordering_cost + holding_cost
        
        self.assertAlmostEqual(total_cost, expected_total, places=2)

    def test_holding_cost_percentage_variations(self):
        """Test vendors with different holding cost percentages."""
        # Create vendors with same price but different holding costs
        vendor_low_holding = {
            'vendor_id': 'LOW_H',
            'vendor_name': 'Low Holding Cost',
            'price_per_unit': 10.0,
            'order_cost': 50.0,
            'holding_cost_percentage': 0.10  # 10%
        }
        
        vendor_high_holding = {
            'vendor_id': 'HIGH_H',
            'vendor_name': 'High Holding Cost',
            'price_per_unit': 10.0,
            'order_cost': 50.0,
            'holding_cost_percentage': 0.40  # 40%
        }
        
        cost_low = calculate_total_cost_for_vendor(self.annual_demand, vendor_low_holding)
        cost_high = calculate_total_cost_for_vendor(self.annual_demand, vendor_high_holding)
        
        # Lower holding cost should result in lower total cost
        self.assertLess(cost_low, cost_high)


class TestEOQFormula(unittest.TestCase):
    """Specific tests for EOQ formula accuracy."""
    
    def test_eoq_formula_textbook_example(self):
        """Test EOQ calculation against textbook example."""
        # Classic textbook example
        annual_demand = 1200
        order_cost = 100
        holding_cost_per_unit = 3.0
        
        # Expected: sqrt((2 * 1200 * 100) / 3) = sqrt(80000) = 282.84... -> 283
        expected = math.ceil(math.sqrt((2 * 1200 * 100) / 3.0))
        actual = calculate_eoq(annual_demand, order_cost, holding_cost_per_unit)
        
        self.assertEqual(actual, expected)

    def test_eoq_formula_precision(self):
        """Test EOQ calculation precision with various inputs."""
        test_cases = [
            (1000, 50, 2.5, 200),  # Perfect square root
            (500, 25, 1.25, 200),  # Same ratio, different scale
            (2000, 100, 5.0, 200), # Same ratio, larger scale
        ]
        
        for demand, order_cost, holding_cost, expected in test_cases:
            with self.subTest(demand=demand, order_cost=order_cost, holding_cost=holding_cost):
                actual = calculate_eoq(demand, order_cost, holding_cost)
                self.assertEqual(actual, expected)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)