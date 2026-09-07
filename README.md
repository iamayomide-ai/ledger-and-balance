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

## Outcome

The system successfully detects all four reconciliation cases — exact matches, 
amount mismatches, missing transactions on either side, and duplicate entries 
— against realistic multi-thousand-row datasets. What would normally take 
hours of manual spreadsheet cross-checking now runs in seconds, with a 
downloadable PDF/CSV report ready for audit review.

## What I Learned

Building the Reconciler engine around an abstract MatchRule base class made 
it straightforward to add new comparison logic later without touching the 
core matching flow — a small design decision that paid off once I started 
testing edge cases like partial-amount matches and near-duplicate entries.
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
