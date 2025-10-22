# Inventory Pulse

**Intelligent Inventory Management System with AI-Driven Reorder Automation**

Inventory Pulse is an advanced inventory management system that leverages artificial intelligence and the Model Context Protocol (MCP) to automate inventory monitoring, reorder decision-making, and supplier coordination. The system integrates seamlessly with Google Sheets, Notion, and email platforms to provide a comprehensive solution for modern inventory management challenges.

## Problem Statement - Industrial Agents (SMB-focussed)

Inventory Replenishment Copilot – Track stock in Sheets, forecast depletion via LLMs, update Notion reorder plans, and email approvals via Gmail.

## Team Name

NeoMinds

## Team Members

- **Member 1**: Madhur Prakash Mangal - madhurprakash2005@gmail.com
- **Member 2**: Akshat Arya - akshatarya2507@gmail.com
- **Member 3**: Nidhi Singh - nidhisingh5958@gmail.com
- **Member 4**: Ansh Johnson - anshjohnson69@gmail.com

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Core Approach](#core-approach)
- [How It Works](#how-it-works)
- [Key Features](#key-features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

Inventory Pulse addresses the critical challenge of maintaining optimal inventory levels while minimizing costs and preventing stockouts. The system employs a sophisticated multi-layered approach that combines real-time data analysis, predictive modeling, and automated decision-making to streamline inventory operations.

### Problem Statement

Traditional inventory management systems often suffer from:
- Manual monitoring processes prone to human error
- Reactive rather than proactive reorder strategies
- Lack of integration between different business systems
- Insufficient visibility into decision-making rationale
- Time-consuming approval workflows

### Solution Approach

Inventory Pulse solves these challenges through:
- **Automated Monitoring**: Continuous surveillance of inventory levels across all SKUs
- **Predictive Analytics**: AI-driven demand forecasting and trend analysis
- **Intelligent Decision Making**: Economic Order Quantity (EOQ) optimization with vendor selection
- **Unified Integration**: Seamless connectivity across Google Sheets, Notion, and email systems
- **Transparent Workflows**: Clear audit trails and decision rationale for all actions

## System Architecture

### High-Level Architecture

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

### Component Architecture

The system is built on a modular architecture with clear separation of concerns:

**1. Agent Main Controller**
- Orchestrates the entire inventory management workflow
- Implements the core business logic and decision-making processes
- Manages data flow between different system components
- Handles error recovery and fallback mechanisms

**2. MCP Integration Layer**
- Provides unified access to external services through the Model Context Protocol
- Standardizes communication patterns across different APIs
- Enables seamless switching between different service providers
- Maintains consistent data formats and error handling

**3. Business Logic Layer**
- Implements reorder policies and optimization algorithms
- Performs Economic Order Quantity (EOQ) calculations
- Generates AI-powered rationale for decisions
- Manages vendor selection and cost optimization

**4. Data Integration Layer**
- Connects to Google Sheets for inventory data management
- Integrates with Notion for workflow and documentation
- Handles email communications for approvals and notifications
- Manages supplier API interactions for order placement

## Core Approach

### 1. Data-Driven Decision Making

Inventory Pulse employs a sophisticated data analysis approach that considers multiple factors:

**Inventory Metrics Analysis**
- Current stock levels and consumption rates
- Historical demand patterns and seasonality
- Lead times and supplier reliability metrics
- Cost structures and pricing variations

**Predictive Modeling**
- Time-series forecasting for demand prediction
- Trend analysis for identifying consumption patterns
- Seasonal adjustment for cyclical inventory needs
- Risk assessment for stockout probability

### 2. Economic Optimization

The system implements advanced optimization algorithms to minimize total inventory costs:

**Economic Order Quantity (EOQ) Calculation**
```
EOQ = √(2 × Annual Demand × Ordering Cost / Holding Cost)
```

**Total Cost Optimization**
- Balances ordering costs against holding costs
- Considers quantity discounts and bulk pricing
- Factors in storage limitations and cash flow constraints
- Optimizes across multiple suppliers and vendors

### 3. Intelligent Automation

The automation framework is designed with multiple layers of intelligence:

**Rule-Based Automation**
- Configurable thresholds for automatic reordering
- Business rules for vendor selection and approval routing
- Safety stock calculations based on demand variability
- Lead time adjustments for supplier performance

**AI-Enhanced Decision Making**
- Large Language Model (LLM) integration for rationale generation
- Natural language explanations for all reorder decisions
- Context-aware recommendations based on business conditions
- Continuous learning from historical decision outcomes

### 4. Workflow Integration

The system seamlessly integrates with existing business workflows:

**Google Sheets Integration**
- Real-time inventory data synchronization
- Automated updates of stock levels and reorder status
- Historical tracking of inventory movements
- Customizable reporting and dashboard views

**Notion Workflow Management**
- Structured documentation of reorder decisions
- Approval workflow tracking and status updates
- Searchable knowledge base of inventory actions
- Team collaboration and communication tools

**Email-Based Approvals**
- Automated generation of approval requests
- Embedded approve/reject links for quick decisions
- Detailed rationale and supporting data in notifications
- Audit trail of all approval activities

## How It Works

### Phase 1: Inventory Monitoring and Analysis

**1.1 Data Collection**
The system continuously monitors inventory levels by:
- Fetching current stock data from Google Sheets via MCP connector
- Retrieving historical consumption patterns and trends
- Collecting supplier information including pricing and lead times
- Gathering external factors such as seasonal demand indicators

**1.2 Demand Forecasting**
Advanced analytics engine processes the collected data to:
- Generate demand forecasts using time-series analysis
- Identify consumption trends and seasonal patterns
- Calculate demand variability and uncertainty metrics
- Predict future inventory requirements with confidence intervals

**1.3 Risk Assessment**
The system evaluates inventory risks by:
- Calculating stockout probability based on current levels
- Assessing supplier reliability and lead time variability
- Identifying critical SKUs with high business impact
- Evaluating market conditions and external risk factors

### Phase 2: Reorder Decision Engine

**2.1 Policy Evaluation**
The reorder policy engine determines when action is needed by:
- Comparing current stock levels against reorder points
- Evaluating safety stock requirements based on demand variability
- Considering lead times and supplier performance metrics
- Applying business rules and constraints for decision making

**2.2 Economic Optimization**
When reorder is triggered, the EOQ optimizer:
- Calculates optimal order quantities to minimize total costs
- Evaluates multiple suppliers and pricing structures
- Considers quantity discounts and bulk pricing opportunities
- Balances ordering costs against inventory holding costs

**2.3 Vendor Selection**
The intelligent vendor selection process:
- Compares pricing across multiple suppliers
- Evaluates supplier reliability and performance history
- Considers lead times and delivery capabilities
- Factors in payment terms and relationship quality

### Phase 3: Workflow Orchestration

**3.1 Documentation Generation**
For each reorder decision, the system:
- Creates detailed Notion pages with complete rationale
- Generates AI-powered explanations for decision logic
- Documents all relevant data and calculations
- Provides links to supporting information and historical context

**3.2 Approval Workflow**
The approval process involves:
- Generating comprehensive approval emails with embedded decision data
- Routing requests to appropriate managers based on cost thresholds
- Providing one-click approve/reject functionality via secure links
- Tracking approval status and maintaining audit trails

**3.3 Order Execution**
Upon approval, the system:
- Automatically places orders with selected suppliers via API
- Updates inventory systems with pending order information
- Schedules follow-up activities and delivery tracking
- Notifies relevant stakeholders of order placement

### Phase 4: Continuous Monitoring and Learning

**4.1 Status Tracking**
The system continuously monitors:
- Order status and delivery progress
- Inventory level changes and consumption patterns
- Supplier performance and delivery accuracy
- System performance and decision quality metrics

**4.2 Performance Analysis**
Regular analysis includes:
- Comparing actual outcomes against predictions
- Measuring cost savings and efficiency improvements
- Identifying areas for optimization and enhancement
- Generating performance reports and recommendations

**4.3 System Optimization**
Based on performance data, the system:
- Adjusts forecasting models and parameters
- Refines reorder policies and thresholds
- Updates supplier ratings and preferences
- Improves decision-making algorithms and processes

## Key Features

### Intelligent Automation
- **Automated Inventory Monitoring**: Continuous surveillance of stock levels across all SKUs
- **Predictive Reorder Triggers**: AI-driven identification of reorder needs before stockouts occur
- **Economic Order Quantity Optimization**: Automated calculation of optimal order quantities
- **Intelligent Vendor Selection**: Multi-criteria supplier evaluation and selection

### Seamless Integration
- **Google Sheets Connectivity**: Real-time synchronization with existing inventory spreadsheets
- **Notion Workflow Management**: Structured documentation and approval workflows
- **Email-Based Approvals**: Streamlined approval process with embedded decision links
- **MCP Protocol Support**: Unified integration framework for extensibility

### Advanced Analytics
- **Demand Forecasting**: Time-series analysis and trend prediction
- **Cost Optimization**: Total cost minimization across ordering and holding costs
- **Risk Assessment**: Stockout probability and supplier reliability analysis
- **Performance Metrics**: Comprehensive tracking and reporting capabilities

### Transparency and Auditability
- **AI-Generated Rationale**: Natural language explanations for all decisions
- **Complete Audit Trails**: Full documentation of all actions and decisions
- **Decision Transparency**: Clear visibility into decision-making logic and data
- **Historical Analysis**: Comprehensive tracking of system performance over time

## Installation

### Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account with Sheets API enabled
- Notion workspace with integration capabilities
- Email account with SMTP access (Gmail recommended)
- MCP server setup (optional but recommended)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd iit
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Environment Setup

```bash
cp .env.example .env
# Edit .env with your configuration values
```

### Step 4: Credential Configuration

Create the credentials directory and add your service account files:

```bash
mkdir -p credentials
# Add your Google Sheets service account JSON file
# Add any other required credential files
```

### Step 5: Initial Setup

```bash
# Test Google Sheets connection
python tests/test_sheets_connector.py

# Test Notion integration
python tests/test_notion_connector.py

# Test email functionality
python tests/test_email_connector.py
```

## Configuration

### Environment Variables

The system requires several environment variables for proper operation:

#### Core Configuration
```bash
# MCP Server Configuration
MCP_SERVER_URL=http://localhost:3000

# Google Sheets Integration
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SHEETS_CREDENTIALS_JSON=./credentials/google_sheets_service_account.json

# Notion Integration
NOTION_TOKEN=your_notion_integration_token
NOTION_DB_ID=your_notion_database_id

# Email Configuration
GMAIL_USER=your_email@gmail.com
GMAIL_PASSWORD_OR_TOKEN=your_app_password
MANAGER_EMAIL=manager@company.com

# Optional Supplier Integration
SUPPLIER_API_KEY=your_supplier_api_key
SUPPLIER_API_BASE_URL=https://api.supplier.com

# System Configuration
DEMO_MODE=false
LOG_LEVEL=INFO
```

#### Advanced Configuration

```bash
# Reorder Policy Settings
AUTO_ORDER_THRESHOLD=500.0
VENDOR_TRUST_THRESHOLD=0.8
SAFETY_STOCK_MULTIPLIER=1.5

# Economic Optimization
HOLDING_COST_RATE=0.25
ORDERING_COST_DEFAULT=50.0
DISCOUNT_THRESHOLD=1000.0

# Notification Settings
BATCH_APPROVAL_ENABLED=true
NOTIFICATION_FREQUENCY=daily
ESCALATION_TIMEOUT=24
```

### Google Sheets Setup

1. **Create Service Account**
   - Go to Google Cloud Console
   - Create a new service account
   - Download the JSON credentials file
   - Place in `credentials/` directory

2. **Enable APIs**
   - Enable Google Sheets API
   - Enable Google Drive API (for file access)

3. **Share Spreadsheet**
   - Share your inventory spreadsheet with the service account email
   - Grant "Editor" permissions

4. **Configure Sheet Structure**
   - Ensure required columns: SKU, Current Stock, Reorder Point, etc.
   - Follow the provided template structure

### Notion Setup

1. **Create Integration**
   - Go to Notion Developers page
   - Create a new integration
   - Copy the integration token

2. **Setup Database**
   - Create a new database in Notion
   - Add required properties (see database schema)
   - Share database with your integration

3. **Configure Properties**
   - SKU (Title)
   - Current Stock (Number)
   - Reorder Quantity (Number)
   - Total Cost (Number)
   - Status (Select)
   - Rationale (Rich Text)

### Email Configuration

1. **Gmail Setup**
   - Enable 2-Factor Authentication
   - Generate App Password
   - Use App Password in configuration

2. **SMTP Configuration**
   - Server: smtp.gmail.com
   - Port: 587
   - Security: TLS

3. **Alternative Email Providers**
   - Configure SMTP settings for your provider
   - Update email connector configuration

## Usage

### Starting the System

#### MCP Mode (Recommended)
```bash
# Start MCP server (if using external MCP server)
# Follow MCP server documentation

# Start the main agent
python src/agent_main.py
```

#### Legacy Mode
```bash
# Set environment variable to use legacy connectors
export USE_LEGACY_CONNECTORS=true

# Start the main agent
python src/agent_main.py
```

#### Demo Mode
```bash
# Enable demo mode for testing
export DEMO_MODE=true

# Start the agent (outputs will be saved to demo/ directory)
python src/agent_main.py
```

### Webhook Server

For handling approval responses, start the webhook server:

```bash
# Start webhook server
python -m uvicorn src.webhook.app:app --host 0.0.0.0 --port 8000 --reload
```

### Running Specific Components

#### Test Individual Connectors
```bash
# Test Google Sheets integration
python tests/test_sheets_connector.py

# Test Notion integration
python tests/test_notion_connector.py

# Test email functionality
python tests/test_email_connector.py
```

#### Test MCP Integration
```bash
# Test MCP connectivity
python tests/test_mcp_integration.py

# Test specific MCP tools
python tests/test_mcp_tools.py
```

#### Generate Demo Data
```bash
# Create sample inventory data
python demo/sample_inventory.py

# Populate test database
python demo/populate_demo_data.py
```

## Project Structure

```
inventory-pulse/
├── src/                                    # Source code
│   ├── agent_main.py                      # Main orchestration logic
│   ├── connectors/                        # External service integrations
│   │   ├── unified_mcp_connector.py       # MCP unified interface
│   │   ├── mcp_client.py                 # MCP communication client
│   │   ├── sheets_connector.py           # Google Sheets integration
│   │   ├── notion_connector.py           # Notion integration
│   │   ├── email_connector.py            # Email functionality
│   │   └── supplier_connector.py         # Supplier API integration
│   ├── policies/                          # Business logic
│   │   ├── reorder_policy.py             # Reorder decision logic
│   │   ├── eoq_optimizer.py              # Economic Order Quantity
│   │   └── replenishment_policy.py       # Replenishment strategies
│   ├── models/                            # Data models and AI
│   │   ├── reorder_request.py            # Reorder request model
│   │   ├── forecast.py                   # Demand forecasting
│   │   └── llm_rationale.py              # AI rationale generation
│   ├── utils/                             # Utilities
│   │   ├── config.py                     # Configuration management
│   │   └── logger.py                     # Logging utilities
│   └── webhook/                           # Webhook server
│       └── app.py                        # FastAPI webhook handlers
├── tests/                                 # Test suite
│   ├── test_connectors.py                # Connector tests
│   ├── test_policies.py                  # Policy tests
│   ├── test_models.py                    # Model tests
│   └── test_mcp_integration.py           # MCP integration tests
├── demo/                                  # Demo data and examples
│   ├── outbox/                           # Demo email outputs
│   ├── notion_pages/                     # Demo Notion outputs
│   └── sample_inventory.py               # Sample data generator
├── credentials/                           # API credentials (gitignored)
├── requirements.txt                       # Python dependencies
├── .env.example                          # Environment template
├── FRICTION_LOG.txt                      # Development challenges log
└── README.md                             # This file
```

## Testing

### Comprehensive Test Suite

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Component Testing

```bash
# Test MCP integration
pytest tests/test_mcp_integration.py -v

# Test legacy connectors
pytest tests/test_connectors.py -v

# Test business logic
pytest tests/test_policies.py -v

# Test data models
pytest tests/test_models.py -v
```

### Integration Testing

```bash
# End-to-end MCP integration test
python tests/test_mcp_integration.py

# End-to-end legacy integration test
python tests/test_integration.py

# Webhook server testing
python tests/test_webhook.py
```

### Manual Testing

```bash
# Test with sample data
python demo/sample_inventory.py

# Test email delivery
python tests/test_email_delivery.py

# Test Notion page creation
python tests/test_notion_pages.py
```

## Troubleshooting

### Common Issues and Solutions

#### MCP Integration Problems

**MCP Server Connection Failed**
```bash
# Check MCP server status
curl http://localhost:3000/health

# Verify MCP configuration
python -c "
from src.connectors.unified_mcp_connector import UnifiedMCPConnector
connector = UnifiedMCPConnector(demo_mode=True)
print('MCP connection successful')
"
```

**MCP Tool Not Available**
```bash
# List available MCP tools
python -c "
from src.connectors.mcp_client import MCPClient
client = MCPClient('http://localhost:3000')
tools = client.list_tools()
print('Available tools:', [tool['name'] for tool in tools])
"
```

#### Authentication Issues

**Google Sheets Authentication Failed**
- Verify service account JSON file exists and is valid
- Ensure spreadsheet is shared with service account email
- Check that Google Sheets API is enabled in Google Cloud Console

**Notion Integration Problems**
- Verify integration token has correct permissions
- Ensure database is shared with the integration
- Check that all required properties exist in the database

**Email Authentication Failed**
- Verify Gmail app password is correct (16 characters)
- Ensure 2-Factor Authentication is enabled
- Check SMTP settings and port configuration

#### System Performance Issues

**Slow Response Times**
- Check MCP server performance and connectivity
- Verify database query optimization
- Monitor system resource usage

**Memory Usage Problems**
- Review data processing batch sizes
- Check for memory leaks in long-running processes
- Optimize data structures and algorithms

### Debug Mode

Enable comprehensive debugging:

```bash
# Set debug logging level
export LOG_LEVEL=DEBUG

# Enable MCP debug mode
export MCP_DEBUG=true

# Run with detailed logging
python src/agent_main.py
```

### Log Analysis

```bash
# Check system logs
tail -f logs/agent.log

# Search for specific errors
grep "ERROR" logs/agent.log

# Analyze performance metrics
grep "PERFORMANCE" logs/agent.log
```

## Contributing

We welcome contributions to Inventory Pulse. Please follow these guidelines:

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install development dependencies
4. Set up pre-commit hooks

### Code Standards

- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include unit tests for new functionality
- Maintain backward compatibility

### Pull Request Process

1. Create a feature branch from main
2. Implement your changes with tests
3. Update documentation as needed
4. Submit pull request with detailed description

### Testing Requirements

- All new code must include unit tests
- Integration tests for new connectors
- Performance tests for optimization changes
- Documentation updates for new features

---

**Inventory Pulse** - Intelligent Inventory Management for Modern Businesses

Built with the Model Context Protocol (MCP) for seamless integration and extensibility.