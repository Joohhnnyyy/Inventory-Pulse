"""
Reorder Policy Decision Engine

This module implements comprehensive reorder decision logic that integrates
forecasting, EOQ optimization, and vendor selection to make intelligent
inventory replenishment decisions.

Author: Inventory Intelligence Team
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.forecast import compute_daily_average, estimate_days_until_stockout
from policies.eoq_optimizer import select_best_vendor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReorderPolicy:
    """
    Intelligent reorder policy that combines forecasting, EOQ optimization,
    and vendor selection to make optimal inventory decisions.
    """
    
    def __init__(self, safety_margin_days: int = 7, min_order_qty: int = 1):
        """
        Initialize reorder policy with configuration parameters.
        
        Args:
            safety_margin_days: Additional days of safety stock
            min_order_qty: Minimum order quantity
        """
        self.safety_margin_days = safety_margin_days
        self.min_order_qty = min_order_qty
        logger.info(f"ReorderPolicy initialized with safety_margin={safety_margin_days} days, min_order_qty={min_order_qty}")
    
    def evaluate_reorder_need(
        self,
        inventory_item: Dict,
        transactions: List[Dict],
        vendors: List[Dict],
        target_stock_days: int = 30
    ) -> Dict:
        """
        Evaluate whether an item needs reordering and generate recommendations.
        
        Args:
            inventory_item: Dict with fields: sku, on_hand, reorder_point
            transactions: List of transaction dicts with date, sku, quantity
            vendors: List of vendor dicts with name, unit_cost, holding_cost_rate, order_cost, lead_time
            target_stock_days: Target days of stock to maintain
            
        Returns:
            Dict: Reorder recommendation with fields:
                - sku: Product SKU
                - needs_reorder: Boolean indicating if reorder is needed
                - vendor: Recommended vendor name
                - qty: Recommended order quantity
                - eoq: Economic Order Quantity
                - total_cost: Total cost for recommended vendor
                - stockout_date: Predicted stockout date
                - evidence_summary: Summary of decision factors
                - cost_savings: Savings vs other vendors
                - decision_factors: Detailed breakdown of decision logic
        """
        try:
            sku = inventory_item['sku']
            on_hand = inventory_item['on_hand']
            reorder_point = inventory_item.get('reorder_point', 0)
            
            logger.info(f"Evaluating reorder need for SKU: {sku}")
            
            # Step 1: Compute average daily usage using forecast module
            avg_daily = compute_daily_average(transactions, sku)
            if avg_daily <= 0:
                logger.warning(f"No historical usage found for {sku}, using minimal demand assumption")
                avg_daily = 0.1  # Minimal assumption for new items
            
            # Step 2: Calculate annual demand
            annual_demand = avg_daily * 365
            
            # Step 3: Select best vendor using EOQ optimizer
            if not vendors:
                raise ValueError("No vendors provided for evaluation")
            
            best_vendor_result = select_best_vendor(annual_demand, vendors)
            best_vendor = best_vendor_result['best_vendor']
            
            # Step 4: Compute expected days until stockout and stockout date
            days_until_stockout = estimate_days_until_stockout(transactions, sku, on_hand)
            stockout_date = datetime.now() + timedelta(days=days_until_stockout)
            
            # Step 5: Determine if reorder is needed
            lead_time = best_vendor.get('lead_time', 7)  # Default 7 days
            reorder_threshold_days = lead_time + self.safety_margin_days
            
            needs_reorder = (
                days_until_stockout <= reorder_threshold_days or
                on_hand <= reorder_point
            )
            
            # Step 6: Calculate recommended quantity
            target_stock = avg_daily * target_stock_days
            eoq = best_vendor_result['eoq']
            
            if needs_reorder:
                # Recommend quantity to reach target stock level
                qty_to_target = max(0, target_stock - on_hand)
                recommended_qty = max(eoq, self.min_order_qty, qty_to_target)
            else:
                recommended_qty = 0
            
            # Step 7: Calculate cost savings vs other vendors
            cost_savings = self._calculate_cost_savings(best_vendor_result, annual_demand)
            
            # Step 8: Generate evidence summary
            evidence_summary = self._generate_evidence_summary(
                sku, on_hand, avg_daily, days_until_stockout, 
                best_vendor, needs_reorder, recommended_qty
            )
            
            # Detailed decision factors
            decision_factors = {
                'current_stock': on_hand,
                'avg_daily_usage': round(avg_daily, 2),
                'annual_demand': round(annual_demand, 2),
                'days_until_stockout': round(days_until_stockout, 1),
                'lead_time_days': lead_time,
                'safety_margin_days': self.safety_margin_days,
                'reorder_threshold_days': reorder_threshold_days,
                'reorder_point': reorder_point,
                'target_stock_level': round(target_stock, 1),
                'eoq': eoq,
                'stockout_risk': days_until_stockout <= reorder_threshold_days,
                'below_reorder_point': on_hand <= reorder_point
            }
            
            result = {
                'sku': sku,
                'needs_reorder': needs_reorder,
                'vendor': best_vendor['name'],
                'qty': recommended_qty,
                'eoq': eoq,
                'total_cost': best_vendor_result['total_cost'],
                'stockout_date': stockout_date.strftime('%Y-%m-%d'),
                'evidence_summary': evidence_summary,
                'cost_savings': cost_savings,
                'decision_factors': decision_factors
            }
            
            logger.info(f"Reorder evaluation complete for {sku}: needs_reorder={needs_reorder}")
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating reorder need for {inventory_item.get('sku', 'unknown')}: {e}")
            raise
    
    def _calculate_cost_savings(self, best_vendor_result: Dict, annual_demand: float) -> Dict:
        """
        Calculate cost savings compared to other vendors.
        
        Args:
            best_vendor_result: Result from select_best_vendor
            annual_demand: Annual demand quantity
            
        Returns:
            Dict: Cost savings information
        """
        try:
            comparisons = best_vendor_result.get('comparisons', [])
            if len(comparisons) <= 1:
                return {
                    'savings_amount': 0,
                    'savings_percentage': 0,
                    'vs_vendor': None
                }
            
            # Find the second-best vendor
            sorted_comparisons = sorted(comparisons, key=lambda x: x['total_cost'])
            best_cost = sorted_comparisons[0]['total_cost']
            second_best = sorted_comparisons[1]
            
            savings_amount = second_best['total_cost'] - best_cost
            savings_percentage = (savings_amount / second_best['total_cost']) * 100
            
            return {
                'savings_amount': round(savings_amount, 2),
                'savings_percentage': round(savings_percentage, 1),
                'vs_vendor': second_best['name']
            }
            
        except Exception as e:
            logger.warning(f"Error calculating cost savings: {e}")
            return {
                'savings_amount': 0,
                'savings_percentage': 0,
                'vs_vendor': None
            }
    
    def _generate_evidence_summary(
        self,
        sku: str,
        on_hand: int,
        avg_daily: float,
        days_until_stockout: float,
        best_vendor: Dict,
        needs_reorder: bool,
        recommended_qty: int
    ) -> str:
        """
        Generate human-readable evidence summary for the reorder decision.
        
        Args:
            sku: Product SKU
            on_hand: Current stock level
            avg_daily: Average daily usage
            days_until_stockout: Days until predicted stockout
            best_vendor: Selected vendor information
            needs_reorder: Whether reorder is needed
            recommended_qty: Recommended order quantity
            
        Returns:
            str: Evidence summary
        """
        if needs_reorder:
            if days_until_stockout <= self.safety_margin_days:
                urgency = "URGENT"
                reason = f"stockout predicted in {days_until_stockout:.1f} days"
            elif days_until_stockout <= (best_vendor.get('lead_time', 7) + self.safety_margin_days):
                urgency = "HIGH"
                reason = f"stockout within lead time + safety margin ({days_until_stockout:.1f} days)"
            else:
                urgency = "MEDIUM"
                reason = "below reorder point threshold"
            
            summary = (
                f"{urgency} PRIORITY: {sku} needs reordering ({reason}). "
                f"Current stock: {on_hand} units, daily usage: {avg_daily:.1f} units. "
                f"Recommend ordering {recommended_qty} units from {best_vendor['name']} "
                f"(EOQ: {best_vendor.get('eoq', 'N/A')}, cost: ${best_vendor.get('total_cost', 0):.2f})."
            )
        else:
            summary = (
                f"NO ACTION NEEDED: {sku} has sufficient stock. "
                f"Current: {on_hand} units, {days_until_stockout:.1f} days until stockout, "
                f"daily usage: {avg_daily:.1f} units."
            )
        
        return summary
    
    def batch_evaluate_reorders(
        self,
        inventory_items: List[Dict],
        transactions: List[Dict],
        vendors: List[Dict],
        target_stock_days: int = 30
    ) -> List[Dict]:
        """
        Evaluate reorder needs for multiple inventory items.
        
        Args:
            inventory_items: List of inventory item dicts
            transactions: List of transaction dicts
            vendors: List of vendor dicts
            target_stock_days: Target days of stock to maintain
            
        Returns:
            List[Dict]: List of reorder recommendations
        """
        results = []
        
        for item in inventory_items:
            try:
                # Filter transactions for this SKU
                item_transactions = [t for t in transactions if t.get('sku') == item['sku']]
                
                result = self.evaluate_reorder_need(
                    item, item_transactions, vendors, target_stock_days
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to evaluate {item.get('sku', 'unknown')}: {e}")
                # Add error result
                results.append({
                    'sku': item.get('sku', 'unknown'),
                    'needs_reorder': False,
                    'error': str(e),
                    'evidence_summary': f"Error evaluating {item.get('sku', 'unknown')}: {e}"
                })
        
        # Sort by priority (urgent reorders first)
        results.sort(key=lambda x: (
            not x.get('needs_reorder', False),  # Reorders first
            x.get('decision_factors', {}).get('days_until_stockout', 999)  # Most urgent first
        ))
        
        logger.info(f"Batch evaluation complete: {len(results)} items processed")
        return results

if __name__ == "__main__":
    """
    Example usage and testing of the reorder policy.
    """
    print("=== Reorder Policy Test ===")
    
    # Initialize policy
    policy = ReorderPolicy(safety_margin_days=7, min_order_qty=10)
    
    # Example inventory item
    inventory_item = {
        'sku': 'WIDGET-001',
        'on_hand': 25,
        'reorder_point': 50
    }
    
    # Example transactions (last 90 days)
    transactions = []
    base_date = datetime.now() - timedelta(days=90)
    
    # Generate synthetic transaction history
    for i in range(90):
        date = base_date + timedelta(days=i)
        # Simulate varying daily usage (1-4 units per day)
        daily_usage = 2 + (i % 3)  # Varies between 2-4
        transactions.append({
            'date': date.strftime('%Y-%m-%d'),
            'sku': 'WIDGET-001',
            'quantity': -daily_usage,  # Negative for outbound
            'type': 'sale'
        })
    
    # Example vendors
    vendors = [
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
    
    print(f"Evaluating: {inventory_item}")
    print(f"Transaction history: {len(transactions)} records")
    print(f"Vendor options: {len(vendors)} vendors")
    
    try:
        # Evaluate reorder need
        result = policy.evaluate_reorder_need(
            inventory_item, transactions, vendors, target_stock_days=30
        )
        
        print("\n=== Reorder Recommendation ===")
        print(f"SKU: {result['sku']}")
        print(f"Needs Reorder: {result['needs_reorder']}")
        print(f"Recommended Vendor: {result['vendor']}")
        print(f"Recommended Quantity: {result['qty']}")
        print(f"EOQ: {result['eoq']}")
        print(f"Total Cost: ${result['total_cost']:.2f}")
        print(f"Predicted Stockout: {result['stockout_date']}")
        
        print(f"\nEvidence Summary:")
        print(result['evidence_summary'])
        
        print(f"\nCost Savings:")
        savings = result['cost_savings']
        if savings['vs_vendor']:
            print(f"Save ${savings['savings_amount']:.2f} ({savings['savings_percentage']:.1f}%) vs {savings['vs_vendor']}")
        else:
            print("No cost comparison available")
        
        print(f"\nDecision Factors:")
        factors = result['decision_factors']
        for key, value in factors.items():
            print(f"  {key}: {value}")
        
        # Test batch evaluation
        print("\n=== Batch Evaluation Test ===")
        inventory_items = [
            inventory_item,
            {'sku': 'GADGET-002', 'on_hand': 100, 'reorder_point': 30},
            {'sku': 'TOOL-003', 'on_hand': 5, 'reorder_point': 20}
        ]
        
        # Add transactions for other SKUs
        for sku in ['GADGET-002', 'TOOL-003']:
            for i in range(30):  # Less history for these items
                date = base_date + timedelta(days=i)
                daily_usage = 1 + (i % 2)  # 1-2 units per day
                transactions.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'sku': sku,
                    'quantity': -daily_usage,
                    'type': 'sale'
                })
        
        batch_results = policy.batch_evaluate_reorders(
            inventory_items, transactions, vendors
        )
        
        print(f"Batch results for {len(batch_results)} items:")
        for result in batch_results:
            status = "REORDER" if result.get('needs_reorder') else "OK"
            print(f"  {result['sku']}: {status} - {result.get('evidence_summary', 'N/A')}")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()