"""
Generates sample_data/head_office.csv and sample_data/branch.csv
with deliberately planted RECONCILED, MISMATCH, MISSING and
DUPLICATE cases so you can demo every code path during defense.

Run from the project root:
    python sample_data/generate_sample_data.py
"""
import csv
import os
from datetime import date, timedelta

OUT_DIR = os.path.dirname(__file__)

names = ["Chidinma Okafor", "Tunde Bakare", "Amina Yusuf", "Emeka Obi",
         "Ngozi Eze", "Segun Adebayo", "Fatima Bello", "Ifeoma Nwosu"]
branches = ["Ikeja", "Victoria Island", "Yaba", "Surulere", "Apapa"]

base_date = date(2026, 7, 28)

head_office_rows = []
branch_rows = []

# 1) Clean matches (RECONCILED)
for i in range(1, 11):
    ref = f"TXN{1000+i}"
    row = dict(
        reference_number=ref, account_number=f"00{1000+i}", customer_name=names[i % len(names)],
        branch=branches[i % len(branches)], amount=round(5000 + i * 137.5, 2),
        currency="NGN", narration="Fund transfer",
        transaction_date=(base_date - timedelta(days=i % 3)).isoformat(),
    )
    head_office_rows.append(row)
    branch_rows.append(dict(row))

# 2) Amount mismatches
for i in range(11, 14):
    ref = f"TXN{1000+i}"
    ho = dict(reference_number=ref, account_number=f"00{1000+i}", customer_name=names[i % len(names)],
               branch=branches[i % len(branches)], amount=round(8000 + i * 50, 2),
               currency="NGN", narration="POS settlement",
               transaction_date=base_date.isoformat())
    br = dict(ho)
    br["amount"] = ho["amount"] + 250.0  # deliberate mismatch
    head_office_rows.append(ho)
    branch_rows.append(br)

# 3) Missing from Branch (exists only in Head Office)
for i in range(14, 17):
    ref = f"TXN{1000+i}"
    head_office_rows.append(dict(
        reference_number=ref, account_number=f"00{1000+i}", customer_name=names[i % len(names)],
        branch=branches[i % len(branches)], amount=round(3000 + i * 20, 2),
        currency="NGN", narration="ATM withdrawal", transaction_date=base_date.isoformat(),
    ))

# 4) Missing from Head Office (exists only in Branch)
for i in range(17, 19):
    ref = f"TXN{1000+i}"
    branch_rows.append(dict(
        reference_number=ref, account_number=f"00{1000+i}", customer_name=names[i % len(names)],
        branch=branches[i % len(branches)], amount=round(4200 + i * 20, 2),
        currency="NGN", narration="Internet banking transfer", transaction_date=base_date.isoformat(),
    ))

# 5) Duplicate reference within Branch ledger
dup_ref = "TXN1099"
for _ in range(2):
    branch_rows.append(dict(
        reference_number=dup_ref, account_number="001099", customer_name="Segun Adebayo",
        branch="Ikeja", amount=1500.0, currency="NGN", narration="Duplicate test",
        transaction_date=base_date.isoformat(),
    ))
head_office_rows.append(dict(
    reference_number=dup_ref, account_number="001099", customer_name="Segun Adebayo",
    branch="Ikeja", amount=1500.0, currency="NGN", narration="Duplicate test",
    transaction_date=base_date.isoformat(),
))

fieldnames = ["reference_number", "account_number", "customer_name", "branch",
              "amount", "currency", "narration", "transaction_date"]


def write_csv(filename, rows):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}")


if __name__ == "__main__":
    write_csv("head_office.csv", head_office_rows)
    write_csv("branch.csv", branch_rows)
