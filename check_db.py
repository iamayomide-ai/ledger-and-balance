"""
Quick way to peek into the database without the interactive Python
prompt (which can choke on pasted multi-line input).

Run with:
    python check_db.py
"""
import sqlite3

conn = sqlite3.connect("instance/recon.db")
cur = conn.cursor()

print("\n--- Tables ---")
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
for row in cur.fetchall():
    print(row[0])

print("\n--- First 5 transactions ---")
cur.execute("SELECT id, reference_number, source, amount, transaction_date FROM transactions LIMIT 5;")
for row in cur.fetchall():
    print(row)

print("\n--- Reconciliation result counts by status ---")
cur.execute("SELECT status, COUNT(*) FROM reconciliation_results GROUP BY status;")
for row in cur.fetchall():
    print(row)

conn.close()
