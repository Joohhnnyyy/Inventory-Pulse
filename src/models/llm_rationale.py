"""
LLM Rationale Generator for Inventory Management

This module provides LLM-powered rationale generation for inventory reorder decisions.
It supports both real LLM calls (OpenAI/Composio) and deterministic fallback for demo mode.

Author: Inventory Intelligence Team
Version: 1.0.0
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Explicit prompt template for transparency
RATIONALE_PROMPT_TEMPLATE = """
You are an inventory management expert analyzing a reorder decision. Based on the provided context, generate a clear rationale explaining why this item needs reordering.

CONTEXT:
- SKU: {sku}
- Current Stock: {on_hand} units
- Weekly Demand: {weekly_demand} units
- Predicted Stockout Date: {stockout_date}
- Best Vendor: {vendor_name} (EOQ: {eoq} units, Total Cost: ${total_cost:.2f})
- Last 90 Days Stats: Average Daily Usage: {avg_daily:.2f} units, Standard Deviation: {stddev:.2f}

Please provide:
1. A paragraph explaining the reorder rationale (2-3 sentences)
2. 3-4 bullet points highlighting key factors

Format your response as JSON:
{{
    "paragraph": "Your paragraph explanation here",
    "bullets": ["Bullet point 1", "Bullet point 2", "Bullet point 3", "Bullet point 4"]
}}
"""

def call_llm(prompt: str) -> str:
    """
    Call LLM service with fallback to deterministic response.
    
    Supports Groq API and OpenAI API. Falls back to template-based response
    if no API keys are available.
    
    Args:
        prompt: The prompt to send to the LLM
        
    Returns:
        str: LLM response or deterministic fallback
    """
    # Try Groq first
    groq_key = os.getenv('GROQ_API_KEY')
    if groq_key:
        try:
            headers = {
                'Authorization': f'Bearer {groq_key}',
                'Content-Type': 'application/json'
            }
            
            model = os.getenv('LLM_MODEL', 'llama-3.3-70b-versatile')
            
            payload = {
                'model': model,
                'messages': [
                    {'role': 'system', 'content': 'You are an inventory management expert. Respond only with valid JSON.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 500,
                'temperature': 0.3
            }
            
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                logger.warning(f"Groq API error: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Groq API call failed: {e}")
    
    # Try OpenAI as fallback
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        try:
            headers = {
                'Authorization': f'Bearer {openai_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': 'You are an inventory management expert. Respond only with valid JSON.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 500,
                'temperature': 0.3
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                logger.warning(f"OpenAI API error: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}")
    
    # Try Composio
    composio_key = os.getenv('COMPOSIO_API_KEY')
    if composio_key:
        try:
            # Composio API implementation would go here
            # For now, fall through to deterministic fallback
            logger.info("Composio integration not yet implemented, using fallback")
        except Exception as e:
            logger.warning(f"Composio API call failed: {e}")
    
    # Deterministic fallback
    logger.info("Using deterministic fallback for LLM rationale generation")
    return _generate_deterministic_rationale(prompt)

def _generate_deterministic_rationale(prompt: str) -> str:
    """
    Generate deterministic rationale based on prompt context.
    
    Args:
        prompt: The original prompt containing context
        
    Returns:
        str: JSON-formatted deterministic response
    """
    # Extract key information from prompt for template
    lines = prompt.split('\n')
    context = {}
    
    for line in lines:
        if 'SKU:' in line:
            context['sku'] = line.split('SKU:')[1].strip()
        elif 'Current Stock:' in line:
            context['on_hand'] = line.split('Current Stock:')[1].split('units')[0].strip()
        elif 'Weekly Demand:' in line:
            context['weekly_demand'] = line.split('Weekly Demand:')[1].split('units')[0].strip()
        elif 'Predicted Stockout Date:' in line:
            context['stockout_date'] = line.split('Predicted Stockout Date:')[1].strip()
        elif 'Best Vendor:' in line:
            vendor_info = line.split('Best Vendor:')[1].strip()
            context['vendor_info'] = vendor_info
    
    # Generate deterministic response
    sku = context.get('sku', 'UNKNOWN')
    on_hand = context.get('on_hand', '0')
    weekly_demand = context.get('weekly_demand', '0')
    stockout_date = context.get('stockout_date', 'Unknown')
    vendor_info = context.get('vendor_info', 'Unknown vendor')
    
    paragraph = f"Item {sku} requires immediate reordering due to low stock levels. With only {on_hand} units remaining and weekly demand of {weekly_demand} units, stockout is predicted for {stockout_date}. The recommended vendor offers optimal cost-efficiency for this replenishment."
    
    bullets = [
        f"Current stock ({on_hand} units) is insufficient for projected demand",
        f"Weekly consumption rate of {weekly_demand} units indicates rapid depletion",
        f"Stockout risk identified for {stockout_date}",
        f"Selected vendor provides best total cost optimization: {vendor_info}"
    ]
    
    return json.dumps({
        "paragraph": paragraph,
        "bullets": bullets
    }, indent=2)

def generate_rationale(context: Dict) -> Dict:
    """
    Generate LLM-powered rationale for inventory reorder decisions.
    
    Args:
        context: Dictionary containing:
            - sku: Product SKU
            - on_hand: Current stock level
            - weekly_demand: Projected weekly demand
            - stockout_date: Predicted stockout date
            - best_vendor: Dict with name, EOQ, TotalCost
            - last_90d_stats: Dict with avg_daily, stddev
            
    Returns:
        Dict with fields:
            - paragraph: Explanatory paragraph
            - bullets: List of key bullet points
    """
    try:
        # Validate required context fields
        required_fields = ['sku', 'on_hand', 'weekly_demand', 'stockout_date', 'best_vendor', 'last_90d_stats']
        for field in required_fields:
            if field not in context:
                raise ValueError(f"Missing required context field: {field}")
        
        # Extract context values
        sku = context['sku']
        on_hand = context['on_hand']
        weekly_demand = context['weekly_demand']
        stockout_date = context['stockout_date']
        
        best_vendor = context['best_vendor']
        vendor_name = best_vendor.get('name', 'Unknown')
        eoq = best_vendor.get('EOQ', 0)
        total_cost = best_vendor.get('TotalCost', 0)
        
        stats = context['last_90d_stats']
        avg_daily = stats.get('avg_daily', 0)
        stddev = stats.get('stddev', 0)
        
        # Format the prompt
        prompt = RATIONALE_PROMPT_TEMPLATE.format(
            sku=sku,
            on_hand=on_hand,
            weekly_demand=weekly_demand,
            stockout_date=stockout_date,
            vendor_name=vendor_name,
            eoq=eoq,
            total_cost=total_cost,
            avg_daily=avg_daily,
            stddev=stddev
        )
        
        logger.info(f"Generating rationale for SKU: {sku}")
        
        # Call LLM
        llm_response = call_llm(prompt)
        
        # Parse JSON response
        try:
            rationale = json.loads(llm_response)
            
            # Validate response structure
            if 'paragraph' not in rationale or 'bullets' not in rationale:
                raise ValueError("Invalid LLM response structure")
            
            if not isinstance(rationale['bullets'], list):
                raise ValueError("Bullets must be a list")
            
            logger.info(f"Successfully generated rationale for SKU: {sku}")
            return rationale
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {llm_response}")
            
            # Fallback to deterministic response
            fallback_response = _generate_deterministic_rationale(prompt)
            return json.loads(fallback_response)
            
    except Exception as e:
        logger.error(f"Error generating rationale for SKU {context.get('sku', 'unknown')}: {e}")
        
        # Emergency fallback
        return {
            "paragraph": f"Reorder recommended for {context.get('sku', 'item')} due to low stock levels and projected demand.",
            "bullets": [
                "Current stock levels are below optimal thresholds",
                "Demand forecasting indicates potential stockout risk",
                "Vendor selection optimized for cost efficiency",
                "Immediate action recommended to maintain service levels"
            ]
        }

if __name__ == "__main__":
    """
    Example usage and testing of the LLM rationale generator.
    """
    print("=== LLM Rationale Generator Test ===")
    
    # Example context
    example_context = {
        "sku": "WIDGET-001",
        "on_hand": 25,
        "weekly_demand": 15,
        "stockout_date": "2024-02-15",
        "best_vendor": {
            "name": "Acme Supplies",
            "EOQ": 100,
            "TotalCost": 1250.00
        },
        "last_90d_stats": {
            "avg_daily": 2.1,
            "stddev": 0.8
        }
    }
    
    print(f"Input context: {json.dumps(example_context, indent=2)}")
    print("\n" + "="*50)
    
    # Generate rationale
    try:
        rationale = generate_rationale(example_context)
        
        print("Generated Rationale:")
        print(f"Paragraph: {rationale['paragraph']}")
        print("\nKey Points:")
        for i, bullet in enumerate(rationale['bullets'], 1):
            print(f"{i}. {bullet}")
            
        print(f"\nFull JSON output:")
        print(json.dumps(rationale, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Prompt Template Used ===")
    print("The following prompt template is used for LLM calls:")
    print(RATIONALE_PROMPT_TEMPLATE)