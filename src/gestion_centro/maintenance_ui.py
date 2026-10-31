"""Pantalla de mantenimiento y diagnóstico técnico para administradores."""
import json
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QLabel,
)
from gestion_centro.persistence.diagnostics import run_diagnostics
from gestion_centro.persistence.database import session_scope
from gestion_centro.auth.models import AccessAudit


class MaintenanceDialog(QDialog):
    def __init__(self, paths, factory, actor_id):
        super().__init__()
        self.paths, self.factory, self.actor_id = paths, factory, actor_id
        self.report = None
        self.setWindowTitle("Mantenimiento y diagnóstico")
        self.resize(760, 480)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "El diagnóstico no muestra nombres, expedientes ni contenido de documentos. "
            "No elimina datos ni modifica la base de datos."
        ))
        run = QPushButton("Ejecutar diagnóstico")
        run.clicked.connect(self.run)
        layout.addWidget(run)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Comprobación", "Estado", "Detalle técnico"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        export = QPushButton("Guardar informe técnico…")
        export.clicked.connect(self.export)
        layout.addWidget(export)
        self.run()

    def run(self):
        try:
            self.report = run_diagnostics(self.paths)
            rows = [(x["name"], x["status"], x["detail"]) for x in self.report["checks"]]
            rows.extend([
                ("Espacio libre", "INFO", f'{self.report["disk_free_bytes"]:,} bytes'),
                ("Adjuntos", "INFO", f'{self.report["document_file_count"]} archivos · {self.report["document_bytes"]:,} bytes'),
                ("Adjunto mayor", "INFO", f'{self.report["largest_attachment_bytes"]:,} bytes'),
            ])
            self.table.setRowCount(len(rows))
            for i, values in enumerate(rows):
                for j, value in enumerate(values):
                    self.table.setItem(i, j, QTableWidgetItem(value))
            with session_scope(self.factory) as session:
                account = session.get(__import__("gestion_centro.auth.models", fromlist=["UserAccount"]).UserAccount, self.actor_id)
                session.add(AccessAudit(account_id=account.id, username_snapshot=account.username,
                    event="maintenance_diagnostics", details=f'checks={len(rows)}'))
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Diagnóstico interrumpido", str(exc))

    def export(self):
        if not self.report:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar informe técnico",
            "informe_tecnico_centro.json", "Informe JSON (*.json)")
        if not filename:
            return
        try:
            Path(filename).write_text(json.dumps(self.report, ensure_ascii=False, indent=2), encoding="utf-8")
            QMessageBox.information(self, "Informe guardado", "Se ha guardado el informe técnico.")
        except OSError as exc:
            QMessageBox.critical(self, "No se pudo guardar", str(exc))
