import os
import tempfile
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file

from .models import db, Transaction, ReconciliationResult
from .importer import TransactionImporter, ImportError_
from .reconciliation import Reconciler
from .reports import build_pdf_report, build_csv_report
from .seed import seed_demo_data

main_bp = Blueprint("main", __name__)


@main_bp.route("/seed-demo", methods=["POST"])
def seed_demo():
    seed_demo_data()
    flash("Demo data loaded: 19 Head Office + 19 Branch transactions.", "success")
    return redirect(url_for("main.upload"))


@main_bp.route("/")
def dashboard():
    total_raw_txns = Transaction.query.count()
    results = ReconciliationResult.query.all()

    counts = {
        "reconciled": sum(1 for r in results if r.status == ReconciliationResult.STATUS_RECONCILED),
        "amount_mismatch": sum(1 for r in results if r.status == ReconciliationResult.STATUS_AMOUNT_MISMATCH),
        "currency_mismatch": sum(1 for r in results if r.status == ReconciliationResult.STATUS_CURRENCY_MISMATCH),
        "date_mismatch": sum(1 for r in results if r.status == ReconciliationResult.STATUS_DATE_MISMATCH),
        "missing": sum(1 for r in results if r.status == ReconciliationResult.STATUS_MISSING),
        "duplicate": sum(1 for r in results if r.status == ReconciliationResult.STATUS_DUPLICATE),
    }
    total_results = len(results)
    reconciliation_rate = round(counts["reconciled"] / (total_results or 1) * 100, 1)

    # When results exist, total_txns represents total reconciled items matching the breakdown sum
    total_txns = total_results if total_results > 0 else total_raw_txns

    return render_template(
        "dashboard.html",
        total_txns=total_txns,
        total_raw_txns=total_raw_txns,
        counts=counts,
        reconciliation_rate=reconciliation_rate,
        has_results=total_results > 0,
    )


@main_bp.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        source = request.form.get("source")
        file = request.files.get("file")

        if not file or file.filename == "":
            flash("Please choose a file to upload.", "error")
            return redirect(url_for("main.upload"))

        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        try:
            importer = TransactionImporter(source=source)
            summary = importer.import_file(tmp_path)
            flash(
                f"Imported {summary['imported']} transactions, "
                f"rejected {summary['rejected']}.",
                "success" if summary["rejected"] == 0 else "warning",
            )
            if summary["errors"]:
                for err in summary["errors"]:
                    flash(err, "error")
        except ImportError_ as e:
            flash(str(e), "error")
        finally:
            os.unlink(tmp_path)

        return redirect(url_for("main.upload"))

    ho_count = Transaction.query.filter_by(source=Transaction.SOURCE_HEAD_OFFICE).count()
    branch_count = Transaction.query.filter_by(source=Transaction.SOURCE_BRANCH).count()
    return render_template("upload.html", ho_count=ho_count, branch_count=branch_count)


@main_bp.route("/reconcile", methods=["POST"])
def run_reconciliation():
    tolerance = float(request.form.get("tolerance", 0) or 0)
    reconciler = Reconciler(tolerance=tolerance)
    summary = reconciler.run()
    flash(f"Reconciliation complete: {summary}", "success")
    return redirect(url_for("main.results"))


@main_bp.route("/results")
def results():
    status_filter = request.args.get("status")
    query = ReconciliationResult.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    all_results = query.order_by(ReconciliationResult.id.desc()).all()
    return render_template(
        "results.html",
        results=all_results,
        status_filter=status_filter,
        statuses=[
            ReconciliationResult.STATUS_RECONCILED,
            ReconciliationResult.STATUS_AMOUNT_MISMATCH,
            ReconciliationResult.STATUS_CURRENCY_MISMATCH,
            ReconciliationResult.STATUS_DATE_MISMATCH,
            ReconciliationResult.STATUS_MISSING,
            ReconciliationResult.STATUS_DUPLICATE,
        ],
    )


@main_bp.route("/reports/pdf")
def report_pdf():
    results = ReconciliationResult.query.all()
    path = build_pdf_report(results)
    return send_file(path, as_attachment=True, download_name="reconciliation_report.pdf")


@main_bp.route("/reports/csv")
def report_csv():
    results = ReconciliationResult.query.all()
    path = build_csv_report(results)
    return send_file(path, as_attachment=True, download_name="reconciliation_report.csv")


@main_bp.route("/reset", methods=["POST"])
def reset_data():
    ReconciliationResult.query.delete()
    Transaction.query.delete()
    db.session.commit()
    flash("All data cleared.", "success")
    return redirect(url_for("main.dashboard"))
