"""Interfaz básica de diario e incidencias con autoría y cierre trazable."""
from datetime import datetime, timezone

from PySide6.QtCore import QDate, QDateTime, Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QDateEdit, QDateTimeEdit,
    QComboBox, QLineEdit, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QInputDialog, QListWidget, QListWidgetItem,
    QDialogButtonBox, QLabel,
)
from sqlalchemy import select

from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.models import DiaryDay, DiaryEntry, Incident, Stay
from gestion_centro.domain.service import (
    record_diary_entry, record_incident, close_diary_day, revise_diary_entry,
)


class DiaryDialog(QDialog):
    SHIFTS = {"Mañana": "morning", "Tarde": "afternoon", "Noche": "night"}
    CATEGORIES = {
        "General": "general", "Actividad": "activity", "Salud": "health",
        "Observación": "observation", "Positiva": "positive",
        "Negativa": "negative", "Mantenimiento": "maintenance", "Otros": "other",
    }
    INCIDENT_TYPES = {
        "Conducta": "behavior", "Salud": "health", "Seguridad": "safety",
        "Conflicto": "conflict", "Fuga": "escape", "Daños": "damage", "Otros": "other",
    }
    SEVERITIES = {"Baja": "low", "Media": "medium", "Alta": "high", "Crítica": "critical"}

    def __init__(self, factory, actor_id):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.setWindowTitle("Diario e incidencias")
        self.resize(980, 640)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.day = QDateEdit()
        self.day.setCalendarPopup(True)
        self.day.setDate(QDate.currentDate())
        self.shift = QComboBox()
        for label, key in self.SHIFTS.items(): self.shift.addItem(label, key)
        self.category = QComboBox()
        for label, key in self.CATEGORIES.items(): self.category.addItem(label, key)
        self.happened = QDateTimeEdit()
        self.happened.setCalendarPopup(True)
        self.happened.setDateTime(QDateTime.currentDateTime())
        self.content = QTextEdit()
        self.content.setMaximumHeight(70)
        self.participant_hint = QLineEdit("Sin menores vinculados")
        self.participant_hint.setReadOnly(True)
        self.selected_stay_ids = []
        form.addRow("Fecha del diario", self.day)
        form.addRow("Turno", self.shift)
        form.addRow("Categoría", self.category)
        form.addRow("Fecha y hora del hecho", self.happened)
        form.addRow("Anotación objetiva", self.content)
        select_stays = QPushButton("Vincular menores / estancias…")
        select_stays.clicked.connect(self.choose_stays)
        form.addRow("Personas vinculadas", self.participant_hint)
        form.addRow("", select_stays)
        layout.addLayout(form)
        actions = QHBoxLayout()
        add = QPushButton("Añadir anotación")
        add.clicked.connect(self.add_entry)
        incident = QPushButton("Registrar incidencia")
        incident.clicked.connect(self.add_incident)
        close = QPushButton("Cerrar diario del día")
        close.clicked.connect(self.close_day)
        revise = QPushButton("Corregir mi anotación")
        revise.clicked.connect(self.revise_entry)
        refresh = QPushButton("Actualizar")
        refresh.clicked.connect(self.refresh)
        for b in (add, incident, close, revise, refresh): actions.addWidget(b)
        layout.addLayout(actions)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Hora", "Turno", "Tipo", "Contenido / incidencia", "Autor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        self.day.dateChanged.connect(self.refresh)
        self.refresh()

    def choose_stays(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Vincular menores y estancias activas")
        dialog.resize(520, 420)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Marca únicamente a los menores implicados. Para un hecho general, deja la selección vacía."))
        choices = QListWidget()
        with session_scope(self.factory) as session:
            stays = session.scalars(select(Stay).where(Stay.status == "active").order_by(Stay.started_on.desc())).all()
            rows = [(s.id, f"{s.minor.internal_code} · {s.minor.given_names} {s.minor.family_names}") for s in stays]
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
            local = self.happened.dateTime().toPython()
            moment = local.astimezone(timezone.utc) if local.tzinfo else local.astimezone().astimezone(timezone.utc)
            with session_scope(self.factory) as session:
                record_diary_entry(session, actor_account_id=self.actor_id,
                    diary_date=self.day.date().toPython(), shift=self.shift.currentData(),
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
            QMessageBox.information(self, "Selecciona una anotación", "Selecciona una anotación del diario; las incidencias no se editan desde aquí.")
            return
        try:
            with session_scope(self.factory) as session:
                entry = session.get(DiaryEntry, metadata["id"])
                if entry is None:
                    raise ValueError("La anotación ya no existe.")
                new_content, ok = QInputDialog.getMultiLineText(
                    self, "Corregir anotación propia",
                    "Nueva versión del texto (se conservará la anterior):", entry.content)
                if not ok:
                    return
                revise_diary_entry(session, actor_account_id=self.actor_id,
                    original_entry_id=entry.id, content=new_content)
            self.refresh()
            QMessageBox.information(self, "Corrección guardada", "Se ha guardado una nueva versión. La anterior permanece en el historial.")
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo corregir", str(exc))

    def add_incident(self):
        title, ok = QInputDialog.getText(self, "Incidencia", "Título:")
        if not ok or not title.strip(): return
        description, ok = QInputDialog.getMultiLineText(self, "Incidencia", "Descripción objetiva:")
        if not ok or not description.strip(): return
        type_label, ok = QInputDialog.getItem(self, "Incidencia", "Tipo:", list(self.INCIDENT_TYPES), 0, False)
        if not ok: return
        severity_label, ok = QInputDialog.getItem(self, "Incidencia", "Gravedad:", list(self.SEVERITIES), 0, False)
        if not ok: return
        try:
            local = self.happened.dateTime().toPython()
            moment = local.astimezone(timezone.utc) if local.tzinfo else local.astimezone().astimezone(timezone.utc)
            with session_scope(self.factory) as session:
                record_incident(session, actor_account_id=self.actor_id,
                    diary_date=self.day.date().toPython(), title=title, description=description,
                    incident_type=self.INCIDENT_TYPES[type_label],
                    severity=self.SEVERITIES[severity_label], happened_at=moment,
                    participants=[(stay_id, "involved", None) for stay_id in self.selected_stay_ids])
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo registrar", str(exc))

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
            day = session.scalar(select(DiaryDay).where(DiaryDay.diary_date == selected))
            entries = session.scalars(select(DiaryEntry).where(
                DiaryEntry.diary_day_id == day.id).order_by(DiaryEntry.happened_at)) .all() if day else []
            incidents = session.scalars(select(Incident).where(
                Incident.diary_day_id == day.id).order_by(Incident.happened_at)).all() if day else []
            rows = [(x.happened_at, x.shift, x.category, x.content, x.author_name_snapshot,
                {"kind": "entry", "id": x.id}) for x in entries]
            rows += [(x.happened_at, "Incidencia", x.severity,
                f"{x.title} · {x.description} [{x.status}]", x.author_name_snapshot,
                {"kind": "incident", "id": x.id}) for x in incidents]
            rows.sort(key=lambda x: x[0])
            is_closed = bool(day and day.closed_at)
        self.table.setRowCount(len(rows))
        for i, values in enumerate(rows):
            display = [values[0].astimezone().strftime("%d/%m %H:%M"), *values[1:5]]
            for j, value in enumerate(display):
                item = QTableWidgetItem(str(value))
                if j == 0:
                    item.setData(Qt.ItemDataRole.UserRole, values[5])
                self.table.setItem(i, j, item)
        self.content.setReadOnly(is_closed)
