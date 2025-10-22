"""
Forecasting models for inventory replenishment.

This module provides baseline forecasting capabilities including:
- Daily usage computation from transaction history
- Weekly demand forecasting
- Stockout timeline estimation
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


def compute_daily_average(transactions: List[Dict], sku: str, window_days: int = 90) -> float:
    """
    Compute average daily usage for a SKU based on transaction history.
    
    Args:
        transactions: List of transaction dictionaries with keys:
                     - 'sku': Product SKU
                     - 'quantity': Quantity used (positive number)
                     - 'date': Transaction date (datetime or ISO string)
        sku: SKU to analyze
        window_days: Number of days to look back for analysis (default: 90)
    
    Returns:
        Average daily usage as a float. Returns 0.0 if no transactions found.
    
    Example:
        >>> transactions = [
        ...     {'sku': 'ABC123', 'quantity': 10, 'date': '2024-01-01'},
        ...     {'sku': 'ABC123', 'quantity': 15, 'date': '2024-01-02'}
        ... ]
        >>> compute_daily_average(transactions, 'ABC123', window_days=30)
        0.83  # (10 + 15) / 30 days
    """
    if not transactions:
        logger.warning(f"No transactions provided for SKU {sku}")
        return 0.0
    
    # Filter transactions for the specific SKU
    sku_transactions = [t for t in transactions if t.get('sku') == sku]
    
    if not sku_transactions:
        logger.warning(f"No transactions found for SKU {sku}")
        return 0.0
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=window_days)
    
    # Filter transactions within the window and sum quantities
    total_usage = 0.0
    valid_transactions = 0
    
    for transaction in sku_transactions:
        try:
            # Handle both datetime objects and string dates
            if isinstance(transaction['date'], str):
                trans_date = datetime.fromisoformat(transaction['date'].replace('Z', '+00:00'))
            else:
                trans_date = transaction['date']
            
            # Only include transactions within the window
            if trans_date >= cutoff_date:
                quantity = float(transaction.get('quantity', 0))
                if quantity > 0:  # Only count positive usage
                    total_usage += quantity
                    valid_transactions += 1
                    
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Skipping invalid transaction for SKU {sku}: {e}")
            continue
    
    if valid_transactions == 0:
        logger.info(f"No valid transactions found for SKU {sku} in the last {window_days} days")
        return 0.0
    
    # Calculate average daily usage
    avg_daily = total_usage / window_days
    
    logger.info(f"SKU {sku}: {total_usage} total usage over {window_days} days = {avg_daily:.2f} avg daily")
    return avg_daily


def forecast_weekly_demand(avg_daily_usage: float) -> float:
    """
    Forecast weekly demand based on average daily usage.
    
    Args:
        avg_daily_usage: Average daily usage rate
    
    Returns:
        Projected weekly demand (avg_daily_usage * 7)
    
    Example:
        >>> forecast_weekly_demand(2.5)
        17.5
    """
    if avg_daily_usage < 0:
        logger.warning(f"Negative daily usage provided: {avg_daily_usage}, treating as 0")
        avg_daily_usage = 0.0
    
    weekly_demand = avg_daily_usage * 7
    logger.debug(f"Weekly demand forecast: {avg_daily_usage} daily * 7 = {weekly_demand}")
    
    return weekly_demand


def estimate_days_until_stockout(on_hand: Union[int, float], avg_daily: float) -> float:
    """
    Estimate number of days until stockout based on current inventory and usage rate.
    
    Args:
        on_hand: Current inventory quantity on hand
        avg_daily: Average daily usage rate
    
    Returns:
        Estimated days until stockout as a float.
        Returns float('inf') if avg_daily is 0 or negative.
        Returns 0.0 if on_hand is 0 or negative.
    
    Example:
        >>> estimate_days_until_stockout(100, 2.5)
        40.0
        >>> estimate_days_until_stockout(0, 2.5)
        0.0
        >>> estimate_days_until_stockout(100, 0)
        inf
    """
    # Handle edge cases
    if on_hand <= 0:
        logger.warning(f"On-hand inventory is {on_hand}, stockout imminent")
        return 0.0
    
    if avg_daily <= 0:
        logger.info(f"Average daily usage is {avg_daily}, no stockout expected")
        return float('inf')
    
    days_until_stockout = float(on_hand) / avg_daily
    
    logger.debug(f"Stockout estimate: {on_hand} on hand / {avg_daily} daily = {days_until_stockout:.1f} days")
    
    return days_until_stockout


# Helper function for data validation
def validate_transaction_data(transactions: List[Dict]) -> List[str]:
    """
    Validate transaction data format and return list of validation errors.
    
    Args:
        transactions: List of transaction dictionaries
    
    Returns:
        List of validation error messages (empty if all valid)
    """
    errors = []
    
    if not isinstance(transactions, list):
        errors.append("Transactions must be a list")
        return errors
    
    required_fields = ['sku', 'quantity', 'date']
    
    for i, transaction in enumerate(transactions):
        if not isinstance(transaction, dict):
            errors.append(f"Transaction {i} must be a dictionary")
            continue
        
        for field in required_fields:
            if field not in transaction:
                errors.append(f"Transaction {i} missing required field: {field}")
        
        # Validate quantity is numeric
        if 'quantity' in transaction:
            try:
                float(transaction['quantity'])
            except (ValueError, TypeError):
                errors.append(f"Transaction {i} has invalid quantity: {transaction['quantity']}")
        
        # Validate date format
        if 'date' in transaction and isinstance(transaction['date'], str):
            try:
                datetime.fromisoformat(transaction['date'].replace('Z', '+00:00'))
            except ValueError:
                errors.append(f"Transaction {i} has invalid date format: {transaction['date']}")
    
    return errors


if __name__ == "__main__":
    # Example usage and testing
    import json
    
    # Sample transaction data
    sample_transactions = [
        {'sku': 'ABC123', 'quantity': 10, 'date': '2024-01-01T00:00:00'},
        {'sku': 'ABC123', 'quantity': 15, 'date': '2024-01-02T00:00:00'},
        {'sku': 'ABC123', 'quantity': 8, 'date': '2024-01-03T00:00:00'},
        {'sku': 'XYZ789', 'quantity': 5, 'date': '2024-01-01T00:00:00'},
        {'sku': 'XYZ789', 'quantity': 12, 'date': '2024-01-04T00:00:00'},
    ]
    
    print("=== Forecast Model Demo ===")
    
    # Test validation
    errors = validate_transaction_data(sample_transactions)
    if errors:
        print(f"Validation errors: {errors}")
    else:
        print("✓ Transaction data validation passed")
    
    # Test forecasting for ABC123
    sku = 'ABC123'
    avg_daily = compute_daily_average(sample_transactions, sku, window_days=30)
    weekly_demand = forecast_weekly_demand(avg_daily)
    
    print(f"\nSKU: {sku}")
    print(f"Average daily usage: {avg_daily:.2f}")
    print(f"Weekly demand forecast: {weekly_demand:.2f}")
    
    # Test stockout estimation
    current_inventory = 100
    days_to_stockout = estimate_days_until_stockout(current_inventory, avg_daily)
    
    print(f"Current inventory: {current_inventory}")
    print(f"Days until stockout: {days_to_stockout:.1f}")
    
    # Test edge cases
    print(f"\nEdge case tests:")
    print(f"Zero inventory: {estimate_days_until_stockout(0, avg_daily)}")
    print(f"Zero usage: {estimate_days_until_stockout(100, 0)}")
    print(f"No transactions: {compute_daily_average([], 'MISSING')}")