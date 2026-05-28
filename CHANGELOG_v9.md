# CRM Dashboard v9 Changelog

## Core fixes
- Refactored data model into Snapshot, Historical, Rolling 3M, and Accumulated views.
- Current KPI no longer incorrectly sums all snapshots unless user selects Accumulated mode.
- Health Score now uses rolling 3 snapshot months up to the selected Snapshot Month.
- Login % = Total Login latest 3 months / 30.
- Buy Units/Month = Total Period_Purchase_Units latest 3 months / 3.
- Health Status categories are forced to show HOT / WARM / COOL / COLD even when count is zero.
- Fixed status ordering and color consistency.

## Dashboard fixes
- Removed floating status legend from executive header.
- Replaced it with Buyer Health Distribution showing count and percentage.
- Redesigned AE Efficiency Matrix with AE labels, coverage %, buyers assigned, visits, and benchmark lines.
- Coverage Gap uses Unique Registered Buyers Visited / Buyers Assigned.
- Demand dashboard uses sheet 02_Visit_Car_Demand_Log and filters through Visit_ID.
- Feedback dashboard uses sheet 03_Visit_Feedback_Log.
- Follow-up dashboard uses Follow_Up_Required, Follow_Up_Action, Follow_Up_Owner, and Next_Action_Date instead of Feedback_Action_Needed as primary source.
- Churn Watch separates Inactive vs Churn Risk.
- Next Best Buyers and AE Daily Action List rebuilt from health, opportunity, and visit coverage.

## GitHub readiness
- Clean project structure retained.
- requirements.txt refreshed.
- Syntax validation passed.
