"""Interfaz básica de diario e incidencias con autoría y cierre trazable."""
from datetime import datetime, timezone

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QDateEdit, QDateTimeEdit,
    QComboBox, QLineEdit, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QInputDialog,
)
from sqlalchemy import select

from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.models import DiaryDay, DiaryEntry, Incident, Stay
from gestion_centro.domain.service import (
    record_diary_entry, record_incident, close_diary_day, close_incident,
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
        self.happened.setDateTime(self.day.dateTime() if hasattr(self.day, "dateTime") else self.day.date().startOfDay())
        self.content = QTextEdit()
        self.content.setMaximumHeight(70)
        form.addRow("Fecha del diario", self.day)
        form.addRow("Turno", self.shift)
        form.addRow("Categoría", self.category)
        form.addRow("Fecha y hora del hecho", self.happened)
        form.addRow("Anotación objetiva", self.content)
        layout.addLayout(form)
        actions = QHBoxLayout()
        add = QPushButton("Añadir anotación")
        add.clicked.connect(self.add_entry)
        incident = QPushButton("Registrar incidencia")
        incident.clicked.connect(self.add_incident)
        close = QPushButton("Cerrar diario del día")
        close.clicked.connect(self.close_day)
        refresh = QPushButton("Actualizar")
        refresh.clicked.connect(self.refresh)
        for b in (add, incident, close, refresh): actions.addWidget(b)
        layout.addLayout(actions)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Hora", "Turno", "Tipo", "Contenido / incidencia", "Autor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        self.day.dateChanged.connect(self.refresh)
        self.refresh()

    def add_entry(self):
        try:
            local = self.happened.dateTime().toPython()
            moment = local.astimezone(timezone.utc) if local.tzinfo else local.astimezone().astimezone(timezone.utc)
            with session_scope(self.factory) as session:
                record_diary_entry(session, actor_account_id=self.actor_id,
                    diary_date=self.day.date().toPython(), shift=self.shift.currentData(),
                    category=self.category.currentData(), content=self.content.toPlainText(),
                    happened_at=moment)
            self.content.clear()
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

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
                    severity=self.SEVERITIES[severity_label], happened_at=moment, participants=[])
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
            rows = [(x.happened_at, x.shift, x.category, x.content, x.author_name_snapshot) for x in entries]
            rows += [(x.happened_at, "Incidencia", x.severity,
                f"{x.title} · {x.description} [{x.status}]", x.author_name_snapshot) for x in incidents]
            rows.sort(key=lambda x: x[0])
            is_closed = bool(day and day.closed_at)
        self.table.setRowCount(len(rows))
        for i, values in enumerate(rows):
            display = [values[0].astimezone().strftime("%d/%m %H:%M"), *values[1:]]
            for j, value in enumerate(display):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
        self.content.setReadOnly(is_closed)
