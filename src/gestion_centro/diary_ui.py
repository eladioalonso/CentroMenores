"""Interfaz básica de diario e incidencias con autoría y cierre trazable."""
from datetime import datetime, timezone

from PySide6.QtCore import QDate, QDateTime, Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QDateEdit, QDateTimeEdit,
    QComboBox, QLineEdit, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QListWidget, QListWidgetItem,
    QDialogButtonBox, QLabel, QInputDialog,
)
from sqlalchemy import select

from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.models import DiaryEntry, DiaryEntryStayLink, Stay
from gestion_centro.domain.service import (
    record_diary_entry, close_diary_day, revise_diary_entry,
    list_diary_records,
)
from gestion_centro.domain.documents_service import list_active_stays, list_document_stays


class DiaryDialog(QDialog):
    CATEGORIES = {
        "Actividades realizadas en el día": "activity",
        "Comportamientos positivos": "positive",
        "Comportamientos negativos": "negative",
        "Observaciones": "observation",
    }
    def __init__(self, factory, actor_id):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.setWindowTitle("Diario e incidencias")
        self.resize(980, 640)
        layout = QVBoxLayout(self)
        intro = QLabel("Registra las actividades del día, los comportamientos positivos o negativos y las observaciones relevantes. Las anotaciones quedan vinculadas a su autor.")
        intro.setWordWrap(True)
        intro.setObjectName("formIntro")
        layout.addWidget(intro)
        self.day_state = QLabel()
        self.day_state.setObjectName("recordState")
        layout.addWidget(self.day_state)
        self.day = QDateEdit()
        self.day.setCalendarPopup(True)
        self.day.setDate(QDate.currentDate())
        date_form = QFormLayout()
        date_form.addRow("Fecha", self.day)
        layout.addLayout(date_form)

        form = QFormLayout()
        self.day.setCalendarPopup(True)
        self.day.setDate(QDate.currentDate())
        self.category = QComboBox()
        for label, key in self.CATEGORIES.items():
            self.category.addItem(label, key)
        self.content = QTextEdit()
        self.content.setMinimumHeight(130)
        self.content.setPlaceholderText("Describe los hechos con claridad. El texto se ajustará automáticamente al ancho del cuadro.")
        self.participant_hint = QLineEdit("Sin menores vinculados")
        self.participant_hint.setReadOnly(True)
        self.selected_stay_ids = []
        form.addRow("Apartado", self.category)
        form.addRow("Contenido", self.content)
        select_stays = QPushButton("Vincular menores / estancias…")
        select_stays.clicked.connect(self.choose_stays)
        form.addRow("Personas vinculadas", self.participant_hint)
        form.addRow("", select_stays)
        layout.addLayout(form)
        actions = QHBoxLayout()
        self.add_button = QPushButton("Guardar apartado")
        self.add_button.clicked.connect(self.add_entry)
        self.close_button = QPushButton("Cerrar parte del día")
        self.close_button.clicked.connect(self.close_day)
        self.revise_button = QPushButton("Editar anotación seleccionada")
        self.revise_button.clicked.connect(self.revise_entry)
        self.history_button = QPushButton("Historial de versiones")
        self.history_button.clicked.connect(self.view_entry_history)
        refresh = QPushButton("Actualizar")
        refresh.clicked.connect(self.refresh)
        for b in (self.add_button, self.close_button, self.revise_button, self.history_button, refresh): actions.addWidget(b)
        layout.addLayout(actions)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Hora", "Apartado / tipo", "Contenido", "Autor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        self.table.itemSelectionChanged.connect(self._update_selection_actions)
        self.day.dateChanged.connect(self.refresh)
        self.refresh()

    def choose_stays(self, include_closed=False):
        dialog = QDialog(self)
        dialog.setWindowTitle("Vincular menores y estancias activas")
        dialog.resize(520, 420)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Marca únicamente a los menores implicados. Para un hecho general, deja la selección vacía."))
        choices = QListWidget()
        with session_scope(self.factory) as session:
            stays = (
                list_document_stays(session, actor_account_id=self.actor_id)
                if include_closed else list_active_stays(session, actor_account_id=self.actor_id)
            )
            rows = [(s.id, f"{(s.minor.nif_nie or s.minor.passport_number or 'Sin NIF/NIE')} · "
                     f"{s.minor.given_names} {s.minor.family_names} · "
                     f"{'Activa' if s.status == 'active' else 'Cerrada'}") for s in stays]
        for stay_id, label in rows:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, stay_id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if stay_id in self.selected_stay_ids else Qt.CheckState.Unchecked)
            choices.addItem(item)
        layout.addWidget(choices)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_stay_ids = [choices.item(i).data(Qt.ItemDataRole.UserRole) for i in range(choices.count()) if choices.item(i).checkState() == Qt.CheckState.Checked]
            self.participant_hint.setText(f"{len(self.selected_stay_ids)} estancia(s) vinculada(s)" if self.selected_stay_ids else "Sin menores vinculados")

    def add_entry(self):
        try:
            local_now = datetime.now().astimezone()
            local = datetime.combine(self.day.date().toPython(), local_now.time().replace(tzinfo=None))
            moment = local.astimezone().astimezone(timezone.utc)
            with session_scope(self.factory) as session:
                record_diary_entry(session, actor_account_id=self.actor_id,
                    diary_date=self.day.date().toPython(), shift="unspecified",
                    category=self.category.currentData(), content=self.content.toPlainText(),
                    happened_at=moment, stay_ids=self.selected_stay_ids)
            self.content.clear()
            self.selected_stay_ids = []
            self.participant_hint.setText("Sin menores vinculados")
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

    def revise_entry(self):
        row = self.table.currentRow()
        cell = self.table.item(row, 0) if row >= 0 else None
        metadata = cell.data(Qt.ItemDataRole.UserRole) if cell else None
        if not metadata or metadata.get("kind") != "entry":
            QMessageBox.information(self, "Selecciona una anotación", "Selecciona una anotación del parte diario.")
            return
        try:
            with session_scope(self.factory) as session:
                entry = session.get(DiaryEntry, metadata["id"])
                if entry is None:
                    raise ValueError("La anotación ya no existe.")
                original = {
                    "content": entry.content, "shift": entry.shift,
                    "category": entry.category, "happened_at": entry.happened_at,
                    "stay_ids": [link.stay_id for link in session.scalars(
                        select(DiaryEntryStayLink).where(DiaryEntryStayLink.entry_id == entry.id)
                    ).all()],
                }
            self.selected_stay_ids = list(original["stay_ids"])
            self.participant_hint.setText(
                f"{len(self.selected_stay_ids)} estancia(s) vinculada(s)"
                if self.selected_stay_ids else "Sin menores vinculados"
            )

            dialog = QDialog(self)
            dialog.setWindowTitle("Revisar anotación del parte diario")
            dialog.resize(680, 520)
            form = QFormLayout(dialog)
            category = QComboBox()
            categories = dict(self.CATEGORIES)
            categories.update({
                "General (histórico)": "general", "Salud (histórico)": "health",
                "Mantenimiento (histórico)": "maintenance", "Otros (histórico)": "other",
            })
            for label, key in categories.items():
                category.addItem(label, key)
            category.setCurrentIndex(max(0, category.findData(original["category"])))
            happened = QDateTimeEdit()
            happened.setCalendarPopup(True)
            happened.setDisplayFormat("dd/MM/yyyy HH:mm")
            happened.setDateTime(QDateTime.fromPython(original["happened_at"].astimezone()))
            content = QTextEdit()
            content.setPlainText(original["content"])
            reason = QLineEdit()
            reason.setPlaceholderText("Motivo breve de la corrección")
            form.addRow("Apartado", category)
            form.addRow("Fecha y hora del hecho", happened)
            form.addRow("Contenido", content)
            form.addRow("Motivo de modificación", reason)
            participants = QPushButton("Modificar menores / estancias vinculadas…")
            participants.clicked.connect(lambda: self.choose_stays(include_closed=True))
            form.addRow("Personas vinculadas", self.participant_hint)
            form.addRow("", participants)
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            form.addRow(buttons)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            if not content.toPlainText().strip() or not reason.text().strip():
                QMessageBox.warning(self, "Datos incompletos", "El contenido y el motivo son obligatorios.")
                return
            local_moment = happened.dateTime().toPython()
            moment = local_moment.astimezone(timezone.utc) if local_moment.tzinfo else local_moment.astimezone().astimezone(timezone.utc)
            with session_scope(self.factory) as session:
                revise_diary_entry(
                    session, actor_account_id=self.actor_id,
                    original_entry_id=metadata["id"],
                    content=content.toPlainText(), reason=reason.text(),
                    happened_at=moment, shift=original["shift"],
                    category=category.currentData(),
                    stay_ids=self.selected_stay_ids,
                )
            self.selected_stay_ids = []
            self.participant_hint.setText("Sin menores vinculados")
            self.refresh()
            QMessageBox.information(
                self, "Modificación guardada",
                "Se ha creado una nueva versión. El texto anterior y sus vínculos se conservan, "
                "y queda registrada la persona que realizó la modificación."
            )
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo modificar", str(exc))

    def _update_selection_actions(self):
        row = self.table.currentRow()
        cell = self.table.item(row, 0) if row >= 0 else None
        metadata = cell.data(Qt.ItemDataRole.UserRole) if cell else None
        selected_entry = bool(metadata and metadata.get("kind") == "entry")
        self.revise_button.setEnabled(selected_entry)
        self.history_button.setEnabled(selected_entry)

    def view_entry_history(self):
        row = self.table.currentRow()
        cell = self.table.item(row, 0) if row >= 0 else None
        metadata = cell.data(Qt.ItemDataRole.UserRole) if cell else None
        if not metadata or metadata.get("kind") != "entry":
            QMessageBox.information(self, "Selecciona una anotación", "Selecciona primero una anotación del parte.")
            return
        try:
            with session_scope(self.factory) as session:
                current = session.get(DiaryEntry, metadata["id"])
                if current is None:
                    raise ValueError("La anotación ya no existe.")
                versions = [current]
                parent_id = current.correction_of_id
                while parent_id:
                    parent = session.get(DiaryEntry, parent_id)
                    if parent is None:
                        break
                    versions.append(parent)
                    parent_id = parent.correction_of_id
                versions.reverse()
                history = []
                for number, version in enumerate(versions, start=1):
                    history.extend([
                        f"VERSIÓN {number} · {version.recorded_at.astimezone().strftime('%d/%m/%Y %H:%M')}",
                        f"Registrada por: {version.author_name_snapshot}",
                        f"Fecha del hecho: {version.happened_at.astimezone().strftime('%d/%m/%Y %H:%M')}",
                        version.content, "",
                    ])
            dialog = QDialog(self)
            dialog.setWindowTitle("Historial de la anotación")
            dialog.resize(760, 560)
            layout = QVBoxLayout(dialog)
            viewer = QTextEdit()
            viewer.setReadOnly(True)
            viewer.setPlainText("\\n".join(history))
            layout.addWidget(viewer)
            close = QPushButton("Cerrar")
            close.clicked.connect(dialog.accept)
            layout.addWidget(close)
            dialog.exec()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo consultar el historial", str(exc))

    def close_day(self):
        if QMessageBox.question(self, "Cerrar diario",
            "El cierre impide añadir nuevas anotaciones a esta fecha. ¿Continuar?") != QMessageBox.StandardButton.Yes:
            return
        try:
            with session_scope(self.factory) as session:
                close_diary_day(session, actor_account_id=self.actor_id,
                    diary_date=self.day.date().toPython())
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo cerrar", str(exc))

    def refresh(self):
        selected = self.day.date().toPython()
        with session_scope(self.factory) as session:
            day, entries, _legacy_incidents = list_diary_records(
                session, actor_account_id=self.actor_id, diary_date=selected)
            # El parte muestra la última versión de cada anotación; las anteriores
            # se conservan y pueden consultarse desde el historial.
            superseded_ids = {entry.correction_of_id for entry in entries if entry.correction_of_id}
            entries = [entry for entry in entries if entry.id not in superseded_ids]
            category_labels = {
                "activity": "Actividades realizadas",
                "positive": "Comportamientos positivos",
                "negative": "Comportamientos negativos",
                "observation": "Observaciones",
                "admission": "Altas de usuarios",
                "discharge": "Bajas de usuarios",
                "general": "General (histórico)",
                "health": "Salud (histórico)",
                "maintenance": "Mantenimiento (histórico)",
                "other": "Otros (histórico)",
            }
            rows = [(x.happened_at, category_labels.get(x.category, x.category),
                x.content, x.author_name_snapshot,
                {"kind": "entry", "id": x.id}) for x in entries]
            rows.sort(key=lambda x: x[0])
            is_closed = bool(day and day.closed_at)
            day_details = day
        # Las anotaciones se muestran en una única cronología diaria.
        self.table.setRowCount(len(rows))
        for i, values in enumerate(rows):
            display = [values[0].astimezone().strftime("%d/%m %H:%M"), *values[1:4]]
            for j, value in enumerate(display):
                item = QTableWidgetItem(str(value))
                if j == 0:
                    item.setData(Qt.ItemDataRole.UserRole, values[4])
                self.table.setItem(i, j, item)
        self.content.setReadOnly(is_closed)
        self.add_button.setEnabled(not is_closed)
        self.close_button.setEnabled(not is_closed)
        self._update_selection_actions()
        self.day_state.setText("PARTE CERRADO · No admite nuevas anotaciones; puedes revisar las existentes" if is_closed else "PARTE ABIERTO · Puedes completar y revisar anotaciones")
        self.day_state.setProperty("closed", is_closed)
        self.day_state.style().unpolish(self.day_state)
        self.day_state.style().polish(self.day_state)
