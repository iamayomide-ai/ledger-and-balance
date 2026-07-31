"""
Database models for the Bank Reconciliation System.

OOP notes for defense:
- Transaction is the base entity for a single ledger line item, imported
  from either the Head Office or a Branch ledger. `source` distinguishes
  which ledger it came from.
- ReconciliationResult represents the OUTCOME of comparing a pair (or
  singleton) of transactions sharing a reference number.
- Both classes encapsulate their own data + simple helper behaviour
  (e.g. to_dict / display helpers), rather than exposing raw dicts
  throughout the app -- that's the encapsulation principle in practice.
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Transaction(db.Model):
    """A single transaction line, imported from either ledger."""

    __tablename__ = "transactions"

    SOURCE_HEAD_OFFICE = "HEAD_OFFICE"
    SOURCE_BRANCH = "BRANCH"

    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(64), nullable=False, index=True)
    account_number = db.Column(db.String(32), nullable=False)
    customer_name = db.Column(db.String(128))
    branch = db.Column(db.String(64))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(8), default="NGN")
    narration = db.Column(db.String(255))
    transaction_date = db.Column(db.Date, nullable=False)
    source = db.Column(db.String(16), nullable=False)  # HEAD_OFFICE / BRANCH
    imported_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "reference_number": self.reference_number,
            "account_number": self.account_number,
            "customer_name": self.customer_name,
            "branch": self.branch,
            "amount": self.amount,
            "currency": self.currency,
            "narration": self.narration,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "source": self.source,
        }

    def __repr__(self):
        return f"<Transaction {self.reference_number} {self.source} {self.amount}>"


class ReconciliationResult(db.Model):
    """The outcome of comparing transactions that share a reference number."""

    __tablename__ = "reconciliation_results"

    STATUS_RECONCILED = "RECONCILED"
    STATUS_AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    STATUS_CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    STATUS_DATE_MISMATCH = "DATE_MISMATCH"
    STATUS_MISSING = "MISSING_TRANSACTION"
    STATUS_DUPLICATE = "DUPLICATE"

    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(64), nullable=False, index=True)
    status = db.Column(db.String(24), nullable=False)

    head_office_txn_id = db.Column(db.Integer, db.ForeignKey("transactions.id"), nullable=True)
    branch_txn_id = db.Column(db.Integer, db.ForeignKey("transactions.id"), nullable=True)

    amount_difference = db.Column(db.Float, default=0.0)
    details = db.Column(db.String(255))
    missing_from = db.Column(db.String(16))  # which side is missing the txn, if applicable

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    head_office_txn = db.relationship("Transaction", foreign_keys=[head_office_txn_id])
    branch_txn = db.relationship("Transaction", foreign_keys=[branch_txn_id])

    def to_dict(self):
        return {
            "id": self.id,
            "reference_number": self.reference_number,
            "status": self.status,
            "amount_difference": self.amount_difference,
            "details": self.details,
            "missing_from": self.missing_from,
            "head_office": self.head_office_txn.to_dict() if self.head_office_txn else None,
            "branch": self.branch_txn.to_dict() if self.branch_txn else None,
        }
