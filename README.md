# 🏭 Inventory Intelligence Tool (IIT)

An AI-powered inventory management system that automates reorder decisions, integrates with Notion for workflow management, and provides intelligent forecasting with email approval workflows.

## 🎯 Overview

The Inventory Intelligence Tool is a comprehensive solution for automated inventory management that combines:

- **🤖 AI-Powered Decision Making**: Intelligent reorder recommendations with LLM-generated rationale
- **📊 Multi-Platform Integration**: Google Sheets, Notion, and Email connectors
- **🔄 Automated Workflows**: From inventory monitoring to supplier order placement
- **✅ Approval System**: Email-based approval workflows with webhook handling
- **📈 Forecasting**: Advanced inventory forecasting and EOQ optimization
- **🔧 Composio Integration**: Production-ready integrations with Gmail and Notion

## 🚀 Features

### Core Functionality
- **Automated Inventory Monitoring**: Continuous monitoring of stock levels from Google Sheets
- **Intelligent Reorder Decisions**: AI-powered analysis with detailed rationale generation
- **Multi-Channel Notifications**: Email alerts with approve/reject functionality
- **Notion Integration**: Automatic creation and management of reorder pages
- **Supplier Integration**: Automated order placement with trusted suppliers
- **Webhook Server**: FastAPI-based approval handling system

### Connectors
- **📊 Google Sheets Connector**: Read inventory data and update order status
- **📋 Notion Connector**: Create and manage reorder pages with rich formatting
- **📧 Email Connector**: Send approval emails with HTML formatting
- **🏪 Supplier Connector**: Place orders with supplier APIs
- **🔗 Composio Connectors**: Production-ready Gmail and Notion integrations

### Policies & Models
- **📈 Reorder Policy**: Configurable reorder point and quantity calculations
- **🧮 EOQ Optimizer**: Economic Order Quantity optimization
- **🔮 Forecasting Models**: Demand forecasting with trend analysis
- **🤖 LLM Rationale**: AI-generated explanations for reorder decisions

## 📋 Prerequisites

- **Python 3.8+**
- **Google Cloud Project** (for Sheets integration)
- **Notion Account** (for workflow management)
- **Gmail Account** (for email notifications)
- **Composio Account** (for production integrations)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd iit
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```bash
# Composio Configuration
COMPOSIO_API_KEY=your_composio_api_key_here

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_JSON=./credentials/google_sheets_service_account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_google_sheets_spreadsheet_id_here

# Notion Configuration
NOTION_TOKEN=your_notion_integration_token_here
NOTION_DB_ID=your_notion_database_id_here

# Email Configuration
GMAIL_USER=your_email@gmail.com
GMAIL_PASSWORD_OR_TOKEN=your_gmail_app_password_here
MANAGER_EMAIL=manager@company.com

# Supplier Configuration (Optional)
SUPPLIER_API_KEY=your_supplier_api_key_here
SUPPLIER_API_BASE_URL=https://api.supplier.com/v1
```

## ⚙️ Setup Guide

### 1. Google Sheets Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Sheets API

2. **Create Service Account**
   - Go to IAM & Admin > Service Accounts
   - Create new service account
   - Download JSON credentials file
   - Place in `credentials/` directory

3. **Prepare Your Spreadsheet**
   - Create a Google Sheet with inventory data
   - Required columns: SKU, Current Stock, Reorder Point, etc.
   - Share sheet with service account email

### 2. Notion Setup

Follow the detailed [Notion Setup Guide](NOTION_SETUP_GUIDE.md):

1. **Create Notion Integration**
   - Go to [Notion Developers](https://developers.notion.com)
   - Create new integration
   - Copy integration token

2. **Create Inventory Database**
   - Create new database in Notion
   - Set up required properties (SKU, Quantity, Vendor, etc.)
   - Share database with integration

### 3. Composio Setup

1. **Get Composio API Key**
   - Sign up at [Composio](https://composio.dev)
   - Get your API key from dashboard

2. **Connect Gmail Account**
   ```bash
   python composio_gmail_setup.py
   ```

3. **Connect Notion Account**
   ```bash
   python -c "from src.connectors.composio_notion_connector import ComposioNotionConnector; ComposioNotionConnector(demo_mode=False)"
   ```

### 4. Email Configuration

1. **Gmail App Password**
   - Enable 2-factor authentication on Gmail
   - Generate app-specific password
   - Use in `GMAIL_PASSWORD_OR_TOKEN`

2. **Test Email Setup**
   ```bash
   python test_composio_gmail.py
   ```

## 🚀 Usage

### Running the Main Agent

```bash
# Run in production mode
python -m src.agent_main

# Run in dry-run mode (no actual orders)
python -m src.agent_main --dry-run

# Run with custom configuration
python -m src.agent_main --config custom_config.json
```

### Starting the Webhook Server

```bash
# Start the approval webhook server
uvicorn src.webhook.app:app --host 0.0.0.0 --port 8080 --reload
```

### Testing Components

```bash
# Test email delivery
python test_email_delivery.py

# Test Notion connection
python test_notion_connection.py

# Test Composio Gmail integration
python test_composio_gmail.py

# Test alternative email methods
python test_alternative_email.py
```

## 📁 Project Structure

```
iit/
├── src/
│   ├── agent_main.py              # Main orchestrator
│   ├── connectors/                # Integration connectors
│   │   ├── sheets_connector.py    # Google Sheets integration
│   │   ├── notion_connector.py    # Notion integration
│   │   ├── email_connector.py     # Email functionality
│   │   ├── composio_email_connector_class.py  # Composio Gmail
│   │   ├── composio_notion_connector.py       # Composio Notion
│   │   └── supplier_connector.py  # Supplier API integration
│   ├── models/                    # Data models and AI
│   │   ├── forecast.py           # Forecasting models
│   │   └── llm_rationale.py      # AI rationale generation
│   ├── policies/                 # Business logic
│   │   ├── reorder_policy.py     # Reorder decision logic
│   │   ├── eoq_optimizer.py      # Economic Order Quantity
│   │   └── replenishment_policy.py # Replenishment strategies
│   ├── utils/                    # Utilities
│   │   ├── config.py            # Configuration management
│   │   └── logger.py            # Logging setup
│   └── webhook/                  # Webhook server
│       └── app.py               # FastAPI approval server
├── tests/                       # Unit tests
├── demo/                        # Demo data and outputs
├── credentials/                 # API credentials
├── test_*.py                   # Integration tests
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `COMPOSIO_API_KEY` | Composio API key for integrations | Yes |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | Google Sheets spreadsheet ID | Yes |
| `NOTION_TOKEN` | Notion integration token | Yes |
| `NOTION_DB_ID` | Notion database ID | Yes |
| `GMAIL_USER` | Gmail account for sending emails | Yes |
| `GMAIL_PASSWORD_OR_TOKEN` | Gmail app password | Yes |
| `MANAGER_EMAIL` | Email for approval notifications | Yes |
| `AUTO_ORDER_THRESHOLD` | Auto-order threshold amount | No |
| `VENDOR_TRUST_THRESHOLD` | Vendor trust score threshold | No |

### Agent Configuration

The agent supports various configuration options:

```python
# In agent_main.py
auto_order_threshold = 500.0      # Orders below this amount are auto-approved
vendor_trust_threshold = 0.8      # Minimum vendor trust score
```

## 🔄 Workflow

1. **Inventory Monitoring**: Agent reads current stock levels from Google Sheets
2. **Reorder Analysis**: AI analyzes inventory data and generates reorder recommendations
3. **Notion Page Creation**: Creates detailed reorder pages in Notion with rationale
4. **Email Approval**: Sends approval emails to managers with approve/reject links
5. **Webhook Processing**: Handles approval/rejection responses via webhook server
6. **Order Placement**: Places orders with suppliers for approved items
7. **Status Updates**: Updates Google Sheets and Notion with order status

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_connectors.py
pytest tests/test_policies.py
pytest tests/test_models.py
```

### Integration Tests
```bash
# Test email functionality
python test_email_delivery.py

# Test Composio integrations
python test_composio_gmail.py

# Test Notion connection
python test_notion_connection.py
```

## 🐛 Troubleshooting

### Common Issues

#### Email Delivery Problems
- **Check Gmail app password**: Ensure 2FA is enabled and app password is correct
- **Verify Composio connection**: Run `python test_composio_gmail.py`
- **Check spam folder**: Emails might be filtered as spam

#### Notion Integration Issues
- **Verify integration token**: Check token has correct permissions
- **Database permissions**: Ensure database is shared with integration
- **Property names**: Verify database has required properties

#### Google Sheets Access
- **Service account permissions**: Ensure sheet is shared with service account email
- **API enabled**: Verify Google Sheets API is enabled in Google Cloud Console
- **Credentials path**: Check credentials file path is correct

#### Composio Connection Issues
- **API key validity**: Verify Composio API key is active
- **Account connections**: Re-run setup scripts if connections fail
- **Rate limits**: Check if hitting API rate limits

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Log Files

Check log files in:
- `demo/agent_actions.db` - SQLite database with action logs
- `demo/outbox/` - Email outputs in demo mode
- `demo/notion_pages/` - Notion page outputs in demo mode

## 📚 Documentation

- [Notion Setup Guide](NOTION_SETUP_GUIDE.md) - Detailed Notion integration setup
- [Database Setup Guide](NOTION_DATABASE_SETUP.md) - Notion database configuration
- [Database Schema](database_schema.json) - Complete database schema reference

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
1. Check the troubleshooting section above
2. Review existing documentation
3. Run the test scripts to diagnose issues
4. Check log files for detailed error messages

## 🔮 Future Enhancements

- **Machine Learning Models**: Advanced demand forecasting
- **Multi-Supplier Support**: Compare prices across suppliers
- **Mobile App**: Mobile interface for approvals
- **Dashboard**: Real-time inventory dashboard
- **API Integration**: REST API for external systems
- **Slack Integration**: Slack-based approval workflows