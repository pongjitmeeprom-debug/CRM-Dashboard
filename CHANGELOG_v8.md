# CHANGELOG v8 - GitHub-ready clean package

## Fixed / redesigned

1. Executive header
   - Removed floating HOT/WARM/COOL/COLD badges.
   - Replaced with Buyer Health Distribution showing buyer count and percentage.

2. Health status legend issue
   - Removed isolated legends from dashboard sections.
   - Charts use embedded labels, counts, and percentages instead of unexplained floating legends.
   - HOT/WARM/COOL/COLD are tied to Health Score logic.

3. Sold to Buy terminology
   - Dashboard labels use Buy instead of Sold.
   - Health calculation uses Buy Avg./Month.

4. Visit objective
   - Visit analysis prioritizes `Visit_Objective_Detail` when present.

5. Demand mapping
   - Demand dashboard reads demand-specific fields from `02_Visit_Car_Demand_Log`.

6. Feedback mapping
   - Feedback dashboard reads feedback-specific fields from `03_Visit_Feedback_Log`.

7. Follow-up mapping
   - Follow-up Command Center uses `Feedback_Action_Needed` as the primary source.

8. Coverage gap
   - Coverage Gap uses Unique Buyers Visited, not raw repeated visit count.

9. Next Best Buyers
   - Added Priority Index using Opportunity Score, Health Score, and Coverage.

10. Churn Watch
   - Separates Inactive and Churn Risk logic.

11. AE Daily Action List
   - Generates recommended action list by Priority Index and buyer status.

12. Score definition
   - Added score formulas in sidebar and relevant dashboard sections.

13. UI / UX
   - Added card styling, sidebar styling, chart containers, and cleaner hierarchy.

## GitHub packaging

- Renamed README to `README.md`.
- Ensured `requirements.txt` is present.
- Added `.gitignore`.
- Added clean folders: `data/`, `assets/`, `screenshots/`, `.streamlit/`.
