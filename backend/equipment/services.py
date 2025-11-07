from __future__ import annotations

from io import BytesIO

from django.utils.text import slugify
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_pdf_report(dataset) -> BytesIO:
    """
    Build a lightweight PDF that highlights the dataset level analytics.
    """

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    margin = 50
    y = height - margin

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margin, y, "Chemical Equipment Report")
    y -= 30

    pdf.setFont("Helvetica", 12)
    pdf.drawString(margin, y, f"File: {dataset.file_name}")
    y -= 18
    pdf.drawString(margin, y, f"Uploaded: {dataset.uploaded_at:%Y-%m-%d %H:%M}")
    y -= 30

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(margin, y, "Summary")
    y -= 22

    summary_pairs = [
        ("Total Equipment", dataset.summary.get("total_equipment", 0)),
        ("Avg Flowrate", dataset.summary.get("avg_flowrate", 0)),
        ("Avg Pressure", dataset.summary.get("avg_pressure", 0)),
        ("Avg Temperature", dataset.summary.get("avg_temperature", 0)),
    ]
    pdf.setFont("Helvetica", 12)
    for label, value in summary_pairs:
        pdf.drawString(margin, y, f"{label}: {value}")
        y -= 18

    y -= 12
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(margin, y, "Equipment Type Distribution")
    y -= 22
    pdf.setFont("Helvetica", 12)
    type_dist = dataset.summary.get("type_distribution", {})
    if not type_dist:
        pdf.drawString(margin, y, "No equipment types recorded.")
        y -= 18
    else:
        for equipment_type, count in type_dist.items():
            pdf.drawString(margin, y, f"{equipment_type}: {count}")
            y -= 18

    if dataset.data:
        y -= 12
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(margin, y, "Sample Records")
        y -= 22
        pdf.setFont("Helvetica", 10)
        sample_rows = dataset.data[:5]
        for row in sample_rows:
            row_text = ", ".join(f"{k}: {v}" for k, v in row.items())
            pdf.drawString(margin, y, row_text[:1000])
            y -= 14
            if y < margin:
                pdf.showPage()
                y = height - margin
                pdf.setFont("Helvetica", 10)

    pdf.setTitle(f"equipment-report-{slugify(dataset.file_name)}")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer


def pdf_filename(dataset) -> str:
    return f"equipment-report-{slugify(dataset.file_name)}.pdf"
