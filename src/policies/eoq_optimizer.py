"""
Economic Order Quantity (EOQ) optimizer and vendor selection.

This module provides:
- EOQ calculation using the classic Wilson formula
- Total cost calculation for different vendors
- Vendor selection optimization based on total cost
"""

import math
from typing import List, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


def calculate_eoq(annual_demand: Union[int, float], order_cost: Union[int, float], 
                  holding_cost_per_unit: Union[int, float]) -> int:
    """
    Calculate Economic Order Quantity using the Wilson EOQ formula.
    
    EOQ = sqrt((2 * D * S) / H)
    Where:
    - D = Annual demand
    - S = Order cost per order
    - H = Holding cost per unit per year
    
    Args:
        annual_demand: Annual demand quantity
        order_cost: Cost to place one order (setup cost)
        holding_cost_per_unit: Annual holding cost per unit
    
    Returns:
        EOQ as integer (rounded up to ensure adequate supply)
        Returns 0 if any input is invalid or zero
    
    Example:
        >>> calculate_eoq(1000, 50, 2.5)
        200
    """
    # Validate inputs
    if annual_demand <= 0:
        logger.warning(f"Invalid annual demand: {annual_demand}")
        return 0
    
    if order_cost <= 0:
        logger.warning(f"Invalid order cost: {order_cost}")
        return 0
    
    if holding_cost_per_unit <= 0:
        logger.warning(f"Invalid holding cost: {holding_cost_per_unit}")
        return 0
    
    try:
        # Wilson EOQ formula
        eoq_float = math.sqrt((2 * annual_demand * order_cost) / holding_cost_per_unit)
        
        # Round up to ensure we don't under-order
        eoq = math.ceil(eoq_float)
        
        logger.debug(f"EOQ calculation: sqrt((2*{annual_demand}*{order_cost})/{holding_cost_per_unit}) = {eoq}")
        
        return eoq
        
    except (ValueError, ZeroDivisionError) as e:
        logger.error(f"Error calculating EOQ: {e}")
        return 0


def calculate_total_cost_for_vendor(annual_demand: Union[int, float], vendor: Dict) -> float:
    """
    Calculate total annual cost for a specific vendor including purchase, ordering, and holding costs.
    
    Total Cost = Purchase Cost + Ordering Cost + Holding Cost
    Where:
    - Purchase Cost = annual_demand * price_per_unit
    - Ordering Cost = (annual_demand / EOQ) * order_cost
    - Holding Cost = (EOQ / 2) * price_per_unit * holding_cost_percentage
    
    Args:
        annual_demand: Annual demand quantity
        vendor: Dictionary containing vendor information with keys:
                - price_per_unit: Unit price from this vendor
                - order_cost: Cost to place an order with this vendor
                - lead_time_days: Lead time in days (for reference)
                - vendor_id: Unique vendor identifier
                - vendor_name: Vendor name
                - holding_cost_percentage: Annual holding cost as % of unit value (default: 0.25)
    
    Returns:
        Total annual cost as float
        Returns float('inf') if calculation fails or inputs are invalid
    
    Example:
        >>> vendor = {
        ...     'price_per_unit': 10.0,
        ...     'order_cost': 50.0,
        ...     'holding_cost_percentage': 0.25,
        ...     'vendor_id': 'V001',
        ...     'vendor_name': 'Supplier A'
        ... }
        >>> calculate_total_cost_for_vendor(1000, vendor)
        10125.0
    """
    # Validate inputs
    if annual_demand <= 0:
        logger.warning(f"Invalid annual demand: {annual_demand}")
        return float('inf')
    
    required_fields = ['price_per_unit', 'order_cost']
    for field in required_fields:
        if field not in vendor:
            logger.error(f"Vendor missing required field: {field}")
            return float('inf')
        
        if vendor[field] <= 0:
            logger.warning(f"Invalid vendor {field}: {vendor[field]}")
            return float('inf')
    
    try:
        # Extract vendor parameters
        price_per_unit = float(vendor['price_per_unit'])
        order_cost = float(vendor['order_cost'])
        holding_cost_percentage = float(vendor.get('holding_cost_percentage', 0.25))
        
        # Calculate holding cost per unit per year
        holding_cost_per_unit = price_per_unit * holding_cost_percentage
        
        # Calculate EOQ for this vendor
        eoq = calculate_eoq(annual_demand, order_cost, holding_cost_per_unit)
        
        if eoq == 0:
            logger.error(f"Could not calculate EOQ for vendor {vendor.get('vendor_id', 'unknown')}")
            return float('inf')
        
        # Calculate total cost components
        purchase_cost = annual_demand * price_per_unit
        ordering_cost = (annual_demand / eoq) * order_cost
        holding_cost = (eoq / 2) * holding_cost_per_unit
        
        total_cost = purchase_cost + ordering_cost + holding_cost
        
        logger.debug(f"Vendor {vendor.get('vendor_name', 'unknown')} total cost breakdown:")
        logger.debug(f"  Purchase: ${purchase_cost:.2f}")
        logger.debug(f"  Ordering: ${ordering_cost:.2f}")
        logger.debug(f"  Holding: ${holding_cost:.2f}")
        logger.debug(f"  Total: ${total_cost:.2f}")
        
        return total_cost
        
    except (ValueError, TypeError, ZeroDivisionError) as e:
        logger.error(f"Error calculating total cost for vendor: {e}")
        return float('inf')


def select_best_vendor(vendors_list: List[Dict], annual_demand: Union[int, float]) -> Optional[Dict]:
    """
    Select the vendor with the lowest total cost and augment with EOQ and cost information.
    
    Args:
        vendors_list: List of vendor dictionaries (see calculate_total_cost_for_vendor for format)
        annual_demand: Annual demand quantity
    
    Returns:
        Best vendor dictionary augmented with:
        - 'eoq': Calculated EOQ for this vendor
        - 'total_annual_cost': Total annual cost
        - 'cost_breakdown': Dict with purchase_cost, ordering_cost, holding_cost
        
        Returns None if no valid vendors or zero demand
    
    Example:
        >>> vendors = [
        ...     {'vendor_id': 'V001', 'vendor_name': 'Supplier A', 'price_per_unit': 10.0, 'order_cost': 50.0},
        ...     {'vendor_id': 'V002', 'vendor_name': 'Supplier B', 'price_per_unit': 9.5, 'order_cost': 75.0}
        ... ]
        >>> best = select_best_vendor(vendors, 1000)
        >>> print(f"Best vendor: {best['vendor_name']} with EOQ: {best['eoq']}")
    """
    # Validate inputs
    if annual_demand <= 0:
        logger.warning(f"Invalid annual demand for vendor selection: {annual_demand}")
        return None
    
    if not vendors_list:
        logger.warning("No vendors provided for selection")
        return None
    
    if not isinstance(vendors_list, list):
        logger.error("Vendors must be provided as a list")
        return None
    
    best_vendor = None
    best_cost = float('inf')
    
    logger.info(f"Evaluating {len(vendors_list)} vendors for annual demand of {annual_demand}")
    
    for i, vendor in enumerate(vendors_list):
        if not isinstance(vendor, dict):
            logger.warning(f"Vendor {i} is not a dictionary, skipping")
            continue
        
        vendor_id = vendor.get('vendor_id', f'vendor_{i}')
        vendor_name = vendor.get('vendor_name', f'Vendor {i}')
        
        # Calculate total cost for this vendor
        total_cost = calculate_total_cost_for_vendor(annual_demand, vendor)
        
        if total_cost == float('inf'):
            logger.warning(f"Could not calculate cost for vendor {vendor_name} ({vendor_id})")
            continue
        
        logger.info(f"Vendor {vendor_name} ({vendor_id}): Total cost = ${total_cost:.2f}")
        
        # Check if this is the best vendor so far
        if total_cost < best_cost:
            best_cost = total_cost
            best_vendor = vendor.copy()  # Make a copy to avoid modifying original
            
            # Calculate additional details for the best vendor
            price_per_unit = float(vendor['price_per_unit'])
            order_cost = float(vendor['order_cost'])
            holding_cost_percentage = float(vendor.get('holding_cost_percentage', 0.25))
            holding_cost_per_unit = price_per_unit * holding_cost_percentage
            
            eoq = calculate_eoq(annual_demand, order_cost, holding_cost_per_unit)
            
            # Calculate cost breakdown
            purchase_cost = annual_demand * price_per_unit
            ordering_cost = (annual_demand / eoq) * order_cost if eoq > 0 else 0
            holding_cost = (eoq / 2) * holding_cost_per_unit if eoq > 0 else 0
            
            # Augment vendor with calculated values
            best_vendor.update({
                'eoq': eoq,
                'total_annual_cost': total_cost,
                'cost_breakdown': {
                    'purchase_cost': purchase_cost,
                    'ordering_cost': ordering_cost,
                    'holding_cost': holding_cost
                }
            })
    
    if best_vendor is None:
        logger.error("No valid vendors found")
        return None
    
    logger.info(f"Selected best vendor: {best_vendor.get('vendor_name')} with total cost ${best_cost:.2f}")
    
    return best_vendor


def compare_vendors(vendors_list: List[Dict], annual_demand: Union[int, float]) -> List[Dict]:
    """
    Compare all vendors and return them sorted by total cost (lowest first).
    
    Args:
        vendors_list: List of vendor dictionaries
        annual_demand: Annual demand quantity
    
    Returns:
        List of vendor dictionaries augmented with cost information, sorted by total cost
        Invalid vendors are excluded from results
    """
    if annual_demand <= 0 or not vendors_list:
        return []
    
    vendor_comparisons = []
    
    for vendor in vendors_list:
        if not isinstance(vendor, dict):
            continue
        
        total_cost = calculate_total_cost_for_vendor(annual_demand, vendor)
        
        if total_cost == float('inf'):
            continue
        
        # Calculate EOQ and cost breakdown
        price_per_unit = float(vendor['price_per_unit'])
        order_cost = float(vendor['order_cost'])
        holding_cost_percentage = float(vendor.get('holding_cost_percentage', 0.25))
        holding_cost_per_unit = price_per_unit * holding_cost_percentage
        
        eoq = calculate_eoq(annual_demand, order_cost, holding_cost_per_unit)
        
        purchase_cost = annual_demand * price_per_unit
        ordering_cost = (annual_demand / eoq) * order_cost if eoq > 0 else 0
        holding_cost = (eoq / 2) * holding_cost_per_unit if eoq > 0 else 0
        
        # Create augmented vendor record
        vendor_comparison = vendor.copy()
        vendor_comparison.update({
            'eoq': eoq,
            'total_annual_cost': total_cost,
            'cost_breakdown': {
                'purchase_cost': purchase_cost,
                'ordering_cost': ordering_cost,
                'holding_cost': holding_cost
            }
        })
        
        vendor_comparisons.append(vendor_comparison)
    
    # Sort by total cost (lowest first)
    vendor_comparisons.sort(key=lambda v: v['total_annual_cost'])
    
    return vendor_comparisons


if __name__ == "__main__":
    # Example usage and testing
    print("=== EOQ Optimizer Demo ===")
    
    # Test EOQ calculation
    annual_demand = 1000
    order_cost = 50
    holding_cost_per_unit = 2.5
    
    eoq = calculate_eoq(annual_demand, order_cost, holding_cost_per_unit)
    print(f"\nEOQ Calculation:")
    print(f"Annual demand: {annual_demand}")
    print(f"Order cost: ${order_cost}")
    print(f"Holding cost per unit: ${holding_cost_per_unit}")
    print(f"Calculated EOQ: {eoq}")
    
    # Test vendor comparison
    vendors = [
        {
            'vendor_id': 'V001',
            'vendor_name': 'Supplier A',
            'price_per_unit': 10.0,
            'order_cost': 50.0,
            'lead_time_days': 7,
            'holding_cost_percentage': 0.25
        },
        {
            'vendor_id': 'V002',
            'vendor_name': 'Supplier B',
            'price_per_unit': 9.5,
            'order_cost': 75.0,
            'lead_time_days': 14,
            'holding_cost_percentage': 0.20
        },
        {
            'vendor_id': 'V003',
            'vendor_name': 'Supplier C',
            'price_per_unit': 11.0,
            'order_cost': 25.0,
            'lead_time_days': 5,
            'holding_cost_percentage': 0.30
        }
    ]
    
    print(f"\nVendor Comparison for annual demand of {annual_demand}:")
    
    # Compare all vendors
    comparison = compare_vendors(vendors, annual_demand)
    
    for i, vendor in enumerate(comparison, 1):
        print(f"\n{i}. {vendor['vendor_name']} ({vendor['vendor_id']}):")
        print(f"   Price per unit: ${vendor['price_per_unit']:.2f}")
        print(f"   EOQ: {vendor['eoq']}")
        print(f"   Total annual cost: ${vendor['total_annual_cost']:.2f}")
        print(f"   Cost breakdown:")
        print(f"     Purchase: ${vendor['cost_breakdown']['purchase_cost']:.2f}")
        print(f"     Ordering: ${vendor['cost_breakdown']['ordering_cost']:.2f}")
        print(f"     Holding: ${vendor['cost_breakdown']['holding_cost']:.2f}")
    
    # Select best vendor
    best_vendor = select_best_vendor(vendors, annual_demand)
    
    if best_vendor:
        print(f"\n🏆 Best Vendor Selection:")
        print(f"Vendor: {best_vendor['vendor_name']} ({best_vendor['vendor_id']})")
        print(f"Optimal EOQ: {best_vendor['eoq']}")
        print(f"Total Annual Cost: ${best_vendor['total_annual_cost']:.2f}")
        print(f"Lead Time: {best_vendor.get('lead_time_days', 'N/A')} days")
    
    # Test edge cases
    print(f"\n=== Edge Case Tests ===")
    print(f"Zero demand EOQ: {calculate_eoq(0, 50, 2.5)}")
    print(f"Zero order cost EOQ: {calculate_eoq(1000, 0, 2.5)}")
    print(f"Empty vendor list: {select_best_vendor([], 1000)}")
    print(f"Zero demand vendor selection: {select_best_vendor(vendors, 0)}")