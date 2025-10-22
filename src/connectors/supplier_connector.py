"""
Supplier Connector for Automated Order Placement

This module provides functionality to place orders with suppliers, supporting both
real API integration and simulation mode for testing and demo purposes.

Author: Inventory Intelligence Team
Version: 1.0.0
"""

import os
import csv
import json
import logging
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupplierConnector:
    """
    Connector for placing orders with suppliers.
    
    Supports both real API integration and simulation mode.
    """
    
    def __init__(self):
        """Initialize the supplier connector with configuration."""
        self.api_key = os.getenv('SUPPLIER_API_KEY')
        self.api_url = os.getenv('SUPPLIER_API_URL')
        self.demo_mode = not (self.api_key and self.api_url)
        
        # Default vendor lead times (days) for simulation
        self.vendor_lead_times = {
            'acme_supplies': 7,
            'global_parts': 10,
            'quick_ship': 3,
            'bulk_wholesale': 14,
            'premium_vendor': 5
        }
        
        # Setup requests session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        if self.demo_mode:
            logger.info("Supplier connector initialized in DEMO mode - orders will be simulated")
            self._ensure_demo_directory()
        else:
            logger.info("Supplier connector initialized in PRODUCTION mode")
    
    def _ensure_demo_directory(self):
        """Ensure demo directory exists for simulation files."""
        demo_dir = os.path.join(os.getcwd(), 'demo')
        os.makedirs(demo_dir, exist_ok=True)
    
    def _generate_order_id(self) -> str:
        """Generate a unique order ID for simulation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"ORD_{timestamp}_{int(time.time() * 1000) % 10000:04d}"
    
    def _get_vendor_lead_time(self, vendor_id: str) -> int:
        """
        Get lead time for a vendor.
        
        Args:
            vendor_id: Vendor identifier
            
        Returns:
            int: Lead time in days
        """
        # Normalize vendor ID for lookup
        normalized_id = vendor_id.lower().replace(' ', '_').replace('-', '_')
        return self.vendor_lead_times.get(normalized_id, 7)  # Default 7 days
    
    def _simulate_order(self, vendor_id: str, sku: str, qty: int) -> Dict:
        """
        Simulate order placement by writing to CSV file.
        
        Args:
            vendor_id: Vendor identifier
            sku: Product SKU
            qty: Quantity to order
            
        Returns:
            Dict: Simulated order response
        """
        order_id = self._generate_order_id()
        lead_time = self._get_vendor_lead_time(vendor_id)
        estimated_delivery = datetime.now() + timedelta(days=lead_time)
        
        # Prepare order data
        order_data = {
            'order_id': order_id,
            'vendor_id': vendor_id,
            'sku': sku,
            'quantity': qty,
            'order_date': datetime.now().isoformat(),
            'estimated_delivery_date': estimated_delivery.isoformat(),
            'status': 'confirmed',
            'lead_time_days': lead_time
        }
        
        # Write to CSV file
        csv_file = os.path.join('demo', 'supplier_orders.csv')
        file_exists = os.path.exists(csv_file)
        
        try:
            with open(csv_file, 'a', newline='') as f:
                fieldnames = ['order_id', 'vendor_id', 'sku', 'quantity', 'order_date', 
                             'estimated_delivery_date', 'status', 'lead_time_days']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # Write header if file is new
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(order_data)
            
            logger.info(f"Simulated order {order_id} written to {csv_file}")
            
            return {
                'order_id': order_id,
                'estimated_delivery_date': estimated_delivery.strftime('%Y-%m-%d'),
                'status': 'confirmed'
            }
            
        except Exception as e:
            logger.error(f"Failed to write simulated order to CSV: {e}")
            raise
    
    def _place_real_order(self, vendor_id: str, sku: str, qty: int) -> Dict:
        """
        Place real order via API.
        
        Args:
            vendor_id: Vendor identifier
            sku: Product SKU
            qty: Quantity to order
            
        Returns:
            Dict: API response
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'vendor_id': vendor_id,
            'sku': sku,
            'quantity': qty,
            'order_date': datetime.now().isoformat()
        }
        
        try:
            response = self.session.post(
                f"{self.api_url}/orders",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Successfully placed order with vendor {vendor_id} for {qty} units of {sku}")
                return result
            else:
                error_msg = f"API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def place_order(self, vendor_id: str, sku: str, qty: int) -> Dict:
        """
        Place an order with a supplier.
        
        Args:
            vendor_id: Vendor identifier
            sku: Product SKU to order
            qty: Quantity to order
            
        Returns:
            Dict: Order response with fields:
                - order_id: Unique order identifier
                - estimated_delivery_date: Expected delivery date (YYYY-MM-DD)
                - status: Order status
                
        Raises:
            ValueError: If input parameters are invalid
            Exception: If order placement fails after retries
        """
        # Input validation
        if not vendor_id or not isinstance(vendor_id, str):
            raise ValueError("vendor_id must be a non-empty string")
        
        if not sku or not isinstance(sku, str):
            raise ValueError("sku must be a non-empty string")
        
        if not isinstance(qty, int) or qty <= 0:
            raise ValueError("qty must be a positive integer")
        
        logger.info(f"Placing order: Vendor={vendor_id}, SKU={sku}, Qty={qty}")
        
        try:
            if self.demo_mode:
                return self._simulate_order(vendor_id, sku, qty)
            else:
                return self._place_real_order(vendor_id, sku, qty)
                
        except Exception as e:
            logger.error(f"Failed to place order after retries: {e}")
            raise
    
    def get_order_status(self, order_id: str) -> Dict:
        """
        Get status of an existing order.
        
        Args:
            order_id: Order identifier
            
        Returns:
            Dict: Order status information
        """
        if self.demo_mode:
            # In demo mode, read from CSV
            csv_file = os.path.join('demo', 'supplier_orders.csv')
            if not os.path.exists(csv_file):
                raise ValueError(f"Order {order_id} not found")
            
            try:
                with open(csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['order_id'] == order_id:
                            return {
                                'order_id': row['order_id'],
                                'status': row['status'],
                                'estimated_delivery_date': row['estimated_delivery_date'],
                                'vendor_id': row['vendor_id'],
                                'sku': row['sku'],
                                'quantity': int(row['quantity'])
                            }
                    
                raise ValueError(f"Order {order_id} not found")
                
            except Exception as e:
                logger.error(f"Failed to read order status from CSV: {e}")
                raise
        else:
            # Real API call
            headers = {'Authorization': f'Bearer {self.api_key}'}
            response = self.session.get(
                f"{self.api_url}/orders/{order_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to get order status: {response.status_code}")

if __name__ == "__main__":
    """
    Example usage and testing of the supplier connector.
    """
    print("=== Supplier Connector Test ===")
    
    # Initialize connector
    connector = SupplierConnector()
    
    print(f"Mode: {'DEMO' if connector.demo_mode else 'PRODUCTION'}")
    print(f"API URL: {connector.api_url or 'Not configured'}")
    print(f"API Key: {'Configured' if connector.api_key else 'Not configured'}")
    
    # Example order placement
    try:
        print("\n--- Placing Test Order ---")
        order_response = connector.place_order(
            vendor_id="acme_supplies",
            sku="WIDGET-001",
            qty=100
        )
        
        print("Order Response:")
        print(json.dumps(order_response, indent=2))
        
        # Test order status retrieval
        if connector.demo_mode:
            print("\n--- Checking Order Status ---")
            status_response = connector.get_order_status(order_response['order_id'])
            print("Status Response:")
            print(json.dumps(status_response, indent=2))
        
        print("\n--- Placing Second Test Order ---")
        order_response_2 = connector.place_order(
            vendor_id="quick_ship",
            sku="GADGET-002",
            qty=50
        )
        
        print("Second Order Response:")
        print(json.dumps(order_response_2, indent=2))
        
    except Exception as e:
        print(f"Error during testing: {e}")
    
    # Display simulation behavior
    if connector.demo_mode:
        print("\n=== Simulation Behavior ===")
        print("- Orders are written to demo/supplier_orders.csv")
        print("- Order IDs are generated with timestamp and random suffix")
        print("- Delivery dates calculated using vendor-specific lead times:")
        for vendor, days in connector.vendor_lead_times.items():
            print(f"  * {vendor}: {days} days")
        print("- All simulated orders have 'confirmed' status")
        
        # Show CSV file if it exists
        csv_file = os.path.join('demo', 'supplier_orders.csv')
        if os.path.exists(csv_file):
            print(f"\nCurrent contents of {csv_file}:")
            try:
                with open(csv_file, 'r') as f:
                    print(f.read())
            except Exception as e:
                print(f"Error reading CSV: {e}")