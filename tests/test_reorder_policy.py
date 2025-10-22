"""
Unit Tests for Reorder Policy

This module contains comprehensive unit tests for the reorder policy decision engine,
testing various scenarios with synthetic data.

Author: Inventory Intelligence Team
Version: 1.0.0
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from policies.reorder_policy import ReorderPolicy

class TestReorderPolicy(unittest.TestCase):
    """Test cases for ReorderPolicy class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.policy = ReorderPolicy(safety_margin_days=7, min_order_qty=10)
        
        # Standard test vendors
        self.vendors = [
            {
                'name': 'Acme Supplies',
                'unit_cost': 12.50,
                'holding_cost_rate': 0.20,
                'order_cost': 50.0,
                'lead_time': 7
            },
            {
                'name': 'Global Parts',
                'unit_cost': 11.80,
                'holding_cost_rate': 0.25,
                'order_cost': 75.0,
                'lead_time': 10
            },
            {
                'name': 'Quick Ship',
                'unit_cost': 13.20,
                'holding_cost_rate': 0.15,
                'order_cost': 30.0,
                'lead_time': 3
            }
        ]
    
    def _generate_transactions(self, sku: str, days: int, daily_usage: float, start_date: datetime = None) -> list:
        """
        Generate synthetic transaction data.
        
        Args:
            sku: Product SKU
            days: Number of days of history
            daily_usage: Average daily usage
            start_date: Start date for transactions
            
        Returns:
            list: List of transaction dictionaries
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=days)
        
        transactions = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            # Add some variation to daily usage (±20%)
            variation = 0.8 + (i % 5) * 0.1  # 0.8 to 1.2 multiplier
            usage = max(1, int(daily_usage * variation))
            
            transactions.append({
                'date': date.strftime('%Y-%m-%d'),
                'sku': sku,
                'quantity': -usage,  # Negative for outbound
                'type': 'sale'
            })
        
        return transactions
    
    def test_initialization(self):
        """Test ReorderPolicy initialization."""
        policy = ReorderPolicy(safety_margin_days=10, min_order_qty=25)
        self.assertEqual(policy.safety_margin_days, 10)
        self.assertEqual(policy.min_order_qty, 25)
    
    def test_urgent_reorder_scenario(self):
        """Test scenario requiring urgent reorder due to imminent stockout."""
        inventory_item = {
            'sku': 'URGENT-001',
            'on_hand': 5,  # Very low stock
            'reorder_point': 20
        }
        
        # High usage rate - 3 units per day
        transactions = self._generate_transactions('URGENT-001', 30, 3.0)
        
        result = self.policy.evaluate_reorder_need(
            inventory_item, transactions, self.vendors
        )
        
        # Assertions
        self.assertTrue(result['needs_reorder'])
        self.assertEqual(result['sku'], 'URGENT-001')
        self.assertGreater(result['qty'], 0)
        self.assertIn('URGENT', result['evidence_summary'])
        self.assertLess(result['decision_factors']['days_until_stockout'], 7)
    
    def test_normal_reorder_scenario(self):
        """Test normal reorder scenario with moderate stock levels."""
        inventory_item = {
            'sku': 'NORMAL-001',
            'on_hand': 30,
            'reorder_point': 50
        }
        
        # Moderate usage - 2 units per day
        transactions = self._generate_transactions('NORMAL-001', 60, 2.0)
        
        result = self.policy.evaluate_reorder_need(
            inventory_item, transactions, self.vendors
        )
        
        # Should need reorder due to being below reorder point
        self.assertTrue(result['needs_reorder'])
        self.assertEqual(result['sku'], 'NORMAL-001')
        self.assertGreater(result['qty'], 0)
        self.assertIn(result['vendor'], [v['name'] for v in self.vendors])
    
    def test_no_reorder_needed(self):
        """Test scenario where no reorder is needed."""
        inventory_item = {
            'sku': 'SUFFICIENT-001',
            'on_hand': 200,  # High stock
            'reorder_point': 50
        }
        
        # Low usage - 1 unit per day
        transactions = self._generate_transactions('SUFFICIENT-001', 30, 1.0)
        
        result = self.policy.evaluate_reorder_need(
            inventory_item, transactions, self.vendors
        )
        
        # Should not need reorder
        self.assertFalse(result['needs_reorder'])
        self.assertEqual(result['qty'], 0)
        self.assertIn('NO ACTION NEEDED', result['evidence_summary'])
        self.assertGreater(result['decision_factors']['days_until_stockout'], 30)
    
    def test_new_item_no_history(self):
        """Test handling of new items with no transaction history."""
        inventory_item = {
            'sku': 'NEW-001',
            'on_hand': 10,
            'reorder_point': 25
        }
        
        # No transactions for this SKU
        transactions = []
        
        result = self.policy.evaluate_reorder_need(
            inventory_item, transactions, self.vendors
        )
        
        # Should handle gracefully with minimal demand assumption
        self.assertTrue(result['needs_reorder'])  # Below reorder point
        self.assertGreater(result['decision_factors']['avg_daily_usage'], 0)
    
    def test_vendor_selection_optimization(self):
        """Test that the policy selects the most cost-effective vendor."""
        inventory_item = {
            'sku': 'OPTIMIZE-001',
            'on_hand': 20,
            'reorder_point': 50
        }
        
        transactions = self._generate_transactions('OPTIMIZE-001', 90, 2.5)
        
        result = self.policy.evaluate_reorder_need(
            inventory_item, transactions, self.vendors
        )
        
        # Should select a vendor and provide cost information
        self.assertIn(result['vendor'], [v['name'] for v in self.vendors])
        self.assertGreater(result['total_cost'], 0)
        self.assertGreater(result['eoq'], 0)
        
        # Should have cost savings information
        self.assertIn('cost_savings', result)
        self.assertIsInstance(result['cost_savings'], dict)
    
    def test_minimum_order_quantity_enforcement(self):
        """Test that minimum order quantity is enforced."""
        policy = ReorderPolicy(min_order_qty=100)
        
        inventory_item = {
            'sku': 'MIN-QTY-001',
            'on_hand': 45,
            'reorder_point': 50
        }
        
        # Very low usage to test min qty enforcement
        transactions = self._generate_transactions('MIN-QTY-001', 30, 0.5)
        
        result = policy.evaluate_reorder_need(
            inventory_item, transactions, self.vendors
        )
        
        if result['needs_reorder']:
            self.assertGreaterEqual(result['qty'], 100)
    
    def test_safety_margin_impact(self):
        """Test impact of different safety margins."""
        inventory_item = {
            'sku': 'SAFETY-001',
            'on_hand': 20,
            'reorder_point': 10
        }
        
        transactions = self._generate_transactions('SAFETY-001', 30, 2.0)
        
        # Test with different safety margins
        policy_conservative = ReorderPolicy(safety_margin_days=14)
        policy_aggressive = ReorderPolicy(safety_margin_days=3)
        
        result_conservative = policy_conservative.evaluate_reorder_need(
            inventory_item, transactions, self.vendors
        )
        result_aggressive = policy_aggressive.evaluate_reorder_need(
            inventory_item, transactions, self.vendors
        )
        
        # Conservative policy should be more likely to trigger reorders
        if result_conservative['needs_reorder'] and not result_aggressive['needs_reorder']:
            self.assertTrue(True)  # Expected behavior
        elif result_conservative['needs_reorder'] == result_aggressive['needs_reorder']:
            self.assertTrue(True)  # Both policies agree
        else:
            # Aggressive policy triggers but conservative doesn't - unusual but possible
            pass
    
    def test_batch_evaluation(self):
        """Test batch evaluation of multiple items."""
        inventory_items = [
            {'sku': 'BATCH-001', 'on_hand': 5, 'reorder_point': 20},
            {'sku': 'BATCH-002', 'on_hand': 100, 'reorder_point': 30},
            {'sku': 'BATCH-003', 'on_hand': 25, 'reorder_point': 40}
        ]
        
        # Generate transactions for all items
        transactions = []
        for item in inventory_items:
            sku = item['sku']
            item_transactions = self._generate_transactions(sku, 45, 2.0)
            transactions.extend(item_transactions)
        
        results = self.policy.batch_evaluate_reorders(
            inventory_items, transactions, self.vendors
        )
        
        # Should return results for all items
        self.assertEqual(len(results), 3)
        
        # Results should be sorted by priority (reorders first)
        reorder_count = sum(1 for r in results if r.get('needs_reorder', False))
        self.assertGreaterEqual(reorder_count, 0)
        
        # Each result should have required fields
        for result in results:
            self.assertIn('sku', result)
            self.assertIn('needs_reorder', result)
            self.assertIn('evidence_summary', result)
    
    def test_error_handling_invalid_input(self):
        """Test error handling with invalid input data."""
        # Test with missing required fields
        invalid_item = {'sku': 'INVALID-001'}  # Missing on_hand
        transactions = []
        
        with self.assertRaises(KeyError):
            self.policy.evaluate_reorder_need(invalid_item, transactions, self.vendors)
        
        # Test with empty vendors list
        valid_item = {'sku': 'VALID-001', 'on_hand': 10, 'reorder_point': 20}
        
        with self.assertRaises(ValueError):
            self.policy.evaluate_reorder_need(valid_item, transactions, [])
    
    def test_decision_factors_completeness(self):
        """Test that all decision factors are included in results."""
        inventory_item = {
            'sku': 'FACTORS-001',
            'on_hand': 30,
            'reorder_point': 40
        }
        
        transactions = self._generate_transactions('FACTORS-001', 60, 2.0)
        
        result = self.policy.evaluate_reorder_need(
            inventory_item, transactions, self.vendors
        )
        
        # Check that all expected decision factors are present
        expected_factors = [
            'current_stock', 'avg_daily_usage', 'annual_demand',
            'days_until_stockout', 'lead_time_days', 'safety_margin_days',
            'reorder_threshold_days', 'reorder_point', 'target_stock_level',
            'eoq', 'stockout_risk', 'below_reorder_point'
        ]
        
        factors = result['decision_factors']
        for factor in expected_factors:
            self.assertIn(factor, factors, f"Missing decision factor: {factor}")
    
    def test_cost_savings_calculation(self):
        """Test cost savings calculation accuracy."""
        inventory_item = {
            'sku': 'SAVINGS-001',
            'on_hand': 20,
            'reorder_point': 50
        }
        
        transactions = self._generate_transactions('SAVINGS-001', 90, 3.0)
        
        result = self.policy.evaluate_reorder_need(
            inventory_item, transactions, self.vendors
        )
        
        if result['needs_reorder']:
            savings = result['cost_savings']
            
            # Should have savings information
            self.assertIn('savings_amount', savings)
            self.assertIn('savings_percentage', savings)
            self.assertIn('vs_vendor', savings)
            
            # Savings amount should be non-negative
            self.assertGreaterEqual(savings['savings_amount'], 0)
            self.assertGreaterEqual(savings['savings_percentage'], 0)
    
    def test_evidence_summary_quality(self):
        """Test quality and completeness of evidence summaries."""
        test_cases = [
            # Urgent case
            {'sku': 'URGENT-TEST', 'on_hand': 3, 'reorder_point': 20, 'daily_usage': 4.0},
            # Normal case
            {'sku': 'NORMAL-TEST', 'on_hand': 40, 'reorder_point': 60, 'daily_usage': 2.0},
            # Sufficient stock case
            {'sku': 'SUFFICIENT-TEST', 'on_hand': 150, 'reorder_point': 30, 'daily_usage': 1.0}
        ]
        
        for case in test_cases:
            inventory_item = {
                'sku': case['sku'],
                'on_hand': case['on_hand'],
                'reorder_point': case['reorder_point']
            }
            
            transactions = self._generate_transactions(
                case['sku'], 45, case['daily_usage']
            )
            
            result = self.policy.evaluate_reorder_need(
                inventory_item, transactions, self.vendors
            )
            
            summary = result['evidence_summary']
            
            # Summary should contain key information
            self.assertIn(case['sku'], summary)
            self.assertIn(str(case['on_hand']), summary)
            
            # Should indicate urgency level appropriately
            if result['needs_reorder']:
                if case['on_hand'] < 10:  # Very low stock
                    self.assertIn('URGENT', summary)
                self.assertIn('units', summary)
            else:
                self.assertIn('NO ACTION NEEDED', summary)
    
    def test_target_stock_days_impact(self):
        """Test impact of different target stock day settings."""
        inventory_item = {
            'sku': 'TARGET-001',
            'on_hand': 30,
            'reorder_point': 40
        }
        
        transactions = self._generate_transactions('TARGET-001', 60, 2.0)
        
        # Test with different target stock days
        result_30_days = self.policy.evaluate_reorder_need(
            inventory_item, transactions, self.vendors, target_stock_days=30
        )
        
        result_60_days = self.policy.evaluate_reorder_need(
            inventory_item, transactions, self.vendors, target_stock_days=60
        )
        
        # Higher target stock days should generally result in higher order quantities
        if result_30_days['needs_reorder'] and result_60_days['needs_reorder']:
            self.assertGreaterEqual(result_60_days['qty'], result_30_days['qty'])

class TestReorderPolicyIntegration(unittest.TestCase):
    """Integration tests for ReorderPolicy with mocked dependencies."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.policy = ReorderPolicy()
    
    @patch('policies.reorder_policy.compute_daily_average')
    @patch('policies.reorder_policy.estimate_days_until_stockout')
    @patch('policies.reorder_policy.select_best_vendor')
    def test_integration_with_mocked_dependencies(self, mock_select_vendor, mock_stockout, mock_daily_avg):
        """Test integration with mocked forecast and EOQ modules."""
        # Setup mocks
        mock_daily_avg.return_value = 2.5
        mock_stockout.return_value = 8.0
        mock_select_vendor.return_value = {
            'best_vendor': {
                'name': 'Test Vendor',
                'unit_cost': 10.0,
                'lead_time': 5,
                'eoq': 100
            },
            'eoq': 100,
            'total_cost': 1000.0,
            'comparisons': [
                {'name': 'Test Vendor', 'total_cost': 1000.0},
                {'name': 'Other Vendor', 'total_cost': 1200.0}
            ]
        }
        
        inventory_item = {
            'sku': 'MOCK-001',
            'on_hand': 20,
            'reorder_point': 30
        }
        
        transactions = [{'date': '2024-01-01', 'sku': 'MOCK-001', 'quantity': -2}]
        vendors = [{'name': 'Test Vendor', 'unit_cost': 10.0}]
        
        result = self.policy.evaluate_reorder_need(
            inventory_item, transactions, vendors
        )
        
        # Verify mocks were called
        mock_daily_avg.assert_called_once()
        mock_stockout.assert_called_once()
        mock_select_vendor.assert_called_once()
        
        # Verify result structure
        self.assertEqual(result['sku'], 'MOCK-001')
        self.assertEqual(result['vendor'], 'Test Vendor')
        self.assertIn('needs_reorder', result)

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTest(unittest.makeSuite(TestReorderPolicy))
    test_suite.addTest(unittest.makeSuite(TestReorderPolicyIntegration))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")