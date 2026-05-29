# CRM Dashboard v11 Changelog

## Fixes
- Renamed sidebar controls to remove ambiguity:
  - `Selected Month`
  - `Data Scope`: `Current Snapshot` or `Accumulated to Selected Month`
- Added explicit active scope caption showing KPI window and rolling health months.
- Fixed same-family chart layout issues:
  - Plotly legends now use top horizontal layout where legends are needed.
  - Single-status charts hide legends and use direct labels.
  - Wider margins prevent legend clipping / falling off the right edge.
- Redesigned Historical CRM Trend:
  - Uses a metric selector instead of plotting Login/Bid/Buy/Units all in one crowded chart.
  - Prevents duplicate-looking legends and scale confusion.
- Clarified Health distributions:
  - Executive page now shows Login Status Distribution separately from Final Health Score Distribution.
  - This avoids interpreting Login HOT and Final Health HOT as the same thing.
- Applied chart layout helper across dashboard pages to avoid repeated legend clipping issues.

## Data Semantics
- Current Snapshot = selected month only.
- Accumulated to Selected Month = first available snapshot through selected month.
- Rolling 3M Health = latest 3 snapshot months up to selected month.

## Validation Notes
- KPI totals should change when switching Data Scope.
- For selected month 2026-03:
  - Snapshot = Mar only.
  - Accumulated to Selected Month = Feb + Mar.
- Health score remains rolling and is intentionally separate from KPI data scope.
