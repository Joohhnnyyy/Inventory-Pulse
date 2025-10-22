"""
Unit tests for the forecast module.

Tests cover:
- Daily average computation with various scenarios
- Weekly demand forecasting
- Stockout estimation with edge cases
- Data validation
"""

import unittest
from datetime import datetime, timedelta
from src.models.forecast import (
    compute_daily_average,
    forecast_weekly_demand,
    estimate_days_until_stockout,
    validate_transaction_data
)


class TestForecast(unittest.TestCase):
    """Test cases for forecasting functions."""
    
    def setUp(self):
        """Set up test data."""
        # Base date for consistent testing
        self.base_date = datetime(2024, 1, 1)
        
        # Generate synthetic transaction data
        self.sample_transactions = [
            {'sku': 'ABC123', 'quantity': 10, 'date': '2024-01-01T00:00:00'},
            {'sku': 'ABC123', 'quantity': 15, 'date': '2024-01-02T00:00:00'},
            {'sku': 'ABC123', 'quantity': 8, 'date': '2024-01-03T00:00:00'},
            {'sku': 'ABC123', 'quantity': 12, 'date': '2024-01-04T00:00:00'},
            {'sku': 'ABC123', 'quantity': 20, 'date': '2024-01-05T00:00:00'},
            {'sku': 'XYZ789', 'quantity': 5, 'date': '2024-01-01T00:00:00'},
            {'sku': 'XYZ789', 'quantity': 7, 'date': '2024-01-02T00:00:00'},
            {'sku': 'XYZ789', 'quantity': 3, 'date': '2024-01-03T00:00:00'},
        ]
        
        # Old transactions (outside typical window)
        old_date = (datetime.now() - timedelta(days=120)).isoformat()
        self.old_transactions = [
            {'sku': 'ABC123', 'quantity': 100, 'date': old_date},
        ]
        
        # Mixed valid and invalid transactions
        self.mixed_transactions = [
            {'sku': 'ABC123', 'quantity': 10, 'date': '2024-01-01T00:00:00'},
            {'sku': 'ABC123', 'quantity': 'invalid', 'date': '2024-01-02T00:00:00'},
            {'sku': 'ABC123', 'quantity': 15, 'date': 'invalid-date'},
            {'sku': 'ABC123', 'quantity': -5, 'date': '2024-01-03T00:00:00'},  # Negative quantity
            {'sku': 'ABC123', 'quantity': 8, 'date': '2024-01-04T00:00:00'},
        ]

    def test_compute_daily_average_basic(self):
        """Test basic daily average computation."""
        # Test with known data
        avg = compute_daily_average(self.sample_transactions, 'ABC123', window_days=30)
        
        # ABC123 has transactions: 10, 15, 8, 12, 20 = 65 total
        # Over 30 days = 65/30 = 2.167
        expected = 65.0 / 30.0
        self.assertAlmostEqual(avg, expected, places=2)

    def test_compute_daily_average_different_sku(self):
        """Test daily average for different SKU."""
        avg = compute_daily_average(self.sample_transactions, 'XYZ789', window_days=30)
        
        # XYZ789 has transactions: 5, 7, 3 = 15 total
        # Over 30 days = 15/30 = 0.5
        expected = 15.0 / 30.0
        self.assertAlmostEqual(avg, expected, places=2)

    def test_compute_daily_average_no_transactions(self):
        """Test daily average with no transactions."""
        avg = compute_daily_average([], 'ABC123', window_days=30)
        self.assertEqual(avg, 0.0)

    def test_compute_daily_average_no_matching_sku(self):
        """Test daily average with no matching SKU."""
        avg = compute_daily_average(self.sample_transactions, 'NONEXISTENT', window_days=30)
        self.assertEqual(avg, 0.0)

    def test_compute_daily_average_with_old_data(self):
        """Test that old transactions are excluded."""
        # Combine recent and old transactions
        all_transactions = self.sample_transactions + self.old_transactions
        
        # Should only use recent transactions, not the old 100-quantity one
        avg = compute_daily_average(all_transactions, 'ABC123', window_days=90)
        
        # Should be same as without old data
        expected = 65.0 / 90.0
        self.assertAlmostEqual(avg, expected, places=2)

    def test_compute_daily_average_with_invalid_data(self):
        """Test daily average with mixed valid/invalid data."""
        avg = compute_daily_average(self.mixed_transactions, 'ABC123', window_days=30)
        
        # Should only count valid positive transactions: 10, 8 = 18 total
        # Negative quantity (-5) should be ignored
        expected = 18.0 / 30.0
        self.assertAlmostEqual(avg, expected, places=2)

    def test_forecast_weekly_demand_basic(self):
        """Test basic weekly demand forecasting."""
        daily_avg = 2.5
        weekly = forecast_weekly_demand(daily_avg)
        expected = 2.5 * 7
        self.assertEqual(weekly, expected)

    def test_forecast_weekly_demand_zero(self):
        """Test weekly demand with zero daily usage."""
        weekly = forecast_weekly_demand(0.0)
        self.assertEqual(weekly, 0.0)

    def test_forecast_weekly_demand_negative(self):
        """Test weekly demand with negative daily usage."""
        weekly = forecast_weekly_demand(-1.0)
        self.assertEqual(weekly, 0.0)  # Should treat negative as 0

    def test_estimate_days_until_stockout_basic(self):
        """Test basic stockout estimation."""
        days = estimate_days_until_stockout(100, 2.5)
        expected = 100.0 / 2.5
        self.assertEqual(days, expected)

    def test_estimate_days_until_stockout_zero_inventory(self):
        """Test stockout estimation with zero inventory."""
        days = estimate_days_until_stockout(0, 2.5)
        self.assertEqual(days, 0.0)

    def test_estimate_days_until_stockout_negative_inventory(self):
        """Test stockout estimation with negative inventory."""
        days = estimate_days_until_stockout(-10, 2.5)
        self.assertEqual(days, 0.0)

    def test_estimate_days_until_stockout_zero_usage(self):
        """Test stockout estimation with zero daily usage."""
        days = estimate_days_until_stockout(100, 0.0)
        self.assertEqual(days, float('inf'))

    def test_estimate_days_until_stockout_negative_usage(self):
        """Test stockout estimation with negative daily usage."""
        days = estimate_days_until_stockout(100, -1.0)
        self.assertEqual(days, float('inf'))

    def test_validate_transaction_data_valid(self):
        """Test validation with valid transaction data."""
        errors = validate_transaction_data(self.sample_transactions)
        self.assertEqual(len(errors), 0)

    def test_validate_transaction_data_invalid_structure(self):
        """Test validation with invalid data structure."""
        # Not a list
        errors = validate_transaction_data("not a list")
        self.assertIn("Transactions must be a list", errors)
        
        # List with non-dict items
        errors = validate_transaction_data([1, 2, 3])
        self.assertTrue(any("must be a dictionary" in error for error in errors))

    def test_validate_transaction_data_missing_fields(self):
        """Test validation with missing required fields."""
        invalid_transactions = [
            {'sku': 'ABC123'},  # Missing quantity and date
            {'quantity': 10},   # Missing sku and date
            {'date': '2024-01-01'},  # Missing sku and quantity
        ]
        
        errors = validate_transaction_data(invalid_transactions)
        
        # Should have errors for missing fields
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any("missing required field" in error for error in errors))

    def test_validate_transaction_data_invalid_types(self):
        """Test validation with invalid field types."""
        invalid_transactions = [
            {'sku': 'ABC123', 'quantity': 'not_a_number', 'date': '2024-01-01T00:00:00'},
            {'sku': 'ABC123', 'quantity': 10, 'date': 'invalid_date_format'},
        ]
        
        errors = validate_transaction_data(invalid_transactions)
        
        # Should have errors for invalid types
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any("invalid quantity" in error for error in errors))
        self.assertTrue(any("invalid date format" in error for error in errors))

    def test_integration_realistic_scenario(self):
        """Test integration with realistic inventory scenario."""
        # Create realistic transaction history for a product
        transactions = []
        base_date = datetime.now() - timedelta(days=60)
        
        # Generate 60 days of transactions with varying usage
        for day in range(60):
            date = base_date + timedelta(days=day)
            # Simulate varying daily usage (2-8 units per day)
            quantity = 2 + (day % 7)  # Varies from 2 to 8
            transactions.append({
                'sku': 'PROD001',
                'quantity': quantity,
                'date': date.isoformat()
            })
        
        # Calculate forecasts
        avg_daily = compute_daily_average(transactions, 'PROD001', window_days=60)
        weekly_demand = forecast_weekly_demand(avg_daily)
        
        # Test with current inventory
        current_inventory = 200
        days_to_stockout = estimate_days_until_stockout(current_inventory, avg_daily)
        
        # Validate results are reasonable
        self.assertGreater(avg_daily, 0)
        self.assertLess(avg_daily, 10)  # Should be between 2-8 based on our data
        self.assertEqual(weekly_demand, avg_daily * 7)
        self.assertGreater(days_to_stockout, 0)
        self.assertLess(days_to_stockout, 365)  # Should be reasonable

    def test_datetime_object_handling(self):
        """Test handling of datetime objects vs string dates."""
        # Create transactions with datetime objects
        datetime_transactions = [
            {'sku': 'TEST001', 'quantity': 10, 'date': datetime(2024, 1, 1)},
            {'sku': 'TEST001', 'quantity': 15, 'date': datetime(2024, 1, 2)},
        ]
        
        avg = compute_daily_average(datetime_transactions, 'TEST001', window_days=30)
        expected = 25.0 / 30.0
        self.assertAlmostEqual(avg, expected, places=2)

    def test_edge_case_single_transaction(self):
        """Test with single transaction."""
        single_transaction = [
            {'sku': 'SINGLE', 'quantity': 42, 'date': '2024-01-01T00:00:00'}
        ]
        
        avg = compute_daily_average(single_transaction, 'SINGLE', window_days=30)
        expected = 42.0 / 30.0
        self.assertAlmostEqual(avg, expected, places=2)


class TestForecastPerformance(unittest.TestCase):
    """Performance tests for forecast functions."""
    
    def test_large_dataset_performance(self):
        """Test performance with large transaction dataset."""
        # Generate large dataset
        large_transactions = []
        base_date = datetime.now() - timedelta(days=365)
        
        for day in range(365):
            for transaction in range(5):  # 5 transactions per day
                date = base_date + timedelta(days=day)
                large_transactions.append({
                    'sku': f'SKU{transaction % 10}',
                    'quantity': 1 + (transaction % 5),
                    'date': date.isoformat()
                })
        
        # Should handle 1825 transactions efficiently
        import time
        start_time = time.time()
        
        avg = compute_daily_average(large_transactions, 'SKU0', window_days=90)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete in reasonable time (< 1 second)
        self.assertLess(processing_time, 1.0)
        self.assertGreater(avg, 0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)