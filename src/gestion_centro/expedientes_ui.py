"""Consulta y gestión básica de expedientes y estancias."""
from datetime import date, datetime, timezone

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog,
    QLabel, QDateEdit, QTabWidget, QWidget, QTextEdit, QScrollArea, QComboBox,
)
from sqlalchemy import select

from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.models import Minor, Stay, Event, EventStayLink, MinorPersonalDataVersion
from gestion_centro.domain.service import (
    create_minor, open_stay, close_stay, record_event,
    has_health_access, audit_minor_health_access, HEALTH_PERSONAL_FIELDS,
)


class NewMinorDialog(QDialog):
    """Alta completa del expediente. Los campos complementarios son opcionales."""

    def __init__(self, parent=None, *, health_access=False):
        super().__init__(parent)
        self.health_access = health_access
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
        if self.health_access:
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
        with session_scope(factory) as session:
            self.health_access = has_health_access(session, actor_account_id=actor_id)
        self.resize(850, 600)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.personal = QWidget()
        self.personal_form = QFormLayout(self.personal)
        self.tabs.addTab(self.personal, 'Datos personales')
        self.health_data = QWidget()
        self.health_form = QFormLayout(self.health_data)
        if self.health_access:
            self.tabs.addTab(self.health_data, 'Datos sanitarios')
        self.stays = QTableWidget(0, 4)
        self.stays.setHorizontalHeaderLabels(['Ingreso', 'Salida', 'Estado', 'Motivo'])
        self.stays.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.stays, 'Estancias')
        self.events = QTableWidget(0, 4)
        self.events.setHorizontalHeaderLabels(['Fecha', 'Acontecimiento', 'Descripción', 'Autor'])
        self.events.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.events, 'Acontecimientos')
        actions = QHBoxLayout()
        for label, callback in [('Nuevo ingreso / reingreso', self.new_stay), ('Cerrar estancia', self.close_stay), ('Registrar acontecimiento', self.add_event), ('Historial completo', lambda: self.tabs.setCurrentWidget(self.events))]:
            button = QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        edit = QPushButton('Modificar datos')
        edit.clicked.connect(self.edit_personal)
        actions.addWidget(edit)
        history = QPushButton('Historial de modificaciones')
        history.clicked.connect(self.show_personal_history)
        actions.addWidget(history)
        health = QPushButton('Ficha sanitaria y medicación')
        health.clicked.connect(self.open_health)
        actions.addWidget(health)
        education = QPushButton('Seguimiento educativo')
        education.clicked.connect(self.open_education)
        actions.addWidget(education)
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
            fields = [('Código', minor.internal_code), ('Nombre', minor.given_names), ('Apellidos', minor.family_names), ('País de nacimiento', minor.birth_country), ('Localidad', minor.locality), ('Nacionalidad', minor.nationality), ('Fecha nacimiento', str(minor.birth_date or '—')), ('Edad', str(minor.age) if minor.age is not None else '—'), ('NIF/NIE', minor.nif_nie), ('Pasaporte', minor.passport_number), ('Dirección', minor.address), ('Email', minor.email)]
            for label, value in fields:
                self.personal_form.addRow(label, QLabel(value or '—'))
            while self.health_form.rowCount():
                self.health_form.removeRow(0)
            if self.health_access:
                audit_minor_health_access(session, actor_account_id=self.actor_id, minor_id=minor.id)
                health_fields = [('CIP', minor.cip), ('Centro de salud', minor.health_center),
                    ('Facultativo', minor.physician), ('Enfermera', minor.nurse),
                    ('Caducidad tarjeta sanitaria', str(minor.health_card_expires_on or '—')),
                    ('Historial clínico', minor.clinical_history)]
                for label, value in health_fields:
                    display = QTextEdit()
                    display.setReadOnly(True)
                    display.setMaximumHeight(90 if label == 'Historial clínico' else 42)
                    display.setPlainText(value or '—')
                    self.health_form.addRow(label, display)
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


    def current_stay(self):
        with session_scope(self.factory) as session:
            minor = session.get(Minor, self.minor_id)
            if minor is None:
                return None
            stays = sorted(minor.stays, key=lambda item: item.sequence_number, reverse=True)
            active = next((item for item in stays if item.status == 'active'), None)
            return active.id if active else (stays[0].id if stays else None)

    def new_stay(self):
        value, ok = QInputDialog.getText(self, 'Nuevo ingreso', 'Fecha de ingreso (DD/MM/AAAA):', text=date.today().strftime('%d/%m/%Y'))
        if not ok:
            return
        try:
            start = datetime.strptime(value, '%d/%m/%Y').date()
            with session_scope(self.factory) as session:
                open_stay(session, actor_account_id=self.actor_id, minor_id=self.minor_id, started_on=start)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, 'No se pudo abrir la estancia', str(exc))

    def close_stay(self):
        stay_id = self.current_stay()
        if not stay_id:
            QMessageBox.information(self, 'Estancias', 'No hay ninguna estancia que cerrar.')
            return
        reason, ok = QInputDialog.getMultiLineText(self, 'Cerrar estancia', 'Motivo del cierre:')
        if not ok or not reason.strip():
            return
        try:
            with session_scope(self.factory) as session:
                close_stay(session, actor_account_id=self.actor_id, stay_id=stay_id, ended_on=date.today(), reason=reason)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, 'No se pudo cerrar', str(exc))

    def add_event(self):
        stay_id = self.current_stay()
        if not stay_id:
            QMessageBox.information(self, 'Acontecimientos', 'Registra primero un ingreso.')
            return
        title, ok = QInputDialog.getText(self, 'Acontecimiento', 'Título:')
        if not ok or not title.strip():
            return
        description, ok = QInputDialog.getMultiLineText(self, 'Acontecimiento', 'Descripción objetiva:')
        if not ok or not description.strip():
            return
        try:
            with session_scope(self.factory) as session:
                record_event(session, author_account_id=self.actor_id, title=title, description=description, happened_at=datetime.now(timezone.utc), stay_ids=[stay_id])
            self.refresh()
            self.tabs.setCurrentWidget(self.events)
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, 'No se pudo registrar', str(exc))

    def show_personal_history(self):
        with session_scope(self.factory) as session:
            versions = session.scalars(
                select(MinorPersonalDataVersion)
                .where(MinorPersonalDataVersion.minor_id == self.minor_id)
                .order_by(MinorPersonalDataVersion.changed_at.desc())
            ).all()
            if self.health_access:
                audit_minor_health_access(session, actor_account_id=self.actor_id, minor_id=self.minor_id)
            rows = []
            for version in versions:
                visible_fields = [
                    field for field in version.new_values
                    if self.health_access or field not in HEALTH_PERSONAL_FIELDS
                ]
                if visible_fields:
                    rows.append(
                        f"{version.changed_at.astimezone().strftime('%d/%m/%Y %H:%M')} · {version.changed_by_name_snapshot}\n" +
                        "\n".join(
                            f"{field}: {version.old_values.get(field)!r} → {version.new_values.get(field)!r}"
                            for field in visible_fields
                        )
                    )
        dialog = QDialog(self)
        dialog.setWindowTitle('Historial de modificaciones')
        dialog.resize(700, 500)
        layout = QVBoxLayout(dialog)
        details = QTextEdit()
        details.setReadOnly(True)
        details.setPlainText('\n\n'.join(rows) if rows else 'No hay modificaciones registradas.')
        layout.addWidget(details)
        close = QPushButton('Cerrar')
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.exec()

    def active_stay_id(self):
        with session_scope(self.factory) as session:
            stay = session.scalar(select(Stay.id).where(
                Stay.minor_id == self.minor_id, Stay.status == "active"
            ))
            return stay

    def open_health(self):
        # La ficha sanitaria pertenece al residente y puede consultarse aunque
        # no tenga una estancia activa. Las actuaciones de medicación mantienen
        # su vínculo con el ingreso en el que se registran.
        stay_id = self.active_stay_id()
        from gestion_centro.care_ui import HealthDialog
        HealthDialog(self.factory, self.actor_id, stay_id=stay_id).exec()
        self.refresh()

    def open_education(self):
        stay_id = self.active_stay_id()
        if not stay_id:
            QMessageBox.information(self, "Seguimiento educativo", "El expediente no tiene una estancia activa.")
            return
        from gestion_centro.care_ui import EducationDialog
        EducationDialog(self.factory, self.actor_id, stay_id=stay_id).exec()
        self.refresh()

    def edit_personal(self):
        with session_scope(self.factory) as session:
            minor = session.get(Minor, self.minor_id)
            if minor is None:
                return
            dialog = QDialog(self)
            dialog.setWindowTitle('Modificar datos del expediente')
            dialog.resize(650, 700)
            layout = QVBoxLayout(dialog)
            tabs = QTabWidget()
            personal_tab = QWidget()
            personal_form = QFormLayout(personal_tab)
            health_tab = QWidget()
            health_form = QFormLayout(health_tab)
            controls = {}
            for key, label, value in [
                ('given_names', 'Nombre(s) *', minor.given_names),
                ('family_names', 'Apellidos *', minor.family_names),
                ('birth_country', 'País de nacimiento', minor.birth_country),
                ('locality', 'Localidad', minor.locality),
                ('nationality', 'Nacionalidad', minor.nationality),
                ('nif_nie', 'NIF / NIE', minor.nif_nie),
                ('passport_number', 'Pasaporte', minor.passport_number),
                ('address', 'Dirección', minor.address),
                ('email', 'Email', minor.email),
            ]:
                field = QLineEdit(value or '')
                controls[key] = field
                personal_form.addRow(label, field)
            birth = QDateEdit()
            birth.setCalendarPopup(True)
            birth.setDisplayFormat('dd/MM/yyyy')
            birth.setMinimumDate(QDate(1900, 1, 1))
            birth.setSpecialValueText('No indicada')
            birth.setDate(QDate(minor.birth_date.year, minor.birth_date.month, minor.birth_date.day) if minor.birth_date else birth.minimumDate())
            personal_form.addRow('Fecha de nacimiento', birth)
            age_label = QLabel(str(minor.age) if minor.age is not None else '—')
            personal_form.addRow('Edad (calculada)', age_label)
            def refresh_age(selected):
                if selected <= birth.minimumDate():
                    age_label.setText('—')
                    return
                today = QDate.currentDate()
                years = today.year() - selected.year() - (
                    (today.month(), today.day()) < (selected.month(), selected.day())
                )
                age_label.setText(str(years))
            birth.dateChanged.connect(refresh_age)
            refresh_age(birth.date())
            expiry = QDateEdit()
            expiry.setCalendarPopup(True)
            expiry.setDisplayFormat('dd/MM/yyyy')
            expiry.setMinimumDate(QDate(1900, 1, 1))
            expiry.setSpecialValueText('No indicada')
            expiry.setDate(QDate(minor.health_card_expires_on.year, minor.health_card_expires_on.month, minor.health_card_expires_on.day) if minor.health_card_expires_on else expiry.minimumDate())
            clinical = None
            if self.health_access:
                audit_minor_health_access(session, actor_account_id=self.actor_id, minor_id=minor.id)
                for key, label, value in [
                    ('cip', 'CIP', minor.cip), ('health_center', 'Centro de salud', minor.health_center),
                    ('physician', 'Facultativo', minor.physician), ('nurse', 'Enfermera', minor.nurse),
                ]:
                    field = QLineEdit(value or '')
                    controls[key] = field
                    health_form.addRow(label, field)
                health_form.addRow('Caducidad tarjeta sanitaria', expiry)
                clinical = QTextEdit()
                clinical.setPlainText(minor.clinical_history or '')
                health_form.addRow('Historial clínico', clinical)
            tabs.addTab(personal_tab, 'Datos personales')
            if self.health_access:
                tabs.addTab(health_tab, 'Datos sanitarios')
            layout.addWidget(tabs)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            values = {key: field.text() for key, field in controls.items()}
            values['birth_date'] = birth.date().toPython() if birth.date() > birth.minimumDate() else None
            if self.health_access:
                values['health_card_expires_on'] = expiry.date().toPython() if expiry.date() > expiry.minimumDate() else None
                values['clinical_history'] = clinical.toPlainText()
        try:
            from gestion_centro.domain.service import update_minor_personal_data
            with session_scope(self.factory) as session:
                update_minor_personal_data(session, actor_account_id=self.actor_id, minor_id=self.minor_id, **values)
            self.refresh()
            QMessageBox.information(self, 'Expediente', 'Datos modificados y cambio versionado y auditado.')
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, 'No se pudo modificar', str(exc))

class ExpedientesDialog(QDialog):
    def __init__(self, factory, actor_id):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        with session_scope(factory) as session:
            self.health_access = has_health_access(session, actor_account_id=actor_id)
        self.setWindowTitle("Expedientes y estancias")
        self.resize(980, 620)
        layout = QVBoxLayout(self)
        intro = QLabel("Cada residente dispone de un expediente único. Los ingresos y reingresos se consultan como estancias independientes.")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText("Buscar por código o nombre…")
        self.search.textChanged.connect(self.refresh)
        filters.addWidget(self.search, 2)
        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos los expedientes", "all")
        self.status_filter.addItem("Expedientes activos", "active")
        self.status_filter.addItem("Expedientes inactivos", "inactive")
        self.status_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.status_filter, 1)
        self.stay_filter = QComboBox()
        self.stay_filter.addItem("Todas las estancias", "all")
        self.stay_filter.addItem("Ingresos activos", "active")
        self.stay_filter.addItem("Ingresos cerrados", "closed")
        self.stay_filter.addItem("Sin ingresos", "none")
        self.stay_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.stay_filter, 1)
        layout.addLayout(filters)
        self.summary = QLabel()
        self.summary.setStyleSheet("color: #53677D; padding: 2px 1px 6px 1px;")
        layout.addWidget(self.summary)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Código", "Nombre", "Estado expediente", "Estancia", "Ingreso"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        for label, callback in [
            ("Abrir expediente", self.open_selected), ("Nuevo expediente", self.new_minor),
            ("Actualizar", self.refresh),
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
        minor_status = self.status_filter.currentData()
        stay_status = self.stay_filter.currentData()
        with session_scope(self.factory) as session:
            minors = session.scalars(select(Minor).order_by(Minor.internal_code)).all()
            rows = []
            for minor in minors:
                if minor_status == "active" and not minor.active:
                    continue
                if minor_status == "inactive" and minor.active:
                    continue
                name = f"{minor.given_names} {minor.family_names}"
                if term and term not in minor.internal_code.casefold() and term not in name.casefold():
                    continue
                stays = sorted(minor.stays, key=lambda x: x.sequence_number, reverse=True)
                if stay_status == "none":
                    selected_stays = [] if stays else [None]
                elif stay_status == "active":
                    selected_stays = [stay for stay in stays if stay.status == "active"]
                elif stay_status == "closed":
                    selected_stays = [stay for stay in stays if stay.status != "active"]
                else:
                    selected_stays = stays if stays else [None]
                for stay in selected_stays:
                    rows.append((minor.id, stay.id if stay else None, minor.internal_code,
                        name, "Activo" if minor.active else "Inactivo",
                        ("Activa" if stay.status == "active" else "Cerrada") if stay else "Sin ingresos",
                        stay.started_on.strftime("%d/%m/%Y") if stay else "—"))
        self.summary.setText(
            f"{len(rows)} resultado(s) · {len({row[0] for row in rows})} expediente(s)"
        )
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
        dialog = NewMinorDialog(self, health_access=self.health_access)
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
