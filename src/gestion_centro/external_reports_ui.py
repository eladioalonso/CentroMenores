"""Interfaz de informes externos con selección explícita y doble revisión."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QLineEdit, QTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QCheckBox, QHBoxLayout, QInputDialog,
)
from sqlalchemy import select
from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.models import Stay
from gestion_centro.domain.documents import Authorization
from gestion_centro.domain.external_reports import ExternalReport
from gestion_centro.domain.external_reports_service import (
    create_external_report, review_external_report, mark_external_report_delivered,
    list_external_reports,
)


class ExternalReportsDialog(QDialog):
    FIELDS = [
        ("Datos identificativos básicos", "identity_basic"),
        ("Fechas de estancia", "stay_dates"),
        ("Resumen educativo", "education"),
        ("Historial de escolarización", "schooling"),
    ]

    def __init__(self, factory, actor_id):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.setWindowTitle("Informes externos · selección y trazabilidad")
        self.resize(960, 680)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.stay = QComboBox()
        self.authorization = QComboBox()
        self.recipient = QLineEdit()
        self.purpose = QLineEdit()
        form.addRow("Estancia", self.stay)
        form.addRow("Autorización vigente", self.authorization)
        form.addRow("Organismo / destinatario", self.recipient)
        form.addRow("Finalidad concreta", self.purpose)
        layout.addLayout(form)
        layout.addWidget(QLabel("Campos expresamente incluidos (no se incorporan automáticamente otros datos):"))
        self.field_checks = []
        for label, key in self.FIELDS:
            check = QCheckBox(label)
            check.setProperty("field_key", key)
            self.field_checks.append(check)
            layout.addWidget(check)
        layout.addWidget(QLabel("Contenido del informe. Introduce únicamente información correspondiente a los campos seleccionados:"))
        self.content = QTextEdit()
        self.content.setPlaceholderText("Redacción manual del contenido que se propone remitir…")
        layout.addWidget(self.content)
        create = QPushButton("Guardar borrador")
        create.clicked.connect(self.create)
        layout.addWidget(create)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Fecha", "Destinatario", "Finalidad", "Campos", "Estado", "Revisión / entrega"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        review = QPushButton("Revisar y aprobar")
        review.clicked.connect(self.review)
        deliver = QPushButton("Registrar entrega")
        deliver.clicked.connect(self.deliver)
        refresh = QPushButton("Actualizar")
        refresh.clicked.connect(self.refresh)
        actions.addWidget(review); actions.addWidget(deliver); actions.addWidget(refresh)
        layout.addLayout(actions)
        with session_scope(factory) as session:
            stays = session.scalars(select(Stay).where(Stay.status == "active")
                .order_by(Stay.started_on.desc())).all()
            for stay in stays:
                self.stay.addItem(
                    f"{stay.minor.internal_code} · {stay.minor.given_names} {stay.minor.family_names}",
                    stay.id)
        self.stay.currentIndexChanged.connect(self.refresh_authorizations)
        self.refresh_authorizations()
        self.refresh()

    def refresh_authorizations(self):
        self.authorization.clear()
        stay_id = self.stay.currentData()
        if not stay_id:
            return
        from datetime import date
        with session_scope(self.factory) as session:
            rows = session.scalars(select(Authorization).where(
                Authorization.stay_id == stay_id, Authorization.status == "valid",
                Authorization.valid_from <= date.today()).order_by(Authorization.valid_from.desc())).all()
            for item in rows:
                if item.valid_until is None or item.valid_until >= date.today():
                    self.authorization.addItem(
                        f"{item.authorization_type} · {item.issuer} · {item.scope[:60]}", item.id)

    def refresh(self):
        stay_id = self.stay.currentData()
        with session_scope(self.factory) as session:
            rows = list_external_reports(session, actor_account_id=self.actor_id, stay_id=stay_id) if stay_id else []
            data = [(r.id, r.created_at, r.recipient, r.purpose, r.included_fields,
                r.status, r.reviewed_by_name_snapshot or "—",
                r.delivery_reference or "—") for r in rows]
        self.table.setRowCount(len(data))
        for i, row in enumerate(data):
            report_id, created, recipient, purpose, fields, status, reviewer, delivery = row
            values = [created.astimezone().strftime("%d/%m/%Y %H:%M"), recipient,
                purpose, fields, status, f"Revisó: {reviewer} · Entrega: {delivery}"]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if col == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, report_id)
                self.table.setItem(i, col, cell)

    def selected_report_id(self):
        row = self.table.currentRow()
        cell = self.table.item(row, 0) if row >= 0 else None
        return cell.data(Qt.ItemDataRole.UserRole) if cell else None

    def create(self):
        fields = [check.property("field_key") for check in self.field_checks if check.isChecked()]
        if not self.stay.currentData() or not self.authorization.currentData():
            QMessageBox.warning(self, "Falta autorización", "Selecciona una estancia y una autorización vigente.")
            return
        try:
            with session_scope(self.factory) as session:
                create_external_report(session, actor_account_id=self.actor_id,
                    stay_id=self.stay.currentData(), authorization_id=self.authorization.currentData(),
                    recipient=self.recipient.text(), purpose=self.purpose.text(),
                    included_fields=fields, content=self.content.toPlainText())
            self.content.clear()
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

    def review(self):
        report_id = self.selected_report_id()
        if not report_id: return
        if QMessageBox.question(self, "Revisión", "¿Has comprobado el contenido, los campos seleccionados y la autorización antes de aprobar?") != QMessageBox.StandardButton.Yes:
            return
        try:
            with session_scope(self.factory) as session:
                review_external_report(session, actor_account_id=self.actor_id, report_id=report_id)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo aprobar", str(exc))

    def deliver(self):
        report_id = self.selected_report_id()
        if not report_id: return
        reference, ok = QInputDialog.getText(self, "Registrar entrega", "Referencia / justificante de entrega:")
        if not ok or not reference.strip(): return
        try:
            with session_scope(self.factory) as session:
                mark_external_report_delivered(session, actor_account_id=self.actor_id,
                    report_id=report_id, delivery_reference=reference)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo registrar", str(exc))
