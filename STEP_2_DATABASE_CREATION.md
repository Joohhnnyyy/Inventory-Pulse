# Step 2: Create Your Inventory Database - Detailed Guide

## 🎯 Overview
You'll create a Notion database called "Inventory Reorders" that will store all your inventory reorder information with specific properties that match your system's requirements.

---

## 📋 Step-by-Step Instructions

### 2.1 Create the Database

1. **Open Notion** and navigate to your workspace
2. **Click the "+" button** or press `Ctrl/Cmd + N` to create a new page
3. **Type `/database`** and select "Table - Full page"
4. **Name your database**: `Inventory Reorders`
5. **Press Enter** to create the database

### 2.2 Set Up Required Properties

Your database needs these exact properties. **Follow this order** to avoid confusion:

#### Property 1: SKU (Title Property)
- **Already exists** as "Name" - rename it to "SKU"
- **Type**: Title
- **Purpose**: Unique product identifier

#### Property 2: Quantity
1. Click **"+ Add a property"**
2. **Name**: `Quantity`
3. **Type**: Number
4. **Format**: Number (no decimal places)

#### Property 3: Vendor
1. Click **"+ Add a property"**
2. **Name**: `Vendor`
3. **Type**: Text

#### Property 4: Total Cost
1. Click **"+ Add a property"**
2. **Name**: `Total Cost`
3. **Type**: Number
4. **Format**: Currency (USD)

#### Property 5: EOQ (Economic Order Quantity)
1. Click **"+ Add a property"**
2. **Name**: `EOQ`
3. **Type**: Number
4. **Format**: Number (no decimal places)

#### Property 6: Status
1. Click **"+ Add a property"**
2. **Name**: `Status`
3. **Type**: Select
4. **Add these options** (click "Create" for each):
   - `Pending` (🟡 Yellow)
   - `Approved` (🟢 Green)
   - `Ordered` (🔵 Blue)
   - `Received` (✅ Green)
   - `Cancelled` (🔴 Red)

#### Property 7: Forecast
1. Click **"+ Add a property"**
2. **Name**: `Forecast`
3. **Type**: Text

#### Property 8: Evidence
1. Click **"+ Add a property"**
2. **Name**: `Evidence`
3. **Type**: Text

#### Property 9: Order Confirmation
1. Click **"+ Add a property"**
2. **Name**: `Order Confirmation`
3. **Type**: Text

#### Property 10: Priority
1. Click **"+ Add a property"**
2. **Name**: `Priority`
3. **Type**: Select
4. **Add these options**:
   - `Critical` (🔴 Red)
   - `High` (🟠 Orange)
   - `Medium` (🟡 Yellow)
   - `Low` (🟢 Green)

#### Property 11: Supplier Contact
1. Click **"+ Add a property"**
2. **Name**: `Supplier Contact`
3. **Type**: Email

#### Property 12: Created (Auto-generated)
1. Click **"+ Add a property"**
2. **Name**: `Created`
3. **Type**: Created time
4. **Format**: Date & time

---

## 🎨 Create Useful Views

### View 1: All Orders (Default)
- **Already exists** - just rename the default view
- Shows all records

### View 2: Pending Orders
1. Click **"+ Add a view"**
2. **Name**: `Pending Orders`
3. **Type**: Table
4. **Filter**: Status equals "Pending"
5. **Sort**: Priority (Critical → Low), then Created (Newest first)

### View 3: Approved Orders
1. Click **"+ Add a view"**
2. **Name**: `Approved Orders`
3. **Type**: Table
4. **Filter**: Status equals "Approved"
5. **Sort**: Created (Newest first)

### View 4: Status Board
1. Click **"+ Add a view"**
2. **Name**: `Status Board`
3. **Type**: Board
4. **Group by**: Status
5. **Sort**: Priority, then Created

---

## 📝 Create a Template (Optional but Recommended)

1. Click the **"⌄" dropdown** next to "New" button
2. Select **"+ New template"**
3. **Name**: `Standard Reorder`
4. **Fill in default values**:
   - Status: Pending
   - Priority: Medium
   - Created: (auto-filled)
5. **Save template**

---

## ⚙️ Configure Database Settings

1. Click the **"•••" menu** in the top-right of your database
2. Select **"Database settings"**
3. **Configure**:
   - **Show properties in cards**: Enable for Status, Priority, Vendor
   - **Card preview**: Show first property (SKU)
   - **Card size**: Medium

---

## 🔗 Get Your Database ID

**This is crucial for the integration!**

1. **Copy the database URL** from your browser address bar
2. **Extract the ID**: It's the long string of characters after the last `/` and before any `?`

**Example**:
- URL: `https://www.notion.so/yourworkspace/Inventory-Reorders-a1b2c3d4e5f6789012345678901234567890?v=...`
- Database ID: `a1b2c3d4e5f6789012345678901234567890`

**Clean format** (remove dashes): `a1b2c3d4e5f6789012345678901234567890`

---

## ✅ Verification Checklist

Before proceeding, make sure you have:

- [ ] Database named "Inventory Reorders"
- [ ] All 12 properties created with correct types
- [ ] Status select options: Pending, Approved, Ordered, Received, Cancelled
- [ ] Priority select options: Critical, High, Medium, Low
- [ ] At least 2-3 views created
- [ ] Database ID copied and ready
- [ ] Database is in your workspace (not someone else's)

---

## 🎯 What's Next?

After completing this step:

1. **Share the database** with your integration (Step 3)
2. **Update your .env file** with the database ID
3. **Test the connection** using the provided scripts

---

## 🆘 Troubleshooting

**Problem**: Can't find "Add a property" button
- **Solution**: Make sure you're in the database view, not a page view

**Problem**: Select options not saving
- **Solution**: Press Enter after typing each option name

**Problem**: Database ID looks wrong
- **Solution**: Make sure you're copying from the database URL, not a page URL

**Problem**: Properties appear in wrong order
- **Solution**: Drag and drop property headers to reorder them

---

## 💡 Pro Tips

1. **Use consistent naming**: Stick to the exact property names listed
2. **Test with sample data**: Add 1-2 test records to verify everything works
3. **Bookmark the database**: You'll be accessing it frequently
4. **Set up notifications**: Configure Notion to notify you of status changes

---

Ready to proceed to Step 3? You'll need your Database ID from this step!