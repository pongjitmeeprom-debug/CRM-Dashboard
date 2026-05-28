# CRM Intelligence Dashboard

Streamlit dashboard for CRM buyer health, AE visits, opportunity, demand, feedback, follow-up, and next-best-action analysis.

## Project structure

```text
.
├── app.py
├── requirements.txt
├── README.md
├── CHANGELOG_v8.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/
│   └── .gitkeep
├── assets/
│   └── .gitkeep
└── screenshots/
    └── .gitkeep
```

## How to run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then upload these two Excel files in the Streamlit sidebar:

1. Buyer Master file with sheets named `Buyer_Master_...`
2. Visit Activity file with sheets such as:
   - `01_Visit_Activity_Log`
   - `02_Visit_Car_Demand_Log`
   - `03_Visit_Feedback_Log`

## Main logic implemented

### Health Score

```text
Login % = Total Login latest 6 months / 30

Login Status:
HOT  >= 65%
WARM >= 35% and < 65%
COOL > 0% and < 35%
COLD = 0%

Buy Avg./Month = Total Buy latest 6 months / 6

Buy Status:
HIGH     >= 14 units/month
MODERATE >= 5 and < 14
LOW      > 0 and < 5
COLD     = 0

Health Score = Login Score x 50% + Buy Score x 50%
```

### Opportunity Score

```text
Opportunity Score = Bid Score x 50% + Buyer Size Score x 30% + Coverage Gap Score x 20%
Coverage Gap uses Unique Buyers Visited, not repeated visit count.
```

## Notes

- The dashboard uses `Buy` terminology instead of `Sold`.
- Floating HOT/WARM/COOL/COLD legends were removed and replaced by distribution widgets with counts and percentages.
- Follow-up command center uses `Feedback_Action_Needed` when available.
