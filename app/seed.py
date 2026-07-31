"""
Seeds the database directly with the same planted demo dataset used in
sample_data/generate_sample_data.py, without needing to upload CSV files.
Useful for live demos where uploading files on stage is a risk.
"""
from datetime import date, timedelta

from .models import db, Transaction

names = ["Chidinma Okafor", "Tunde Bakare", "Amina Yusuf", "Emeka Obi",
         "Ngozi Eze", "Segun Adebayo", "Fatima Bello", "Ifeoma Nwosu"]
branches = ["Ikeja", "Victoria Island", "Yaba", "Surulere", "Apapa"]
base_date = date(2026, 7, 28)


def seed_demo_data():
    """Clears existing transactions/results and inserts a fresh demo set."""
    from .models import ReconciliationResult
    ReconciliationResult.query.delete()
    Transaction.query.delete()

    def add(source, ref, i, amount, currency="NGN", narration="Fund transfer", txn_date=None):
        db.session.add(Transaction(
            reference_number=ref,
            account_number=f"00{1000+i}",
            customer_name=names[i % len(names)],
            branch=branches[i % len(branches)],
            amount=amount,
            currency=currency,
            narration=narration,
            transaction_date=txn_date or base_date,
            source=source,
        ))

    # Clean matches
    for i in range(1, 11):
        ref = f"TXN{1000+i}"
        amt = round(5000 + i * 137.5, 2)
        d = base_date - timedelta(days=i % 3)
        add(Transaction.SOURCE_HEAD_OFFICE, ref, i, amt, txn_date=d)
        add(Transaction.SOURCE_BRANCH, ref, i, amt, txn_date=d)

    # Amount mismatches
    for i in range(11, 14):
        ref = f"TXN{1000+i}"
        amt = round(8000 + i * 50, 2)
        add(Transaction.SOURCE_HEAD_OFFICE, ref, i, amt, narration="POS settlement")
        add(Transaction.SOURCE_BRANCH, ref, i, amt + 250.0, narration="POS settlement")

    # Missing from Branch
    for i in range(14, 17):
        ref = f"TXN{1000+i}"
        add(Transaction.SOURCE_HEAD_OFFICE, ref, i, round(3000 + i * 20, 2), narration="ATM withdrawal")

    # Missing from Head Office
    for i in range(17, 19):
        ref = f"TXN{1000+i}"
        add(Transaction.SOURCE_BRANCH, ref, i, round(4200 + i * 20, 2), narration="Internet banking transfer")

    # Duplicate within Branch
    dup_ref = "TXN1099"
    add(Transaction.SOURCE_HEAD_OFFICE, dup_ref, 99, 1500.0, narration="Duplicate test")
    add(Transaction.SOURCE_BRANCH, dup_ref, 99, 1500.0, narration="Duplicate test")
    add(Transaction.SOURCE_BRANCH, dup_ref, 99, 1500.0, narration="Duplicate test")

    db.session.commit()
