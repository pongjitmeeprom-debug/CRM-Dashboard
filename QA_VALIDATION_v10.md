# QA Validation v10

Validated before packaging:

- Python syntax check: passed (`python -m py_compile app.py`)
- KPI Mode pipeline separated:
  - Snapshot = selected Snapshot_Month only
  - Accumulated = first available month through selected Snapshot_Month
- Health engine separated from KPI Mode:
  - Rolling 3M follows selected Snapshot Month
  - Login % = Total Login 3M / 30
  - Buy Units/Month = Total Period_Purchase_Units 3M / 3
  - Final Health Status = HOT >=65, WARM >=35 and <65, COOL >0 and <35, COLD =0
- Fixed v9 bug where Final Health HOT used threshold >=80 and hid expected HOT buyers.
- Added KPI Layer Validation table in Executive page.
- Added separate Login Status and Buy Status distributions in Buyer Health page.

Known interpretation note:
- Login Status HOT can still be 0 in the current sample if no buyer reaches Total Login 3M >= 19.5.
- Final Health HOT can exist when combined Login Score and Buy Score reach >=65.
