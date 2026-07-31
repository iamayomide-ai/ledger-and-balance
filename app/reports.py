import csv
import tempfile
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def build_csv_report(results) -> str:
    fd, path = tempfile.mkstemp(suffix=".csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Reference", "Status", "Amount Diff", "Details"])
        for r in results:
            writer.writerow([r.reference_number, r.status, r.amount_difference, r.details])
    return path


def build_pdf_report(results) -> str:
    fd, path = tempfile.mkstemp(suffix=".pdf")
    doc = SimpleDocTemplate(path, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = [Paragraph("Bank Reconciliation Report", styles["Title"]), Spacer(1, 12)]

    data = [["Reference", "Status", "Amount Diff", "Details"]]
    for r in results:
        data.append([r.reference_number, r.status, str(r.amount_difference), (r.details or "")[:80]])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ]))
    elements.append(table)
    doc.build(elements)
    return path
