"""Consulta y gestión básica de expedientes y estancias."""
from datetime import date, datetime, timezone

from PySide6.QtCore import Qt, QDate, QDateTime
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog,
    QLabel, QDateEdit, QTabWidget, QWidget, QTextEdit, QScrollArea, QComboBox, QDateTimeEdit, QDialogButtonBox, QCheckBox, QGridLayout,
)
from sqlalchemy import select

from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.models import Minor, Stay, Event, EventStayLink, MinorPersonalDataVersion
from gestion_centro.domain.documents_service import list_documents
from gestion_centro.domain.service import (
    create_minor, open_stay, close_stay, record_event, update_stay, revise_event,
    HEALTH_PERSONAL_FIELDS,
)


class NewMinorDialog(QDialog):
    """Alta de menor con los campos de la ficha simplificada."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo expediente")
        self.resize(760, 760)
        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs)

        personal = QWidget()
        personal_form = QFormLayout(personal)
        self.given = QLineEdit()
        self.family = QLineEdit()
        self.sex = QComboBox()
        self.sex.addItem("No indicado", "")
        self.sex.addItem("Femenino", "female")
        self.sex.addItem("Masculino", "male")
        self.sex.addItem("Otro", "other")
        self.birth_date = self._date_field()
        self.age_label = QLabel("—")
        self.birth_date.dateChanged.connect(self.update_age)
        self.locality = QLineEdit()
        self.birth_country = QLineEdit()
        self.nationality = QLineEdit()
        self.address = QTextEdit()
        self.address.setMaximumHeight(70)
        self.postal_code = QLineEdit()
        self.nif_nie = QLineEdit()
        self.email = QLineEdit()
        self.mobile_phone = QLineEdit()
        for label, widget in [
            ("Nombre *", self.given), ("Apellidos *", self.family),
            ("Sexo", self.sex), ("Fecha de nacimiento", self.birth_date),
            ("Edad (calculada)", self.age_label), ("Lugar de nacimiento", self.locality),
            ("País de nacimiento", self.birth_country), ("Nacionalidad", self.nationality),
            ("Dirección actual", self.address), ("Código postal", self.postal_code),
            ("NIF/NIE", self.nif_nie), ("Email", self.email),
            ("Nº teléfono móvil", self.mobile_phone),
        ]:
            personal_form.addRow(label, widget)
        tabs.addTab(personal, "1. Datos generales")

        sanitary = QWidget()
        sanitary_form = QFormLayout(sanitary)
        self.cip = QLineEdit()
        self.card_issued = self._date_field()
        self.card_expires = self._date_field()
        self.health_center = QLineEdit()
        self.physician = QLineEdit()
        self.nurse = QLineEdit()
        self.clinical_history = QTextEdit()
        self.clinical_history.setMinimumHeight(100)
        for label, widget in [
            ("CIP", self.cip), ("Fecha de emisión", self.card_issued),
            ("Fecha de caducidad", self.card_expires),
            ("Centro de salud asignado", self.health_center),
            ("Facultativo asignado", self.physician),
            ("Enfermería asignada", self.nurse),
            ("Enfermedades y tratamientos", self.clinical_history),
        ]:
            sanitary_form.addRow(label, widget)
        tabs.addTab(sanitary, "2. Información sanitaria")

        documents = QWidget()
        documents_layout = QVBoxLayout(documents)
        note = QLabel("Los documentos escaneados se añadirán y consultarán desde la pestaña Documentos de la ficha, una vez creado el expediente.")
        note.setWordWrap(True)
        documents_layout.addWidget(note)
        documents_layout.addStretch(1)
        tabs.addTab(documents, "3. Documentos")

        buttons = QHBoxLayout()
        save = QPushButton("Crear expediente")
        cancel = QPushButton("Cancelar")
        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        root.addLayout(buttons)

    @staticmethod
    def _date_field():
        field = QDateEdit()
        field.setCalendarPopup(True)
        field.setDisplayFormat("dd/MM/yyyy")
        field.setMinimumDate(QDate(1900, 1, 1))
        field.setSpecialValueText("No indicada")
        field.setDate(field.minimumDate())
        return field

    def update_age(self, selected):
        if selected <= self.birth_date.minimumDate():
            self.age_label.setText("—")
            return
        born = selected.toPython()
        today = date.today()
        years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        self.age_label.setText(str(years))

    def _optional_date(self, field):
        return field.date().toPython() if field.date() > field.minimumDate() else None

    def values(self):
        return {
            "given_names": self.given.text(),
            "family_names": self.family.text(),
            "sex": self.sex.currentData(),
            "birth_date": self._optional_date(self.birth_date),
            "locality": self.locality.text(),
            "birth_country": self.birth_country.text(),
            "nationality": self.nationality.text(),
            "address": self.address.toPlainText(),
            "postal_code": self.postal_code.text(),
            "nif_nie": self.nif_nie.text(),
            "email": self.email.text(),
            "mobile_phone": self.mobile_phone.text(),
            "cip": self.cip.text(),
            "health_card_issued_on": self._optional_date(self.card_issued),
            "health_card_expires_on": self._optional_date(self.card_expires),
            "health_center": self.health_center.text(),
            "physician": self.physician.text(),
            "nurse": self.nurse.text(),
            "clinical_history": self.clinical_history.toPlainText(),
        }


class MinorWorkspaceDialog(QDialog):
    def __init__(self, factory, actor_id, minor_id, parent=None, documents_opener=None):
        super().__init__(parent)
        self.factory, self.actor_id, self.minor_id = factory, actor_id, minor_id
        self.documents_opener = documents_opener
        self.resize(980, 680)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.personal = QWidget()
        self.personal_form = QFormLayout(self.personal)
        self.tabs.addTab(self.personal, "1. Datos generales")
        self.sanitary = QWidget()
        self.sanitary_form = QFormLayout(self.sanitary)
        self.tabs.addTab(self.sanitary, "2. Información sanitaria")
        health_management = QPushButton("Gestionar medicación, administraciones y vacunas")
        health_management.clicked.connect(self.open_health)
        self.sanitary_form.addRow(health_management)
        self.stays = QTableWidget(0, 5)
        self.stays.setHorizontalHeaderLabels(['ID', 'Ingreso', 'Salida', 'Estado', 'Motivo'])
        self.stays.setColumnHidden(0, True)
        self.stays.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stays.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.stays, 'Estancias')
        self.events = QTableWidget(0, 5)
        self.events.setHorizontalHeaderLabels(['ID', 'Fecha', 'Acontecimiento', 'Descripción', 'Autor'])
        self.events.setColumnHidden(0, True)
        self.events.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.events.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.events, 'Acontecimientos')
        documents_tab = QWidget()
        documents_layout = QVBoxLayout(documents_tab)
        documents_info = QLabel('Los documentos se conservan vinculados a cada ingreso o reingreso. Puedes consultar el historial documental de todas las estancias desde aquí.')
        documents_info.setWordWrap(True)
        documents_layout.addWidget(documents_info)
        self.documents_table = QTableWidget(0, 5)
        self.documents_table.setHorizontalHeaderLabels(['Documento', 'Categoría', 'Archivo', 'Versión', 'Caducidad'])
        self.documents_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.documents_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.documents_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        documents_layout.addWidget(self.documents_table)
        documents_button = QPushButton('Añadir o consultar documentación')
        documents_button.clicked.connect(self.open_documents)
        documents_layout.addWidget(documents_button)
        documents_layout.addStretch(1)
        self.tabs.addTab(documents_tab, '3. Documentos escaneados')
        actions = QGridLayout()
        actions.setHorizontalSpacing(8)
        actions.setVerticalSpacing(6)
        action_items = [
            ('Nuevo ingreso / reingreso', self.new_stay),
            ('Cerrar estancia', self.close_stay),
            ('Modificar estancia', self.edit_stay),
            ('Modificar datos', self.edit_personal),
            ('Registrar acontecimiento', self.add_event),
            ('Rectificar acontecimiento', self.edit_event),
            ('Historial acontecimiento', self.show_event_history),
            ('Historial de modificaciones', self.show_personal_history),
            ('Seguimiento educativo', self.open_education),
            ('Cerrar expediente', self.accept),
        ]
        for index, (label, callback) in enumerate(action_items):
            button = QPushButton(label)
            button.setMinimumHeight(34)
            button.clicked.connect(callback)
            actions.addWidget(button, index // 4, index % 4)
        layout.addLayout(actions)
        self.refresh()

    def refresh(self):
        with session_scope(self.factory) as session:
            minor = session.get(Minor, self.minor_id)
            if minor is None:
                self.reject()
                return
            self.setWindowTitle('Expediente · ' + (minor.nif_nie or minor.passport_number or 'Sin NIF/NIE') + ' · ' + minor.given_names + ' ' + minor.family_names)
            while self.personal_form.rowCount():
                self.personal_form.removeRow(0)
            general_fields = [
                ("Nombre", minor.given_names), ("Apellidos", minor.family_names),
                ("Sexo", {"female": "Femenino", "male": "Masculino", "other": "Otro"}.get(minor.sex, "—")),
                ("Fecha de nacimiento", str(minor.birth_date or "—")),
                ("Edad", str(minor.age) if minor.age is not None else "—"),
                ("Lugar de nacimiento", minor.locality), ("País de nacimiento", minor.birth_country),
                ("Nacionalidad", minor.nationality), ("Dirección actual", minor.address),
                ("Código postal", minor.postal_code), ("NIF/NIE", minor.nif_nie),
                ("Email", minor.email), ("Teléfono móvil", minor.mobile_phone),
            ]
            sanitary_fields = [
                ("CIP", minor.cip), ("Fecha de emisión", str(minor.health_card_issued_on or "—")),
                ("Fecha de caducidad", str(minor.health_card_expires_on or "—")),
                ("Centro de salud asignado", minor.health_center), ("Facultativo asignado", minor.physician),
                ("Enfermería asignada", minor.nurse), ("Enfermedades y tratamientos", minor.clinical_history),
            ]
            for form_widget, fields in ((self.personal_form, general_fields), (self.sanitary_form, sanitary_fields)):
                while form_widget.rowCount():
                    form_widget.removeRow(0)
                for label, value in fields:
                    form_widget.addRow(label, QLabel(value or "—"))
            stays = sorted(minor.stays, key=lambda item: item.sequence_number, reverse=True)
            documents = []
            for stay in stays:
                documents.extend(list_documents(session, actor_account_id=self.actor_id, stay_id=stay.id))
            documents.sort(key=lambda item: item.created_at, reverse=True)
            self.documents_table.setRowCount(len(documents))
            for row, document in enumerate(documents):
                values = [document.title, document.category, document.original_filename,
                          str(document.version), document.expires_on.strftime('%d/%m/%Y') if document.expires_on else '—']
                for col, value in enumerate(values):
                    self.documents_table.setItem(row, col, QTableWidgetItem(value))
            self.stays.setRowCount(len(stays))
            for row, stay in enumerate(stays):
                vals = [stay.id, str(stay.started_on), str(stay.ended_on or '—'),
                        'Activa' if stay.status == 'active' else 'Cerrada', stay.closure_reason or '—']
                for col, value in enumerate(vals):
                    cell = QTableWidgetItem(str(value))
                    if col == 0:
                        cell.setData(Qt.ItemDataRole.UserRole, stay.id)
                    self.stays.setItem(row, col, cell)
            links = session.scalars(select(EventStayLink).join(Stay).where(Stay.minor_id == minor.id)).all()
            event_map = {event.id: event for event in (
                session.get(Event, link.event_id) for link in links
            ) if event is not None}
            superseded_events = {event.correction_of_id for event in event_map.values() if event.correction_of_id}
            events = [event for event in event_map.values() if event.id not in superseded_events]
            events.sort(key=lambda item: item.happened_at, reverse=True)
            self.events.setRowCount(len(events))
            for row, event in enumerate(events):
                vals = [event.id, event.happened_at.astimezone().strftime('%d/%m/%Y %H:%M'),
                        event.title, event.description, event.author_name_snapshot]
                for col, value in enumerate(vals):
                    cell = QTableWidgetItem(str(value))
                    if col == 0:
                        cell.setData(Qt.ItemDataRole.UserRole, event.id)
                    self.events.setItem(row, col, cell)


    def edit_stay(self):
        row = self.stays.currentRow()
        cell = self.stays.item(row, 0) if row >= 0 else None
        if cell is None:
            QMessageBox.information(self, 'Selecciona estancia', 'Selecciona primero una estancia.')
            return
        stay_id = cell.data(Qt.ItemDataRole.UserRole)
        with session_scope(self.factory) as session:
            stay = session.get(Stay, stay_id)
            if stay is None:
                QMessageBox.warning(self, 'No disponible', 'La estancia ya no existe.')
                return
            values = (stay.started_on, stay.ended_on, stay.status, stay.closure_reason or '')
        dialog = QDialog(self)
        dialog.setWindowTitle('Modificar estancia')
        form = QFormLayout(dialog)
        started = QDateEdit(QDate(values[0].year, values[0].month, values[0].day))
        started.setCalendarPopup(True)
        status = QComboBox()
        status.addItem('Activa', 'active')
        status.addItem('Cerrada', 'closed')
        status.setCurrentIndex(max(0, status.findData(values[2])))
        ended = QDateEdit(QDate.currentDate())
        ended.setCalendarPopup(True)
        no_end = QCheckBox('Sin fecha de salida')
        if values[1]:
            ended.setDate(QDate(values[1].year, values[1].month, values[1].day))
        else:
            no_end.setChecked(True)
        reason = QTextEdit()
        reason.setPlainText(values[3])
        def update_state():
            closed = status.currentData() == 'closed'
            no_end.setEnabled(not closed)
            ended.setEnabled(closed)
            reason.setEnabled(closed)
        status.currentIndexChanged.connect(update_state)
        update_state()
        form.addRow('Fecha de ingreso', started)
        form.addRow('Estado', status)
        form.addRow('Fecha de salida', ended)
        form.addRow('', no_end)
        form.addRow('Motivo de cierre', reason)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        final_status = status.currentData()
        try:
            with session_scope(self.factory) as session:
                update_stay(
                    session, actor_account_id=self.actor_id, stay_id=stay_id,
                    started_on=started.date().toPython(), status=final_status,
                    ended_on=ended.date().toPython() if final_status == 'closed' else None,
                    closure_reason=reason.toPlainText() if final_status == 'closed' else None,
                )
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, 'No se pudo modificar la estancia', str(exc))

    def edit_event(self):
        row = self.events.currentRow()
        cell = self.events.item(row, 0) if row >= 0 else None
        if cell is None:
            QMessageBox.information(self, 'Selecciona acontecimiento', 'Selecciona primero un acontecimiento.')
            return
        event_id = cell.data(Qt.ItemDataRole.UserRole)
        with session_scope(self.factory) as session:
            event = session.get(Event, event_id)
            if event is None:
                QMessageBox.warning(self, 'No disponible', 'El acontecimiento ya no existe.')
                return
            values = (event.title, event.description, event.happened_at)
        dialog = QDialog(self)
        dialog.setWindowTitle('Rectificar acontecimiento')
        dialog.resize(600, 460)
        form = QFormLayout(dialog)
        title = QLineEdit(values[0])
        description = QTextEdit()
        description.setPlainText(values[1])
        happened = QDateTimeEdit(QDateTime.fromPython(values[2].astimezone()))
        happened.setCalendarPopup(True)
        happened.setDisplayFormat('dd/MM/yyyy HH:mm')
        reason = QLineEdit()
        reason.setPlaceholderText('Motivo de la corrección')
        form.addRow('Título', title)
        form.addRow('Descripción', description)
        form.addRow('Fecha y hora', happened)
        form.addRow('Motivo', reason)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        moment = happened.dateTime().toPython()
        moment = moment.astimezone(timezone.utc) if moment.tzinfo else moment.astimezone().astimezone(timezone.utc)
        try:
            with session_scope(self.factory) as session:
                revise_event(
                    session, actor_account_id=self.actor_id, event_id=event_id,
                    title=title.text(), description=description.toPlainText(),
                    happened_at=moment, reason=reason.text(),
                )
            self.refresh()
            QMessageBox.information(self, 'Acontecimiento rectificado', 'Se ha creado una nueva versión y se conserva la original.')
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, 'No se pudo rectificar', str(exc))

    def show_event_history(self):
        row = self.events.currentRow()
        cell = self.events.item(row, 0) if row >= 0 else None
        if cell is None:
            QMessageBox.information(self, 'Selecciona acontecimiento', 'Selecciona primero un acontecimiento.')
            return
        event_id = cell.data(Qt.ItemDataRole.UserRole)
        with session_scope(self.factory) as session:
            current = session.get(Event, event_id)
            if current is None:
                QMessageBox.warning(self, 'No disponible', 'El acontecimiento ya no existe.')
                return
            versions = [current]
            parent_id = current.correction_of_id
            while parent_id:
                parent = session.get(Event, parent_id)
                if parent is None:
                    break
                versions.append(parent)
                parent_id = parent.correction_of_id
            versions.reverse()
            lines = []
            for number, version in enumerate(versions, start=1):
                lines.extend([
                    f"VERSIÓN {number} · {version.recorded_at.astimezone().strftime('%d/%m/%Y %H:%M')}",
                    f"Registrada por: {version.author_name_snapshot}",
                    f"Fecha del hecho: {version.happened_at.astimezone().strftime('%d/%m/%Y %H:%M')}",
                    version.title, version.description, "",
                ])
        dialog = QDialog(self)
        dialog.setWindowTitle('Historial del acontecimiento')
        dialog.resize(760, 560)
        layout = QVBoxLayout(dialog)
        viewer = QTextEdit()
        viewer.setReadOnly(True)
        viewer.setPlainText("\\n".join(lines))
        layout.addWidget(viewer)
        close = QPushButton('Cerrar')
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.exec()

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
            rows = []
            for version in versions:
                visible_fields = [
                    field for field in version.new_values
                    if field not in HEALTH_PERSONAL_FIELDS
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

    def open_documents(self):
        if self.documents_opener is None:
            QMessageBox.information(self, 'Documentación', 'Abre la sección Documentación para gestionar los archivos de este expediente.')
            return
        self.documents_opener(self.minor_id)
        self.refresh()

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
            dialog.setWindowTitle("Modificar información del menor")
            dialog.resize(760, 760)
            layout = QVBoxLayout(dialog)
            tabs = QTabWidget()
            personal_tab = QWidget()
            personal_form = QFormLayout(personal_tab)
            controls = {}
            for key, label, value in [
                ("given_names", "Nombre *", minor.given_names),
                ("family_names", "Apellidos *", minor.family_names),
                ("birth_country", "País de nacimiento", minor.birth_country),
                ("locality", "Lugar de nacimiento", minor.locality),
                ("nationality", "Nacionalidad", minor.nationality),
                ("nif_nie", "NIF/NIE", minor.nif_nie),
                ("address", "Dirección actual", minor.address),
                ("postal_code", "Código postal", minor.postal_code),
                ("email", "Email", minor.email),
                ("mobile_phone", "Nº teléfono móvil", minor.mobile_phone),
            ]:
                field = QLineEdit(value or "")
                controls[key] = field
                personal_form.addRow(label, field)
            sex = QComboBox()
            sex.addItem("No indicado", "")
            sex.addItem("Femenino", "female")
            sex.addItem("Masculino", "male")
            sex.addItem("Otro", "other")
            sex.setCurrentIndex(max(0, sex.findData(minor.sex or "")))
            birth = NewMinorDialog._date_field()
            birth.setDate(QDate(minor.birth_date.year, minor.birth_date.month, minor.birth_date.day) if minor.birth_date else birth.minimumDate())
            personal_form.addRow("Sexo", sex)
            personal_form.addRow("Fecha de nacimiento", birth)
            age_label = QLabel(str(minor.age) if minor.age is not None else "—")
            personal_form.addRow("Edad (calculada)", age_label)
            def refresh_age(selected):
                if selected <= birth.minimumDate():
                    age_label.setText("—")
                    return
                today = QDate.currentDate()
                years = today.year() - selected.year() - ((today.month(), today.day()) < (selected.month(), selected.day()))
                age_label.setText(str(years))
            birth.dateChanged.connect(refresh_age)
            tabs.addTab(personal_tab, "1. Datos generales")

            sanitary_tab = QWidget()
            sanitary_form = QFormLayout(sanitary_tab)
            health_controls = {}
            for key, label, value in [
                ("cip", "CIP", minor.cip), ("health_center", "Centro de salud asignado", minor.health_center),
                ("physician", "Facultativo asignado", minor.physician), ("nurse", "Enfermería asignada", minor.nurse),
            ]:
                field = QLineEdit(value or "")
                health_controls[key] = field
                sanitary_form.addRow(label, field)
            issued = NewMinorDialog._date_field()
            expires = NewMinorDialog._date_field()
            for widget, value in ((issued, minor.health_card_issued_on), (expires, minor.health_card_expires_on)):
                if value:
                    widget.setDate(QDate(value.year, value.month, value.day))
            clinical = QTextEdit()
            clinical.setPlainText(minor.clinical_history or "")
            clinical.setMinimumHeight(100)
            sanitary_form.addRow("Fecha de emisión", issued)
            sanitary_form.addRow("Fecha de caducidad", expires)
            sanitary_form.addRow("Enfermedades y tratamientos", clinical)
            tabs.addTab(sanitary_tab, "2. Información sanitaria")
            layout.addWidget(tabs)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            values = {key: field.text() for key, field in controls.items()}
            values.update({key: field.text() for key, field in health_controls.items()})
            values["sex"] = sex.currentData()
            values["birth_date"] = birth.date().toPython() if birth.date() > birth.minimumDate() else None
            values["health_card_issued_on"] = issued.date().toPython() if issued.date() > issued.minimumDate() else None
            values["health_card_expires_on"] = expires.date().toPython() if expires.date() > expires.minimumDate() else None
            values["clinical_history"] = clinical.toPlainText()
        try:
            from gestion_centro.domain.service import update_minor_personal_data
            with session_scope(self.factory) as session:
                update_minor_personal_data(session, actor_account_id=self.actor_id, minor_id=self.minor_id, **values)
            self.refresh()
            QMessageBox.information(self, "Información del menor", "Los cambios se han guardado y quedan versionados y auditados.")
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo modificar", str(exc))

class ExpedientesDialog(QDialog):
    def __init__(self, factory, actor_id, documents_opener=None):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.documents_opener = documents_opener
        self.setWindowTitle("Expedientes y estancias")
        self.resize(980, 620)
        layout = QVBoxLayout(self)
        intro = QLabel("Cada residente dispone de un expediente único. Los ingresos y reingresos se consultan como estancias independientes.")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText("Buscar por NIF/NIE, nombre o pasaporte…")
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
        self.table.setHorizontalHeaderLabels(["NIF/NIE", "Nombre", "Estado expediente", "Estancia", "Ingreso"])
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
        MinorWorkspaceDialog(self.factory, self.actor_id, minor_id, self,
                             documents_opener=self.documents_opener).exec()
        self.refresh()

    def refresh(self):
        term = self.search.text().strip().casefold()
        minor_status = self.status_filter.currentData()
        stay_status = self.stay_filter.currentData()
        with session_scope(self.factory) as session:
            minors = session.scalars(select(Minor).order_by(Minor.family_names, Minor.given_names)).all()
            rows = []
            for minor in minors:
                if minor_status == "active" and not minor.active:
                    continue
                if minor_status == "inactive" and minor.active:
                    continue
                name = f"{minor.given_names} {minor.family_names}"
                if term and term not in (minor.nif_nie or "").casefold() and term not in (minor.passport_number or "").casefold() and term not in name.casefold():
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
                    rows.append((minor.id, stay.id if stay else None, minor.nif_nie or "—",
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
        dialog = NewMinorDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        if not values["given_names"].strip() or not values["family_names"].strip():
            QMessageBox.warning(self, "Datos incompletos", "El nombre y los apellidos son obligatorios.")
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
