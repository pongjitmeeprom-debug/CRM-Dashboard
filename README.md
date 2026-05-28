# CRM Intelligence Dashboard v10

Streamlit dashboard for CRM buyer intelligence using two Excel files:

1. `Buyer_Master_Snapshot_All_Months.xlsx`
2. `AX_Visiting_Buyer_Activity_Log.xlsx`

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Required file structure

The app uses file upload from the sidebar. You do not need to commit raw Excel files to GitHub.

## Data model

- **Snapshot View**: selected `Snapshot_Month` only.
- **Historical View**: monthly trend by `Snapshot_Month`.
- **Rolling 3M**: latest 3 snapshot months up to selected month, used for Health Score.
- **Accumulated View**: optional KPI mode that sums from first month through selected month.

## Locked Health Score logic

```text
Login % = Total Login latest 3 months / 30
HOT  >= 65%
WARM >= 35% and < 65%
COOL > 0% and < 35%
COLD = 0%

Buy Units/Month = Total Period_Purchase_Units latest 3 months / 3
HIGH     >= 14 units/month
MODERATE >= 5 and < 14
LOW      > 0 and < 5
COLD     = 0

Health Score = Login Score x 50% + Buy Score x 50%
```

## Notes

- Health status categories are always displayed in fixed order: HOT, WARM, COOL, COLD.
- Coverage Gap uses unique registered buyers visited, not repeated visit rows.
- Follow-up dashboard uses visit follow-up fields, not `Feedback_Action_Needed` as a primary source.
