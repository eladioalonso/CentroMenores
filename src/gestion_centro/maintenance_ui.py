"""Pantalla de mantenimiento y diagnóstico técnico para administradores."""
import json
from pathlib import Path
from datetime import timezone

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QLabel, QDateEdit,
)
from gestion_centro.persistence.diagnostics import run_diagnostics
from gestion_centro.persistence.database import session_scope
from gestion_centro.auth.models import AccessAudit, UserAccount
from gestion_centro.auth.service import list_audit_events


class AuditDialog(QDialog):
    """Consulta de auditoría restringida a administradores activos."""

    def __init__(self, factory, actor_id):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.setWindowTitle("Registro de auditoría")
        self.resize(1050, 620)
        layout = QVBoxLayout(self)
        filters = QHBoxLayout()
        self.start_date = QDateEdit(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        refresh = QPushButton("Consultar")
        refresh.clicked.connect(self.refresh)
        filters.addWidget(QLabel("Desde"))
        filters.addWidget(self.start_date)
        filters.addWidget(QLabel("Hasta"))
        filters.addWidget(self.end_date)
        filters.addWidget(refresh)
        filters.addStretch(1)
        layout.addLayout(filters)
        hint = QLabel("Se muestran eventos de acceso y cambios administrativos. La consulta también queda registrada.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Fecha y hora", "Cuenta", "Evento", "Detalle técnico"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        close = QPushButton("Cerrar")
        close.clicked.connect(self.accept)
        layout.addWidget(close)
        self.refresh()

    def refresh(self):
        try:
            with session_scope(self.factory) as session:
                rows = list_audit_events(
                    session, actor_account_id=self.actor_id,
                    start_date=self.start_date.date().toPython(),
                    end_date=self.end_date.date().toPython(),
                    limit=500,
                )
            self.table.setRowCount(len(rows))
            for row_index, event in enumerate(rows):
                occurred_at = event.occurred_at
                if occurred_at.tzinfo is None:
                    occurred_at = occurred_at.replace(tzinfo=timezone.utc)
                values = [
                    occurred_at.astimezone().strftime("%d/%m/%Y %H:%M:%S"),
                    event.username_snapshot, event.event, event.details or "—",
                ]
                for column, value in enumerate(values):
                    self.table.setItem(row_index, column, QTableWidgetItem(value))
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo consultar la auditoría", str(exc))


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
        audit = QPushButton("Consultar registro de auditoría")
        audit.clicked.connect(lambda: AuditDialog(factory, actor_id).exec())
        layout.addWidget(audit)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Comprobación", "Estado", "Detalle técnico"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        export = QPushButton("Guardar informe técnico…")
        export.clicked.connect(self.export)
        layout.addWidget(export)
        self.run()

    @staticmethod
    def require_admin(session, actor_id):
        account = session.get(UserAccount, actor_id)
        if (account is None or not account.active or not account.professional.active
                or account.role != "admin"):
            raise PermissionError("Se requiere una cuenta administradora activa")
        return account

    def run(self):
        try:
            with session_scope(self.factory) as session:
                self.require_admin(session, self.actor_id)
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
                account = self.require_admin(session, self.actor_id)
                session.add(AccessAudit(account_id=account.id, username_snapshot=account.username,
                    event="maintenance_diagnostics", details=f'checks={len(rows)}'))
        except (OSError, ValueError, PermissionError) as exc:
            QMessageBox.critical(self, "Diagnóstico interrumpido", str(exc))

    def export(self):
        if not self.report:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar informe técnico",
            "informe_tecnico_centro.json", "Informe JSON (*.json)")
        if not filename:
            return
        try:
            with session_scope(self.factory) as session:
                self.require_admin(session, self.actor_id)
            Path(filename).write_text(json.dumps(self.report, ensure_ascii=False, indent=2), encoding="utf-8")
            QMessageBox.information(self, "Informe guardado", "Se ha guardado el informe técnico.")
        except (OSError, PermissionError) as exc:
            QMessageBox.critical(self, "No se pudo guardar", str(exc))
