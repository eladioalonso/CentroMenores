"""Exportación de informes agregados a PDF y Word."""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document


def _rows(report: dict) -> list[tuple[str, str]]:
    rows = []
    for key, value in report.items():
        if isinstance(value, dict):
            rows.extend((f"{key} · {name}", str(number)) for name, number in sorted(value.items()))
        else:
            rows.append((key, str(value)))
    return rows


def export_pdf(report: dict, destination: Path) -> Path:
    styles = getSampleStyleSheet()
    story = [Paragraph("Memoria estadística agregada", styles["Title"]),
             Paragraph(f"Periodo: {report['period_start']} – {report['period_end']}", styles["Normal"]),
             Spacer(1, 16)]
    table = Table([["Indicador", "Valor"], *_rows(report)], repeatRows=1, colWidths=[350, 150])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)
    SimpleDocTemplate(str(destination), pagesize=A4).build(story)
    return destination


def export_docx(report: dict, destination: Path) -> Path:
    document = Document()
    document.add_heading("Memoria estadística agregada", 0)
    document.add_paragraph(f"Periodo: {report['period_start']} – {report['period_end']}")
    table = document.add_table(rows=1, cols=2)
    table.style = "Light Shading Accent 1"
    table.rows[0].cells[0].text = "Indicador"
    table.rows[0].cells[1].text = "Valor"
    for label, value in _rows(report):
        cells = table.add_row().cells
        cells[0].text = label
        cells[1].text = value
    document.save(destination)
    return destination
