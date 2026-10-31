"""Interfaz de estadísticas agregadas."""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDateEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
)
from PySide6.QtCore import QDate

from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.reports import aggregate_statistics, export_statistics_csv
from gestion_centro.domain.report_exports import export_pdf, export_docx


class ReportsDialog(QDialog):
    def __init__(self, factory, actor_id):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.report = None
        self.setWindowTitle("Estadísticas y memoria agregada")
        self.resize(700, 460)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.start = QDateEdit()
        self.start.setCalendarPopup(True)
        self.start.setDate(QDate.currentDate().addMonths(-1))
        self.end = QDateEdit()
        self.end.setCalendarPopup(True)
        self.end.setDate(QDate.currentDate())
        form.addRow("Desde", self.start)
        form.addRow("Hasta", self.end)
        layout.addLayout(form)
        generate = QPushButton("Generar estadísticas")
        generate.clicked.connect(self.generate)
        layout.addWidget(generate)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Indicador agregado", "Valor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        export = QPushButton("Exportar CSV…")
        export.clicked.connect(self.export)
        layout.addWidget(export)
        pdf = QPushButton("Exportar PDF…")
        pdf.clicked.connect(lambda: self.export_document("pdf"))
        layout.addWidget(pdf)
        word = QPushButton("Exportar Word…")
        word.clicked.connect(lambda: self.export_document("docx"))
        layout.addWidget(word)
        self.generate()

    def generate(self):
        start = self.start.date().toPython()
        end = self.end.date().toPython()
        try:
            with session_scope(self.factory) as session:
                self.report = aggregate_statistics(session, actor_account_id=self.actor_id,
                    start_date=start, end_date=end)
            rows = []
            for key, value in self.report.items():
                if isinstance(value, dict):
                    rows.extend((f"{key} · {subkey}", str(number)) for subkey, number in sorted(value.items()))
                else:
                    rows.append((key, str(value)))
            self.table.setRowCount(len(rows))
            for i, (label, value) in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(label))
                self.table.setItem(i, 1, QTableWidgetItem(value))
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo generar", str(exc))

    def export_document(self, kind):
        if not self.report:
            return
        extension = "pdf" if kind == "pdf" else "docx"
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar informe",
            f"memoria_agregada.{extension}", f"{extension.upper()} (*.{extension})")
        if not filename:
            return
        try:
            (export_pdf if kind == "pdf" else export_docx)(self.report, Path(filename))
            QMessageBox.information(self, "Informe guardado",
                "Se ha generado una memoria estadística agregada sin nombres ni identificadores.")
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Error de exportación", str(exc))

    def export(self):
        if not self.report:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Exportar estadísticas",
            "estadisticas_agregadas.csv", "CSV (*.csv)")
        if not filename:
            return
        try:
            export_statistics_csv(self.report, Path(filename))
            QMessageBox.information(self, "Exportación completada",
                "Se ha exportado información agregada, sin nombres ni identificadores.")
        except OSError as exc:
            QMessageBox.critical(self, "Error de exportación", str(exc))
