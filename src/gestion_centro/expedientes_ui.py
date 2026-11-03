"""Consulta y gestión básica de expedientes y estancias."""
from datetime import date, datetime, timezone

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog,
    QLabel, QDateEdit, QTabWidget, QWidget, QTextEdit, QScrollArea,
)
from sqlalchemy import select

from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.models import Minor, Stay, Event, EventStayLink
from gestion_centro.domain.service import create_minor, open_stay, close_stay, record_event


class NewMinorDialog(QDialog):
    """Alta completa del expediente. Los campos complementarios son opcionales."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo expediente")
        self.resize(620, 720)
        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs)

        personal = QWidget()
        personal_form = QFormLayout(personal)
        self.code = QLineEdit()
        self.given = QLineEdit()
        self.family = QLineEdit()
        self.birth_country = QLineEdit()
        self.locality = QLineEdit()
        self.nationality = QLineEdit()
        self.birth_date = QDateEdit()
        self.birth_date.setCalendarPopup(True)
        self.birth_date.setDisplayFormat("dd/MM/yyyy")
        self.birth_date.setMinimumDate(QDate(1900, 1, 1))
        self.birth_date.setSpecialValueText("No indicada")
        self.birth_date.setDate(self.birth_date.minimumDate())
        self.age_label = QLabel("—")
        self.birth_date.dateChanged.connect(self.update_age)
        self.nif_nie = QLineEdit()
        self.passport = QLineEdit()
        self.address = QTextEdit()
        self.address.setMaximumHeight(65)
        self.email = QLineEdit()
        for label, widget in [
            ("Código interno *", self.code), ("Nombre(s) *", self.given),
            ("Apellidos *", self.family), ("País de nacimiento", self.birth_country),
            ("Localidad", self.locality), ("Nacionalidad", self.nationality),
            ("Fecha de nacimiento", self.birth_date), ("Edad (calculada)", self.age_label),
            ("NIF o NIE", self.nif_nie),
            ("Pasaporte", self.passport), ("Dirección", self.address), ("Email", self.email),
        ]:
            personal_form.addRow(label, widget)
        tabs.addTab(personal, "Datos personales")

        health = QWidget()
        health_form = QFormLayout(health)
        self.cip = QLineEdit()
        self.health_center = QLineEdit()
        self.physician = QLineEdit()
        self.nurse = QLineEdit()
        self.card_expiry = QDateEdit()
        self.card_expiry.setCalendarPopup(True)
        self.card_expiry.setDisplayFormat("dd/MM/yyyy")
        self.card_expiry.setMinimumDate(QDate(1900, 1, 1))
        self.card_expiry.setSpecialValueText("No indicada")
        self.card_expiry.setDate(self.card_expiry.minimumDate())
        self.clinical_history = QTextEdit()
        self.clinical_history.setMinimumHeight(150)
        for label, widget in [
            ("CIP", self.cip), ("Centro de Salud", self.health_center),
            ("Facultativo", self.physician), ("Enfermera", self.nurse),
            ("Caducidad tarjeta sanitaria", self.card_expiry),
            ("Historial clínico", self.clinical_history),
        ]:
            health_form.addRow(label, widget)
        tabs.addTab(health, "Datos sanitarios")

        buttons = QHBoxLayout()
        save = QPushButton("Crear expediente")
        cancel = QPushButton("Cancelar")
        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        root.addLayout(buttons)

    def update_age(self, birth_date):
        if birth_date <= self.birth_date.minimumDate():
            self.age_label.setText("—")
            return
        born = birth_date.toPython()
        today = date.today()
        years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        self.age_label.setText(str(years))

    def values(self):
        birth = self.birth_date.date().toPython() if self.birth_date.date() > self.birth_date.minimumDate() else None
        expiry = self.card_expiry.date().toPython() if self.card_expiry.date() > self.card_expiry.minimumDate() else None
        return {
            "internal_code": self.code.text(), "given_names": self.given.text(),
            "family_names": self.family.text(), "birth_country": self.birth_country.text(),
            "locality": self.locality.text(), "nationality": self.nationality.text(),
            "birth_date": birth, "nif_nie": self.nif_nie.text(),
            "passport_number": self.passport.text(), "cip": self.cip.text(),
            "address": self.address.toPlainText(), "health_center": self.health_center.text(),
            "physician": self.physician.text(), "nurse": self.nurse.text(),
            "health_card_expires_on": expiry, "clinical_history": self.clinical_history.toPlainText(),
            "email": self.email.text(),
        }


class MinorWorkspaceDialog(QDialog):
    def __init__(self, factory, actor_id, minor_id, parent=None):
        super().__init__(parent)
        self.factory, self.actor_id, self.minor_id = factory, actor_id, minor_id
        self.resize(850, 600)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.personal = QWidget()
        self.personal_form = QFormLayout(self.personal)
        self.tabs.addTab(self.personal, 'Datos personales')
        self.stays = QTableWidget(0, 4)
        self.stays.setHorizontalHeaderLabels(['Ingreso', 'Salida', 'Estado', 'Motivo'])
        self.stays.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.stays, 'Estancias')
        self.events = QTableWidget(0, 4)
        self.events.setHorizontalHeaderLabels(['Fecha', 'Acontecimiento', 'Descripción', 'Autor'])
        self.events.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.events, 'Acontecimientos')
        actions = QHBoxLayout()
        edit = QPushButton('Modificar datos')
        edit.clicked.connect(self.edit_personal)
        actions.addWidget(edit)
        close = QPushButton('Cerrar')
        close.clicked.connect(self.accept)
        actions.addWidget(close)
        layout.addLayout(actions)
        self.refresh()

    def refresh(self):
        with session_scope(self.factory) as session:
            minor = session.get(Minor, self.minor_id)
            if minor is None:
                self.reject()
                return
            self.setWindowTitle('Expediente · ' + minor.internal_code + ' · ' + minor.given_names + ' ' + minor.family_names)
            while self.personal_form.rowCount():
                self.personal_form.removeRow(0)
            fields = [('Código', minor.internal_code), ('Nombre', minor.given_names), ('Apellidos', minor.family_names), ('País de nacimiento', minor.birth_country), ('Localidad', minor.locality), ('Nacionalidad', minor.nationality), ('Fecha nacimiento', str(minor.birth_date or '—')), ('Edad', str(minor.age or '—')), ('NIF/NIE', minor.nif_nie), ('Pasaporte', minor.passport_number), ('Dirección', minor.address), ('Email', minor.email)]
            for label, value in fields:
                self.personal_form.addRow(label, QLabel(value or '—'))
            stays = sorted(minor.stays, key=lambda item: item.sequence_number, reverse=True)
            self.stays.setRowCount(len(stays))
            for row, stay in enumerate(stays):
                vals = [str(stay.started_on), str(stay.ended_on or '—'), 'Activa' if stay.status == 'active' else 'Cerrada', stay.closure_reason or '—']
                for col, value in enumerate(vals):
                    self.stays.setItem(row, col, QTableWidgetItem(value))
            links = session.scalars(select(EventStayLink).join(Stay).where(Stay.minor_id == minor.id)).all()
            events = [session.get(Event, link.event_id) for link in links]
            events.sort(key=lambda item: item.happened_at, reverse=True)
            self.events.setRowCount(len(events))
            for row, event in enumerate(events):
                vals = [event.happened_at.astimezone().strftime('%d/%m/%Y %H:%M'), event.title, event.description, event.author_name_snapshot]
                for col, value in enumerate(vals):
                    self.events.setItem(row, col, QTableWidgetItem(value))

    def edit_personal(self):
        with session_scope(self.factory) as session:
            minor = session.get(Minor, self.minor_id)
            if minor is None:
                return
            dialog = QDialog(self)
            dialog.setWindowTitle('Modificar datos personales')
            dialog.resize(520, 560)
            layout = QVBoxLayout(dialog)
            form = QFormLayout()
            controls = {}
            for key, label, value in [
                ('given_names', 'Nombre(s) *', minor.given_names),
                ('family_names', 'Apellidos *', minor.family_names),
                ('birth_country', 'País de nacimiento', minor.birth_country or ''),
                ('locality', 'Localidad', minor.locality or ''),
                ('nationality', 'Nacionalidad', minor.nationality or ''),
                ('nif_nie', 'NIF / NIE', minor.nif_nie or ''),
                ('passport_number', 'Pasaporte', minor.passport_number or ''),
                ('address', 'Dirección', minor.address or ''),
                ('email', 'Email', minor.email or ''),
            ]:
                field = QLineEdit(value)
                controls[key] = field
                form.addRow(label, field)
            birth = QDateEdit()
            birth.setCalendarPopup(True)
            birth.setDisplayFormat('dd/MM/yyyy')
            birth.setMinimumDate(QDate(1900, 1, 1))
            birth.setSpecialValueText('No indicada')
            birth.setDate(QDate(minor.birth_date.year, minor.birth_date.month, minor.birth_date.day) if minor.birth_date else birth.minimumDate())
            form.addRow('Fecha de nacimiento', birth)
            layout.addLayout(form)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            values = {key: field.text() for key, field in controls.items()}
            values['birth_date'] = birth.date().toPython() if birth.date() > birth.minimumDate() else None
        try:
            from gestion_centro.domain.service import update_minor_personal_data
            with session_scope(self.factory) as session:
                update_minor_personal_data(session, actor_account_id=self.actor_id, minor_id=self.minor_id, **values)
            self.refresh()
            QMessageBox.information(self, 'Expediente', 'Datos modificados y cambio auditado.')
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, 'No se pudo modificar', str(exc))

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
            ("Abrir expediente", self.open_selected), ("Nuevo expediente", self.new_minor), ("Nuevo ingreso / reingreso", self.new_stay),
            ("Cerrar estancia", self.close_selected_stay), ("Registrar acontecimiento", self.new_event),
            ("Historial", self.show_history), ("Actualizar", self.refresh),
        ]:
            button = QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.table.cellDoubleClicked.connect(lambda _row, _column: self.open_selected())
        self.refresh()

    def open_selected(self):
        minor_id, _stay_id = self.selected()
        if not minor_id:
            QMessageBox.information(self, 'Selecciona expediente', 'Selecciona primero un expediente.')
            return
        MinorWorkspaceDialog(self.factory, self.actor_id, minor_id, self).exec()
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
        dialog = NewMinorDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        if not values["internal_code"].strip() or not values["given_names"].strip() or not values["family_names"].strip():
            QMessageBox.warning(self, "Datos incompletos", "Código interno, nombre y apellidos son obligatorios.")
            return
        open_now = QMessageBox.question(self, "Primer ingreso",
            "¿Registrar también una estancia activa desde hoy?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        try:
            with session_scope(self.factory) as session:
                minor = create_minor(session, actor_account_id=self.actor_id, **values)
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
