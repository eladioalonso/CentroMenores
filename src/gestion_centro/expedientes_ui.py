"""Consulta y gestión básica de expedientes y estancias."""
from datetime import date, datetime, timezone

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog,
    QLabel,
)
from sqlalchemy import select

from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.models import Minor, Stay, Event, EventStayLink
from gestion_centro.domain.service import create_minor, open_stay, close_stay, record_event


class ExpedientesDialog(QDialog):
    def __init__(self, factory, actor_id):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.setWindowTitle("Expedientes y estancias")
        self.resize(980, 620)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("El expediente identifica al menor; cada ingreso se registra como una estancia independiente."))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar por código o nombre…")
        self.search.textChanged.connect(self.refresh)
        layout.addWidget(self.search)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Código", "Nombre", "Estado expediente", "Estancia", "Ingreso"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        for label, callback in [
            ("Nuevo expediente", self.new_minor),
            ("Nuevo ingreso / reingreso", self.new_stay),
            ("Cerrar estancia", self.close_selected_stay),
            ("Registrar acontecimiento", self.new_event),
            ("Historial", self.show_history),
            ("Actualizar", self.refresh),
        ]:
            button = QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.refresh()

    def refresh(self):
        term = self.search.text().strip().casefold()
        with session_scope(self.factory) as session:
            minors = session.scalars(select(Minor).order_by(Minor.internal_code)).all()
            rows = []
            for minor in minors:
                for stay in sorted(minor.stays, key=lambda x: x.sequence_number, reverse=True):
                    rows.append((minor.id, stay.id, minor.internal_code,
                        f"{minor.given_names} {minor.family_names}",
                        "Activo" if minor.active else "Inactivo",
                        "Activa" if stay.status == "active" else "Cerrada",
                        stay.started_on.strftime("%d/%m/%Y")))
                if not minor.stays:
                    rows.append((minor.id, None, minor.internal_code,
                        f"{minor.given_names} {minor.family_names}",
                        "Activo" if minor.active else "Inactivo", "Sin ingresos", "—"))
        rows = [r for r in rows if not term or term in r[2].casefold() or term in r[3].casefold()]
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            minor_id, stay_id, *display = row
            for col, value in enumerate(display):
                cell = QTableWidgetItem(value)
                if col == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, (minor_id, stay_id))
                self.table.setItem(i, col, cell)

    def selected(self):
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        return item.data(Qt.ItemDataRole.UserRole) if item else (None, None)

    def new_minor(self):
        code, ok = QInputDialog.getText(self, "Nuevo expediente", "Código interno:")
        if not ok or not code.strip(): return
        given, ok = QInputDialog.getText(self, "Nuevo expediente", "Nombre(s):")
        if not ok or not given.strip(): return
        family, ok = QInputDialog.getText(self, "Nuevo expediente", "Apellidos:")
        if not ok or not family.strip(): return
        try:
            with session_scope(self.factory) as session:
                minor = create_minor(session, actor_account_id=self.actor_id,
                    internal_code=code, given_names=given, family_names=family)
                open_now = QMessageBox.question(self, "Primer ingreso",
                    "¿Registrar también una estancia activa desde hoy?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if open_now == QMessageBox.StandardButton.Yes:
                    open_stay(session, actor_account_id=self.actor_id, minor_id=minor.id, started_on=date.today())
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo crear", str(exc))

    def new_stay(self):
        minor_id, _ = self.selected()
        if not minor_id:
            QMessageBox.information(self, "Selecciona expediente", "Selecciona primero un menor.")
            return
        start, ok = QInputDialog.getText(self, "Nuevo ingreso", "Fecha de ingreso (DD/MM/AAAA):",
            text=date.today().strftime("%d/%m/%Y"))
        if not ok: return
        try:
            start_date = datetime.strptime(start, "%d/%m/%Y").date()
            with session_scope(self.factory) as session:
                open_stay(session, actor_account_id=self.actor_id, minor_id=minor_id, started_on=start_date)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo abrir la estancia", str(exc))

    def close_selected_stay(self):
        _, stay_id = self.selected()
        if not stay_id:
            QMessageBox.information(self, "Selecciona estancia", "Selecciona una estancia.")
            return
        reason, ok = QInputDialog.getMultiLineText(self, "Cerrar estancia", "Motivo del cierre:")
        if not ok or not reason.strip(): return
        try:
            with session_scope(self.factory) as session:
                close_stay(session, actor_account_id=self.actor_id, stay_id=stay_id,
                    ended_on=date.today(), reason=reason)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo cerrar", str(exc))

    def new_event(self):
        minor_id, stay_id = self.selected()
        if not minor_id or not stay_id:
            QMessageBox.information(self, "Selecciona estancia", "Selecciona la estancia a la que vincular el acontecimiento.")
            return
        title, ok = QInputDialog.getText(self, "Acontecimiento", "Título:")
        if not ok or not title.strip(): return
        description, ok = QInputDialog.getMultiLineText(self, "Acontecimiento", "Descripción objetiva:")
        if not ok or not description.strip(): return
        try:
            with session_scope(self.factory) as session:
                record_event(session, author_account_id=self.actor_id, title=title,
                    description=description, happened_at=datetime.now(timezone.utc), stay_ids=[stay_id])
            QMessageBox.information(self, "Acontecimiento", "Registrado en el historial de la estancia.")
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo registrar", str(exc))

    def show_history(self):
        _, stay_id = self.selected()
        if not stay_id:
            QMessageBox.information(self, "Selecciona estancia", "Selecciona una estancia.")
            return
        with session_scope(self.factory) as session:
            links = session.scalars(select(EventStayLink).where(EventStayLink.stay_id == stay_id)).all()
            events = [session.get(Event, link.event_id) for link in links]
            rows = sorted(events, key=lambda x: x.happened_at, reverse=True)
            lines = [f"{e.happened_at.astimezone().strftime('%d/%m/%Y %H:%M')} · {e.title}\n{e.description}\nAutor: {e.author_name_snapshot}" for e in rows]
        QMessageBox.information(self, "Historial de acontecimientos",
            "\n\n".join(lines) if lines else "Esta estancia todavía no tiene acontecimientos registrados.")
