"""
Handles importing transaction ledgers (CSV or Excel) into the database.

Expected columns (case-insensitive):
reference_number, account_number, customer_name, branch, amount,
currency, narration, transaction_date
"""
from datetime import datetime
import pandas as pd

from .models import db, Transaction

REQUIRED_COLUMNS = ["reference_number", "account_number", "amount", "transaction_date"]


class ImportError_(Exception):
    pass


class TransactionImporter:
    """Reads a ledger file and persists Transaction rows for a given source."""

    def __init__(self, source: str):
        self.source = source  # Transaction.SOURCE_HEAD_OFFICE or SOURCE_BRANCH

    def import_file(self, filepath: str) -> dict:
        df = self._read_file(filepath)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing_cols:
            raise ImportError_(f"Missing required columns: {', '.join(missing_cols)}")

        imported, rejected = 0, 0
        errors = []

        for idx, row in df.iterrows():
            try:
                txn = Transaction(
                    reference_number=str(row["reference_number"]).strip(),
                    account_number=str(row["account_number"]).strip(),
                    customer_name=str(row.get("customer_name", "")).strip(),
                    branch=str(row.get("branch", "")).strip(),
                    amount=float(row["amount"]),
                    currency=str(row.get("currency", "NGN")).strip() or "NGN",
                    narration=str(row.get("narration", "")).strip(),
                    transaction_date=self._parse_date(row["transaction_date"]),
                    source=self.source,
                )
                if not txn.reference_number or txn.reference_number.lower() == "nan":
                    raise ValueError("Empty reference number")
                db.session.add(txn)
                imported += 1
            except Exception as e:
                rejected += 1
                errors.append(f"Row {idx + 2}: {e}")

        db.session.commit()
        return {"imported": imported, "rejected": rejected, "errors": errors[:20]}

    @staticmethod
    def _read_file(filepath: str) -> pd.DataFrame:
        if filepath.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(filepath)
        return pd.read_csv(filepath)

    @staticmethod
    def _parse_date(value):
        if isinstance(value, datetime):
            return value.date()
        return pd.to_datetime(value).date()
