"""
Replenishment Policy Module

Contains business logic and decision-making algorithms for inventory replenishment.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import math

from ..utils.config import Config

class ReplenishmentPolicy:
    """
    Policy engine for making inventory replenishment decisions.
    """
    
    def __init__(self, config: Config):
        """Initialize the replenishment policy."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Policy parameters
        self.threshold_percentage = config.inventory_threshold_percentage / 100.0
        self.safety_stock_multiplier = getattr(config, 'safety_stock_multiplier', 1.2)
        self.lead_time_days = getattr(config, 'default_lead_time_days', 7)
        
        self.logger.info("Replenishment policy initialized")
    
    def identify_low_stock(self, inventory_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify items that are below the reorder threshold.
        
        Args:
            inventory_data: List of inventory items
            
        Returns:
            List of items that need replenishment
        """
        low_stock_items = []
        
        for item in inventory_data:
            if self._is_low_stock(item):
                low_stock_items.append(item)
                self.logger.info(f"Low stock identified: {item.get('name', 'Unknown')} "
                               f"(Current: {item.get('current_stock', 0)}, "
                               f"Minimum: {item.get('minimum_stock', 0)})")
        
        return low_stock_items
    
    def _is_low_stock(self, item: Dict[str, Any]) -> bool:
        """
        Check if an item is below the reorder threshold.
        
        Args:
            item: Inventory item data
            
        Returns:
            True if item needs replenishment
        """
        current_stock = item.get('current_stock', 0)
        minimum_stock = item.get('minimum_stock', 0)
        
        # Skip if item is inactive or already being reordered
        status = item.get('status', 'active').lower()
        if status in ['inactive', 'reorder_pending', 'discontinued']:
            return False
        
        # Check if current stock is below minimum threshold
        if current_stock <= minimum_stock:
            return True
        
        # Check if current stock is below percentage threshold of maximum
        maximum_stock = item.get('maximum_stock', 0)
        if maximum_stock > 0:
            threshold_level = maximum_stock * self.threshold_percentage
            if current_stock <= threshold_level:
                return True
        
        return False
    
    def calculate_order_quantity(self, item: Dict[str, Any]) -> int:
        """
        Calculate the optimal order quantity for an item.
        
        Args:
            item: Inventory item data
            
        Returns:
            Recommended order quantity
        """
        current_stock = item.get('current_stock', 0)
        minimum_stock = item.get('minimum_stock', 0)
        maximum_stock = item.get('maximum_stock', 0)
        
        # Method 1: Simple reorder to maximum
        if maximum_stock > 0:
            basic_quantity = maximum_stock - current_stock
        else:
            # Fallback: order enough to reach 3x minimum stock
            basic_quantity = (minimum_stock * 3) - current_stock
        
        # Method 2: Economic Order Quantity (EOQ) consideration
        eoq_quantity = self._calculate_eoq(item)
        
        # Method 3: Safety stock consideration
        safety_quantity = self._calculate_safety_stock(item)
        
        # Choose the maximum of the three methods to ensure adequate stock
        recommended_quantity = max(basic_quantity, eoq_quantity, safety_quantity)
        
        # Ensure minimum order quantity
        min_order_qty = item.get('minimum_order_quantity', 1)
        recommended_quantity = max(recommended_quantity, min_order_qty)
        
        # Round up to nearest order unit if specified
        order_unit = item.get('order_unit', 1)
        if order_unit > 1:
            recommended_quantity = math.ceil(recommended_quantity / order_unit) * order_unit
        
        self.logger.info(f"Calculated order quantity for {item.get('name', 'Unknown')}: {recommended_quantity}")
        
        return int(recommended_quantity)
    
    def _calculate_eoq(self, item: Dict[str, Any]) -> int:
        """
        Calculate Economic Order Quantity (EOQ).
        
        Args:
            item: Inventory item data
            
        Returns:
            EOQ-based order quantity
        """
        try:
            # Get parameters for EOQ calculation
            annual_demand = item.get('annual_demand', 0)
            unit_cost = item.get('unit_cost', 0.0)
            holding_cost_rate = getattr(self.config, 'holding_cost_rate', 0.25)  # 25% per year
            order_cost = getattr(self.config, 'order_cost', 50.0)  # $50 per order
            
            if annual_demand <= 0 or unit_cost <= 0:
                return 0
            
            # EOQ formula: sqrt((2 * D * S) / (H * C))
            # D = annual demand, S = order cost, H = holding cost rate, C = unit cost
            holding_cost = holding_cost_rate * unit_cost
            
            eoq = math.sqrt((2 * annual_demand * order_cost) / holding_cost)
            
            return int(eoq)
            
        except Exception as e:
            self.logger.warning(f"Could not calculate EOQ for {item.get('name', 'Unknown')}: {str(e)}")
            return 0
    
    def _calculate_safety_stock(self, item: Dict[str, Any]) -> int:
        """
        Calculate safety stock based on demand variability and lead time.
        
        Args:
            item: Inventory item data
            
        Returns:
            Safety stock quantity
        """
        try:
            # Get demand and lead time parameters
            average_daily_demand = item.get('average_daily_demand', 0)
            demand_std_dev = item.get('demand_std_deviation', 0)
            lead_time_days = item.get('lead_time_days', self.lead_time_days)
            service_level = getattr(self.config, 'service_level', 0.95)  # 95% service level
            
            if average_daily_demand <= 0:
                return 0
            
            # Z-score for service level (95% = 1.645, 99% = 2.33)
            z_score = 1.645 if service_level >= 0.95 else 1.28
            
            # Safety stock = Z * sqrt(lead_time) * demand_std_dev
            if demand_std_dev > 0:
                safety_stock = z_score * math.sqrt(lead_time_days) * demand_std_dev
            else:
                # Fallback: use percentage of average demand
                safety_stock = average_daily_demand * lead_time_days * 0.2  # 20% buffer
            
            return int(safety_stock * self.safety_stock_multiplier)
            
        except Exception as e:
            self.logger.warning(f"Could not calculate safety stock for {item.get('name', 'Unknown')}: {str(e)}")
            return 0
    
    def should_expedite_order(self, item: Dict[str, Any]) -> bool:
        """
        Determine if an order should be expedited based on criticality.
        
        Args:
            item: Inventory item data
            
        Returns:
            True if order should be expedited
        """
        current_stock = item.get('current_stock', 0)
        minimum_stock = item.get('minimum_stock', 0)
        
        # Expedite if stock is critically low (below 50% of minimum)
        critical_threshold = minimum_stock * 0.5
        
        if current_stock <= critical_threshold:
            return True
        
        # Expedite if item is marked as critical
        if item.get('is_critical', False):
            return True
        
        # Expedite if item has high priority
        priority = item.get('priority', 'normal').lower()
        if priority in ['high', 'critical', 'urgent']:
            return True
        
        return False
    
    def get_reorder_recommendations(self, inventory_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive reorder recommendations.
        
        Args:
            inventory_data: List of all inventory items
            
        Returns:
            Dictionary with recommendations and analytics
        """
        low_stock_items = self.identify_low_stock(inventory_data)
        
        recommendations = {
            'timestamp': datetime.now(),
            'total_items_analyzed': len(inventory_data),
            'items_needing_reorder': len(low_stock_items),
            'reorder_items': [],
            'expedited_items': [],
            'total_estimated_cost': 0.0
        }
        
        for item in low_stock_items:
            order_qty = self.calculate_order_quantity(item)
            is_expedited = self.should_expedite_order(item)
            estimated_cost = order_qty * item.get('unit_cost', 0.0)
            
            reorder_item = {
                'item': item,
                'recommended_quantity': order_qty,
                'estimated_cost': estimated_cost,
                'is_expedited': is_expedited,
                'priority': item.get('priority', 'normal')
            }
            
            recommendations['reorder_items'].append(reorder_item)
            recommendations['total_estimated_cost'] += estimated_cost
            
            if is_expedited:
                recommendations['expedited_items'].append(reorder_item)
        
        return recommendations