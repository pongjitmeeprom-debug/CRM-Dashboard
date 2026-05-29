# QA Validation v11

## Confirmed Fixes

### 1. Data Scope semantics
The sidebar no longer uses the ambiguous `KPI Mode` label. It now uses:
- Selected Month
- Data Scope

Meaning:
- Current Snapshot: selected month only
- Accumulated to Selected Month: from first snapshot month to selected month

### 2. Historical Trend legend issue
The multi-line trend chart was replaced with a metric selector. This prevents:
- legend clipping on the right
- duplicate-looking legends
- scale conflict between Login, Bid, Buy, Units

### 3. Health HOT confusion
The Executive page now displays:
- Login Status Distribution
- Final Health Score Distribution

This separates engagement HOT from final health HOT.

### 4. Same-family legend clipping
A shared `plot()` / `style_fig()` helper is used for charts so legends are top-horizontal or hidden when redundant.

## Manual Test Checklist
- Upload Buyer Master and Visit Activity files.
- Select 2026-03.
- Switch Data Scope between Current Snapshot and Accumulated to Selected Month.
- Confirm KPI numbers change.
- Confirm active caption shows the expected scope.
- Confirm Historical CRM Trend no longer has right-side clipped legend.
- Confirm Province Health Mix / AE Health Mix legends are visible at the top.
