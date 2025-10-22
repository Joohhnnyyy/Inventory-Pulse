# Database Property Reference

## 📊 Quick Property Setup Reference

Copy and paste these exact names when creating your properties:

### Required Properties (in order)

| Property Name | Type | Configuration | Notes |
|---------------|------|---------------|-------|
| `SKU` | Title | Default title property | Rename existing "Name" property |
| `Quantity` | Number | No decimals | How many to order |
| `Vendor` | Text | Plain text | Supplier name |
| `Total Cost` | Number | Currency (USD) | Total order cost |
| `EOQ` | Number | No decimals | Economic Order Quantity |
| `Status` | Select | See options below | Order status |
| `Forecast` | Text | Plain text | Demand forecast |
| `Evidence` | Text | Plain text | Supporting data |
| `Order Confirmation` | Text | Plain text | PO numbers, etc. |
| `Priority` | Select | See options below | Order priority |
| `Supplier Contact` | Email | Email format | Contact email |
| `Created` | Created time | Date & time | Auto-generated |

### Status Select Options
```
Pending     (🟡 Yellow)
Approved    (🟢 Green)
Ordered     (🔵 Blue)
Received    (✅ Green)
Cancelled   (🔴 Red)
```

### Priority Select Options
```
Critical    (🔴 Red)
High        (🟠 Orange)
Medium      (🟡 Yellow)
Low         (🟢 Green)
```

## 🎯 Views to Create

1. **All Orders** (Default view - rename existing)
2. **Pending Orders** (Filter: Status = Pending)
3. **Approved Orders** (Filter: Status = Approved)
4. **Status Board** (Board view, Group by Status)

## 📋 Sample Data for Testing

Once your database is set up, you can use this sample data:

| SKU | Quantity | Vendor | Total Cost | EOQ | Status | Priority |
|-----|----------|--------|------------|-----|--------|----------|
| WIDGET-001 | 100 | Acme Supplies Inc. | $1,250.00 | 150 | Pending | High |
| GADGET-205 | 75 | TechParts Ltd. | $890.50 | 100 | Approved | Medium |
| COMPONENT-X42 | 200 | Industrial Components Co. | $2,100.00 | 250 | Ordered | Critical |

## 🔍 Database ID Format

Your database ID should look like this:
```
a1b2c3d4e5f6789012345678901234567890
```

**Where to find it**: In your database URL after the last `/` and before any `?`

## ✅ Final Checklist

- [ ] All 12 properties created
- [ ] Status has 5 options (Pending, Approved, Ordered, Received, Cancelled)
- [ ] Priority has 4 options (Critical, High, Medium, Low)
- [ ] Database ID copied
- [ ] At least one test record added
- [ ] Database is accessible in your workspace