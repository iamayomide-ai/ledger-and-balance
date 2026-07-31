# Bank Reconciliation System (SIWES Project)

A web-based reconciliation tool that solves a real bank problem: comparing
Head Office and Branch transaction ledgers to find matches, mismatches,
missing transactions and duplicates — automatically.

## Problem It Solves

Every day, Head Office and each Branch produce independent transaction
records. Manually cross-checking thousands of rows for mismatched amounts
or missing entries is slow and error-prone. This system automates that
comparison and flags exactly which transactions need investigation.

## Tech Stack

- Python 3 / Flask (web framework)
- SQLAlchemy (ORM) + SQLite (database)
- Pandas / openpyxl (CSV & Excel import)
- ReportLab (PDF report export)

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# optional: generate demo data with planted matches/mismatches/missing/duplicates
python sample_data/generate_sample_data.py

python run.py
```

Visit http://localhost:5000

## How to Demo It

1. Go to **Import**, upload `sample_data/head_office.csv` as Head Office.
2. Upload `sample_data/branch.csv` as Branch.
3. Click **Run Reconciliation**.
4. Go to **Results** — filter by status to show each case type.
5. Export a PDF/CSV report from the Dashboard.

## Project Structure

```
app/
  models.py          -> Transaction, ReconciliationResult (SQLAlchemy models)
  reconciliation.py  -> MatchRule (abstract base) + Reconciler engine
  importer.py         -> TransactionImporter (CSV/Excel ingestion)
  reports.py          -> PDF/CSV report builders
  routes.py           -> Flask routes (Blueprint)
  templates/           -> Jinja2 HTML pages
  static/style.css     -> Styling
sample_data/
  generate_sample_data.py -> creates demo CSVs
run.py                -> app entry point
```

## OOP Concepts Used (for your defense)

- **Abstraction** — `MatchRule` (in `reconciliation.py`) is an abstract base
  class (`abc.ABC`) defining the contract `evaluate(ho_txn, branch_txn)`
  that every concrete rule must implement.
- **Inheritance** — `ExactMatchRule`, `AmountMismatchRule`,
  `CurrencyMismatchRule`, and `DateMismatchRule` all inherit from
  `MatchRule`.
- **Polymorphism** — `Reconciler._evaluate_pair()` calls `.evaluate()` on
  each rule object without knowing (or caring) which concrete class it is;
  each subclass responds differently. This is also a simple Chain of
  Responsibility pattern — rules are tried in priority order until one
  applies.
- **Encapsulation** — `Reconciler` hides all matching logic behind a single
  public method, `run()`. `Transaction` and `ReconciliationResult` expose
  `to_dict()` rather than letting callers reach into raw columns.

## Matching Rules Implemented

| Rule | Condition | Status |
|---|---|---|
| Exact Match | Reference + amount match (within tolerance) | RECONCILED |
| Currency Mismatch | Reference/amount match, currency differs | CURRENCY_MISMATCH |
| Date Mismatch | Reference/amount match, transaction date differs | DATE_MISMATCH |
| Amount Mismatch | Reference matches, amount differs | AMOUNT_MISMATCH |
| Missing | Reference exists in only one ledger | MISSING_TRANSACTION |
| Duplicate | Reference repeated within one ledger | DUPLICATE |

## Deploying to Render (for a live demo without depending on your laptop's Wi-Fi)

1. Push this project to a GitHub repo (must include `Procfile`, `render.yaml`, `requirements.txt`).
2. Go to [render.com](https://render.com), sign up/log in with GitHub.
3. Click **New +** → **Blueprint**, select your repo. Render will read `render.yaml`
   automatically and set the build/start commands for you.
   - If you'd rather set it up manually instead of via Blueprint: **New +** → **Web Service**,
     select the repo, set:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn run:app`
4. Click **Create Web Service**. First deploy takes a few minutes.
5. Once live, Render gives you a URL like `https://bank-reconciliation-system.onrender.com`.

**Important for demo day:**
- The free tier sleeps after 15 minutes of inactivity — the first request after
  sleeping takes 30-50 seconds to wake up. Open the URL yourself a couple of
  minutes before presenting so it's already warm.
- The SQLite database resets on redeploy/restart (Render's free disk isn't
  persistent). Right before presenting, click **Load Demo Data** on the
  Import page (or re-upload the CSVs) so the data is fresh.
- Keep the local setup working too as a backup in case the venue's network
  is unreliable — don't depend on only one path working on the day.

## Possible Extensions (if you have extra time)

- Simple login (Flask-Login) with a single reconciliation-officer role
- Investigation records against each mismatch/missing case
- Chart.js visualisation of reconciliation rate on the dashboard
