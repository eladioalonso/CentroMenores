"""Interfaces de autorizaciones y salidas."""
from datetime import date, datetime, timezone

from PySide6.QtCore import Qt, QDate, QDateTime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QLineEdit, QTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QDateTimeEdit, QCheckBox, QHBoxLayout, QInputDialog,
)
from sqlalchemy import select

from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.models import Stay
from gestion_centro.domain.documents import Authorization, Outing, OutingStay
from gestion_centro.domain.documents_service import (
    record_authorization, set_authorization_status, create_outing, set_outing_status,
    list_active_stays, list_authorizations, list_valid_authorizations, list_outings,
)


class AuthorizationsDialog(QDialog):
    TYPES = {
        "General": "general", "Visitas familiares": "family_visit",
        "Salidas": "outing", "Actividades": "activity",
        "Sanitaria": "medical", "Imagen": "image", "Viajes": "travel", "Otra": "other",
    }

    def __init__(self, factory, actor_id):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.setWindowTitle("Autorizaciones")
        self.resize(850, 520)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.stay = QComboBox()
        self.kind = QComboBox()
        for label, value in self.TYPES.items():
            self.kind.addItem(label, value)
        self.scope = QLineEdit()
        self.issuer = QLineEdit()
        self.start = QDateEdit(QDate.currentDate())
        self.start.setCalendarPopup(True)
        self.end = QDateEdit(QDate.currentDate().addYears(5))
        self.end.setCalendarPopup(True)
        self.no_end = QCheckBox("Sin fecha final")
        form.addRow("Estancia", self.stay)
        form.addRow("Tipo", self.kind)
        form.addRow("Alcance", self.scope)
        form.addRow("Emisor", self.issuer)
        form.addRow("Válida desde", self.start)
        form.addRow("Válida hasta", self.end)
        form.addRow("", self.no_end)
        layout.addLayout(form)
        save = QPushButton("Registrar autorización")
        save.clicked.connect(self.save)
        layout.addWidget(save)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Tipo", "Alcance", "Emisor", "Vigencia", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        revoke = QPushButton("Revocar con motivo")
        revoke.clicked.connect(self.revoke)
        refresh = QPushButton("Actualizar")
        refresh.clicked.connect(self.refresh)
        actions.addWidget(revoke)
        actions.addWidget(refresh)
        layout.addLayout(actions)
        with session_scope(factory) as session:
            stays = list_active_stays(session, actor_account_id=self.actor_id)
            for stay in stays:
                self.stay.addItem(f"{stay.minor.internal_code} · {stay.minor.given_names} {stay.minor.family_names}", stay.id)
        self.stay.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        stay_id = self.stay.currentData()
        if not stay_id:
            self.table.setRowCount(0)
            return
        with session_scope(self.factory) as session:
            rows = list_authorizations(session, actor_account_id=self.actor_id, stay_id=stay_id)
            data = [(a.id, a.authorization_type, a.scope, a.issuer,
                     f"{a.valid_from:%d/%m/%Y} – {a.valid_until:%d/%m/%Y}" if a.valid_until else f"{a.valid_from:%d/%m/%Y} – sin fin",
                     a.status) for a in rows]
        self.table.setRowCount(len(data))
        for row, values in enumerate(data):
            auth_id, *display = values
            for col, value in enumerate(display):
                cell = QTableWidgetItem(value)
                if col == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, auth_id)
                self.table.setItem(row, col, cell)

    def save(self):
        if not self.stay.currentData() or not self.scope.text().strip() or not self.issuer.text().strip():
            QMessageBox.warning(self, "Datos incompletos", "Completa estancia, alcance y emisor.")
            return
        end = None if self.no_end.isChecked() else self.end.date().toPython()
        try:
            with session_scope(self.factory) as session:
                record_authorization(
                    session, actor_account_id=self.actor_id, stay_id=self.stay.currentData(),
                    authorization_type=self.kind.currentData(), scope=self.scope.text(),
                    issuer=self.issuer.text(), valid_from=self.start.date().toPython(),
                    valid_until=end,
                )
            self.scope.clear()
            self.issuer.clear()
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

    def revoke(self):
        row = self.table.currentRow()
        cell = self.table.item(row, 0) if row >= 0 else None
        if cell is None:
            QMessageBox.information(self, "Selecciona", "Selecciona una autorización.")
            return
        reason, ok = QInputDialog.getText(self, "Revocar autorización", "Motivo:")
        if not ok or not reason.strip():
            return
        try:
            with session_scope(self.factory) as session:
                set_authorization_status(session, actor_account_id=self.actor_id,
                    authorization_id=cell.data(Qt.ItemDataRole.UserRole), status="revoked", reason=reason)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo revocar", str(exc))


class OutingsDialog(QDialog):
    KINDS = {"Familiar": "family", "Actividad": "activity", "Escolar": "school",
             "Sanitaria": "health", "Gestión": "administrative", "Otra": "other"}

    def __init__(self, factory, actor_id):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.setWindowTitle("Salidas")
        self.resize(900, 560)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.stay = QComboBox()
        self.kind = QComboBox()
        for label, value in self.KINDS.items():
            self.kind.addItem(label, value)
        self.destination = QLineEdit()
        self.purpose = QTextEdit()
        self.purpose.setMinimumHeight(100)
        self.auth = QComboBox()
        self.depart = QDateTimeEdit(QDateTime.currentDateTime())
        self.depart.setCalendarPopup(True)
        self.depart.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.back = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.back.setCalendarPopup(True)
        self.back.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.restrictions = QCheckBox("He revisado las restricciones individuales")
        form.addRow("Estancia", self.stay)
        form.addRow("Tipo", self.kind)
        form.addRow("Destino", self.destination)
        form.addRow("Finalidad", self.purpose)
        form.addRow("Autorización vigente", self.auth)
        form.addRow("Salida prevista", self.depart)
        form.addRow("Regreso previsto", self.back)
        form.addRow("", self.restrictions)
        layout.addLayout(form)
        create = QPushButton("Registrar salida")
        create.clicked.connect(self.create)
        layout.addWidget(create)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Destino", "Salida prevista", "Estado", "Regreso real"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        self.status = QComboBox()
        for label, value in [("En curso", "in_progress"), ("Regresó", "returned"), ("Cancelada", "cancelled")]:
            self.status.addItem(label, value)
        update = QPushButton("Actualizar estado")
        update.clicked.connect(self.update_status)
        actions.addWidget(self.status)
        actions.addWidget(update)
        layout.addLayout(actions)
        with session_scope(factory) as session:
            stays = session.scalars(select(Stay).where(Stay.status == "active").order_by(Stay.started_on.desc())).all()
            for stay in stays:
                self.stay.addItem(f"{stay.minor.internal_code} · {stay.minor.given_names} {stay.minor.family_names}", stay.id)
        self.stay.currentIndexChanged.connect(self.refresh_authorizations)
        self.refresh_authorizations()
        self.refresh()

    def refresh_authorizations(self):
        self.auth.clear()
        stay_id = self.stay.currentData()
        if not stay_id:
            return
        with session_scope(self.factory) as session:
            rows = list_valid_authorizations(session, actor_account_id=self.actor_id, stay_id=stay_id)
            for item in rows:
                self.auth.addItem(f"{item.authorization_type} · {item.scope[:70]}", item.id)

    def refresh(self):
        with session_scope(self.factory) as session:
            rows = list_outings(session, actor_account_id=self.actor_id,
                stay_id=self.stay.currentData()) if self.stay.currentData() else []
            data = [(o.id, o.destination, o.planned_departure.astimezone().strftime("%d/%m/%Y %H:%M"),
                     o.status, o.actual_return.astimezone().strftime("%d/%m/%Y %H:%M") if o.actual_return else "—")
                    for o in rows]
        self.table.setRowCount(len(data))
        for row, values in enumerate(data):
            outing_id, *display = values
            for col, value in enumerate(display):
                cell = QTableWidgetItem(value)
                if col == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, outing_id)
                self.table.setItem(row, col, cell)

    def create(self):
        if not self.stay.currentData() or not self.auth.currentData() or not self.restrictions.isChecked():
            QMessageBox.warning(self, "Falta información", "Selecciona estancia, autorización y confirma la revisión de restricciones.")
            return
        departure = self.depart.dateTime().toPython()
        returning = self.back.dateTime().toPython()
        departure = departure.astimezone(timezone.utc) if departure.tzinfo else departure.astimezone().astimezone(timezone.utc)
        returning = returning.astimezone(timezone.utc) if returning.tzinfo else returning.astimezone().astimezone(timezone.utc)
        try:
            with session_scope(self.factory) as session:
                create_outing(
                    session, actor_account_id=self.actor_id, kind=self.kind.currentData(),
                    destination=self.destination.text(), purpose=self.purpose.toPlainText(),
                    planned_departure=departure, planned_return=returning,
                    responsible_account_id=self.actor_id, stay_ids=[self.stay.currentData()],
                    authorization_ids=[self.auth.currentData()], restrictions_checked=True,
                )
            self.destination.clear()
            self.purpose.clear()
            self.restrictions.setChecked(False)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo registrar", str(exc))

    def update_status(self):
        row = self.table.currentRow()
        cell = self.table.item(row, 0) if row >= 0 else None
        if cell is None:
            QMessageBox.information(self, "Selecciona", "Selecciona una salida.")
            return
        try:
            with session_scope(self.factory) as session:
                set_outing_status(session, actor_account_id=self.actor_id,
                    outing_id=cell.data(Qt.ItemDataRole.UserRole), status=self.status.currentData())
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo actualizar", str(exc))
