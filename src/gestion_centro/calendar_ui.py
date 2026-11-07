"""Calendario diario, semanal, mensual y anual sobre la agenda común."""
from datetime import datetime, time, timedelta, timezone

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QDateEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QMessageBox,
)
from sqlalchemy import select

from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.models import AgendaItem
from gestion_centro.domain.service import list_agenda_items, has_health_access


class CalendarDialog(QDialog):
    VIEWS = {"Día": "day", "Semana": "week", "Mes": "month", "Año": "year"}

    def __init__(self, factory, actor_id):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        with session_scope(factory) as session:
            self.health_access = has_health_access(session, actor_account_id=actor_id)
        self.setWindowTitle("Calendario del centro")
        self.resize(980, 620)
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.view = QComboBox()
        for label, value in self.VIEWS.items():
            self.view.addItem(label, value)
        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)
        self.kind = QComboBox()
        self.kind.addItem("Todos los tipos", "")
        for label, value in [
            ("Citas", "appointment"), ("Actividades", "activity"), ("Tareas", "task"),
            ("Reuniones", "meeting"), ("Llamadas", "call"), ("Contactos", "contact"),
            ("Cumpleaños", "birthday"), ("Eventos", "event")
        ]:
            self.kind.addItem(label, value)
        if self.health_access:
            self.kind.addItem("Vacunas", "vaccine")
        self.status = QComboBox()
        self.status.addItem("Todos los estados", "")
        for label, value in [("Pendiente","pending"),("En curso","in_progress"),
                             ("Atendido","done"),("Cancelado","cancelled")]:
            self.status.addItem(label, value)
        refresh = QPushButton("Actualizar")
        refresh.clicked.connect(self.refresh)
        self.date.dateChanged.connect(self.refresh)
        self.view.currentIndexChanged.connect(self.refresh)
        self.kind.currentIndexChanged.connect(self.refresh)
        self.status.currentIndexChanged.connect(self.refresh)
        for w in (QLabel("Vista"), self.view, QLabel("Fecha"), self.date,
                  QLabel("Tipo"), self.kind, QLabel("Estado"), self.status, refresh):
            controls.addWidget(w)
        layout.addLayout(controls)
        self.caption = QLabel()
        layout.addWidget(self.caption)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Fecha y hora", "Tipo", "Título", "Descripción", "Estado", "Asignación"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        self.refresh()

    def period(self):
        selected = self.date.date().toPython()
        mode = self.view.currentData()
        if mode == "day":
            start, end = selected, selected + timedelta(days=1)
        elif mode == "week":
            start = selected - timedelta(days=selected.weekday())
            end = start + timedelta(days=7)
        elif mode == "month":
            start = selected.replace(day=1)
            end = (start.replace(year=start.year + 1, month=1) if start.month == 12
                   else start.replace(month=start.month + 1))
        else:
            start = selected.replace(month=1, day=1)
            end = start.replace(year=start.year + 1)
        return start, end

    def refresh(self):
        start, end = self.period()
        start_dt = datetime.combine(start, time.min).astimezone()
        end_dt = datetime.combine(end, time.min).astimezone()
        kind, status = self.kind.currentData(), self.status.currentData()
        try:
            with session_scope(self.factory) as session:
                items = list_agenda_items(session, actor_account_id=self.actor_id,
                    start=start_dt, end=end_dt - timedelta(microseconds=1),
                    kind=kind or None, status=status or None)
                rows = [(x.starts_at, x.kind, x.title, x.description or "", x.status,
                         "Equipo" if x.assignment_scope == "team" else "Individual") for x in items]
            self.caption.setText(f"{start:%d/%m/%Y} – {(end - timedelta(days=1)):%d/%m/%Y} · {len(rows)} elementos")
            self.table.setRowCount(len(rows))
            for i, values in enumerate(rows):
                dt = values[0]
                try:
                    local_dt = dt.astimezone()
                except (ValueError, AttributeError):
                    local_dt = dt
                display = [local_dt.strftime("%d/%m/%Y %H:%M"), *values[1:]]
                for j, value in enumerate(display):
                    self.table.setItem(i, j, QTableWidgetItem(str(value)))
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo cargar el calendario", str(exc))
