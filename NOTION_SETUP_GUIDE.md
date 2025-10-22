# 📋 Notion Integration Setup Guide

This guide will walk you through setting up a Notion integration for your Inventory Intelligence Tool step by step.

## 🎯 Overview

The Notion integration allows your inventory system to:
- Create reorder pages automatically when stock is low
- Track order status (Pending → Approved → Ordered)
- Store detailed inventory analysis and forecasts
- Manage vendor information and costs

## 📝 Step-by-Step Setup

### Step 1: Create a Notion Integration

1. **Go to Notion Developers**
   - Open your browser and navigate to: https://developers.notion.com
   - Click "Sign in" and log in with your Notion account

2. **Create New Integration**
   - Click "Create new integration" or "New integration"
   - Fill in the integration details:
     - **Name**: `Inventory Intelligence Tool` (or any name you prefer)
     - **Logo**: Optional - you can upload a logo or skip this
     - **Associated workspace**: Select your Notion workspace
   - Click "Submit" or "Create"

3. **Copy Integration Token**
   - After creation, you'll see your integration details
   - Find the "Internal Integration Token" section
   - Click "Show" and copy the token (starts with `secret_`)
   - **⚠️ Keep this token secure - treat it like a password!**

### Step 2: Create Inventory Database

1. **Create New Database**
   - In your Notion workspace, create a new page
   - Type `/database` and select "Table - Full page"
   - Name it "Inventory Reorders" or similar

2. **Set Up Database Properties**
   The system expects these properties (Notion will auto-create them when first used):
   
   | Property Name | Type | Description |
   |---------------|------|-------------|
   | **SKU** | Title | Product SKU/identifier |
   | **Quantity** | Number | Quantity to reorder |
   | **Vendor** | Rich Text | Vendor/supplier name |
   | **Total Cost** | Number | Total cost of order |
   | **EOQ** | Number | Economic Order Quantity |
   | **Status** | Select | Order status (Pending, Approved, Ordered) |
   | **Forecast** | Rich Text | Demand forecast details |
   | **Evidence** | Rich Text | Supporting evidence for reorder |
   | **Order Confirmation** | Rich Text | Order confirmation details |
   | **Created Date** | Created time | Auto-generated |

   **Note**: You don't need to create all these manually - the system will create them automatically when it first creates a page.

### Step 3: Share Database with Integration

1. **Share the Database**
   - In your database page, click the "Share" button (top right)
   - Click "Invite" and search for your integration name
   - Select your integration from the dropdown
   - Make sure it has "Can edit" permissions
   - Click "Invite"

2. **Verify Integration Access**
   - You should see your integration listed under "People with access"
   - It should show as having "Can edit" permissions

### Step 4: Get Database ID

1. **Copy Database URL**
   - While viewing your database, copy the URL from your browser
   - The URL will look like: `https://www.notion.so/your-workspace/DATABASE_ID?v=VIEW_ID`

2. **Extract Database ID**
   - The DATABASE_ID is the 32-character string between the last `/` and the `?`
   - Example: If URL is `https://www.notion.so/myworkspace/a1b2c3d4e5f6789012345678901234ab?v=12345`
   - Then DATABASE_ID is: `a1b2c3d4e5f6789012345678901234ab`
   - **Remove any dashes** if present in the ID

### Step 5: Update Environment Variables

1. **Edit .env File**
   - Open your `.env` file in the project root
   - Replace the placeholder values:

   ```env
   # Notion Configuration
   NOTION_TOKEN=secret_your_actual_integration_token_here
   NOTION_DB_ID=your_actual_32_character_database_id_here
   ```

2. **Example**
   ```env
   # Notion Configuration
   NOTION_TOKEN=secret_1234567890abcdef1234567890abcdef12345678
   NOTION_DB_ID=a1b2c3d4e5f6789012345678901234ab
   ```

### Step 6: Test the Connection

1. **Run Test Script**
   ```bash
   python test_notion_connection.py
   ```

2. **Expected Success Output**
   ```
   🔍 Testing Notion API Connection...
   ==================================================
   NOTION_TOKEN: ✅ Set
   NOTION_DB_ID: ✅ Set

   🔗 Initializing Notion client...
   📋 Testing API access...
   ✅ Connected as: Your Name (person)

   📊 Testing database access...
   ✅ Database found: Inventory Reorders
      Created: 2024-01-15T10:30:00.000Z
      Last edited: 2024-01-15T10:30:00.000Z

   📝 Database Properties (10 found):
      • SKU: title
      • Quantity: number
      • Vendor: rich_text
      • Total Cost: number
      • EOQ: number
      • Status: select
      • Forecast: rich_text
      • Evidence: rich_text
      • Order Confirmation: rich_text
      • Created Date: created_time

   🔍 Testing database query...
   ✅ Query successful: Found 0 pages (showing max 5)
      (No pages found in database)

   ✅ Notion connection test completed successfully!
   ```

## 🔧 Troubleshooting

### Common Issues

1. **"Invalid token" Error**
   - Double-check your NOTION_TOKEN starts with `secret_`
   - Make sure you copied the entire token
   - Verify the token hasn't expired

2. **"Database not found" Error**
   - Verify the DATABASE_ID is exactly 32 characters
   - Remove any dashes from the ID
   - Make sure you shared the database with your integration

3. **"Insufficient permissions" Error**
   - Ensure your integration has "Can edit" permissions
   - Re-share the database with your integration

4. **"Integration not found" Error**
   - Make sure you're searching for the exact integration name
   - Try refreshing the share dialog

### Getting Help

If you encounter issues:
1. Check the error message in the test script output
2. Verify each step was completed correctly
3. Try creating a new integration if the token seems invalid
4. Ensure your Notion workspace allows integrations

## 🎉 Next Steps

Once your test passes:
1. Your Notion integration is ready!
2. The inventory system will automatically create reorder pages
3. You can manually test by running the inventory agent
4. Check your Notion database for new reorder entries

## 📚 Additional Resources

- [Notion API Documentation](https://developers.notion.com/docs)
- [Notion Integration Guide](https://developers.notion.com/docs/getting-started)
- [Database Properties Reference](https://developers.notion.com/reference/property-object)