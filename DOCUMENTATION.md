# Documentation

**AI inventory automation - Composio + Gemini AI + Redis messaging**

## Navigation

### Setup & Configuration

- **[Installation](#installation)** - Dependencies & environment
- **[Environment](#environment)** - Config & API keys  
- **[Authentication](#authentication)** - OAuth & Composio setup

### Architecture & Design

- **[System Overview](#system-overview)** - Architecture & components
- **[Workflow](#workflow)** - Process flow & steps
- **[Data Flow](#data-flow)** - Data transformations

### API & Development

- **[Services](#services)** - Service layer API
- **[Models](#models)** - Data models & validation
- **[Testing](#testing)** - Test guides & examples

## Quick Start

**Setup**: [Installation](#installation) → [Environment](#environment) → [Authentication](#authentication)  
**Understand**: [Architecture](#system-overview) → [Workflow](#workflow)  
**Develop**: [Services](#services) → [Models](#models) → [Testing](#testing)

---

## Installation

### Dependencies & Environment

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### System Requirements

- Python 3.8+
- Redis server
- Google Cloud credentials
- Composio API access
- Notion API access

---

## Environment

### Config & API Keys

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Configure the following environment variables:

```env
# LLM Configuration
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key

# Google Sheets
GOOGLE_SHEETS_ID=your_sheets_id
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# Notion
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id

# Composio
COMPOSIO_API_KEY=your_composio_api_key

# Gmail
GMAIL_ADDRESS=your_gmail_address

# MCP Configuration
MCP_SERVER_URL=your_mcp_server_url
```

---

## Authentication

### OAuth & Composio Setup

1. **Google Cloud Setup**:
   - Create a Google Cloud project
   - Enable Sheets API and Gmail API
   - Create service account credentials
   - Place credentials in `credentials/` directory

2. **Notion Setup**:
   - Create a Notion integration
   - Get your integration token
   - Share your database with the integration

3. **Composio Setup**:
   - Sign up for Composio account
   - Get your API key
   - Configure OAuth applications

---

## System Overview

### Architecture & Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Inventory Pulse                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   Agent Main    │    │  MCP Server     │    │ External    │  │
│  │   Controller    │◄──►│   Gateway       │◄──►│ Services    │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│           │                       │                      │      │
│           ▼                       ▼                      ▼      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │ Business Logic  │    │ Legacy Fallback │    │ Webhook     │  │
│  │ & Policies      │    │ Connectors      │    │ Server      │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

- **Agent Main**: Central orchestration and decision-making
- **MCP Server**: Model Context Protocol integration
- **Connectors**: External service integrations
- **Policies**: Business logic and optimization algorithms
- **Webhook Server**: Real-time event handling

---

## Workflow

### Process Flow & Steps

1. **Inventory Monitoring**
   - Continuous monitoring of Google Sheets inventory data
   - Real-time stock level tracking
   - Automated threshold detection

2. **Demand Forecasting**
   - AI-powered demand prediction using Gemini
   - Historical data analysis
   - Seasonal trend identification

3. **Reorder Decision Making**
   - Economic Order Quantity (EOQ) calculations
   - Vendor selection optimization
   - Lead time considerations

4. **Notification & Approval**
   - Automated email notifications via Gmail
   - Notion database updates
   - Approval workflow management

5. **Order Processing**
   - Supplier communication
   - Order tracking
   - Inventory updates

---

## Data Flow

### Data Transformations

```
Google Sheets → Data Validation → AI Analysis → Decision Engine → Notion Updates → Email Notifications
      ↓              ↓               ↓              ↓              ↓              ↓
   Raw Data    Structured Data   Predictions   Reorder Plans   Task Updates   Approvals
```

### Data Models

- **Inventory Item**: SKU, quantity, thresholds, vendor info
- **Forecast**: Demand predictions, confidence intervals
- **Reorder Plan**: Quantities, timing, vendor selection
- **Task**: Notion database entries with approval status

---

## Services

### Service Layer API

#### Inventory Service
```python
from src.connectors.sheets_connector import SheetsConnector

# Get inventory data
inventory = SheetsConnector().get_inventory_data()

# Update stock levels
SheetsConnector().update_inventory(sku, new_quantity)
```

#### Notion Service
```python
from src.connectors.notion_connector import NotionConnector

# Create reorder task
NotionConnector().create_reorder_task(item_data, rationale)

# Update task status
NotionConnector().update_task_status(task_id, status)
```

#### Email Service
```python
from src.connectors.email_connector import EmailConnector

# Send approval request
EmailConnector().send_approval_request(reorder_plan)
```

---

## Models

### Data Models & Validation

#### Inventory Item Model
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class InventoryItem:
    sku: str
    on_hand: int
    reorder_point: int
    lead_time_days: int
    vendor_ids: list[str]
    unit_cost: float
    demand_forecast: Optional[float] = None
```

#### Reorder Plan Model
```python
@dataclass
class ReorderPlan:
    sku: str
    recommended_quantity: int
    selected_vendor: str
    estimated_cost: float
    urgency_level: str
    rationale: str
```

---

## Testing

### Test Guides & Examples

#### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_inventory.py

# Run with coverage
python -m pytest --cov=src tests/
```

#### Example Test
```python
import pytest
from src.policies.eoq_optimizer import EOQOptimizer

def test_eoq_calculation():
    optimizer = EOQOptimizer()
    result = optimizer.calculate_eoq(
        annual_demand=1000,
        ordering_cost=50,
        holding_cost=2
    )
    assert result > 0
    assert isinstance(result, int)
```

#### Integration Testing
```python
# Test full workflow
def test_inventory_workflow():
    # Mock data setup
    # Run agent cycle
    # Verify outputs
    pass
```

---

## ⬅️ Back to Main

**[Main README](README.md)** - Project overview & quick start

---

*This documentation is part of the Inventory Pulse project by Team NeoMinds*