"""Interfaz básica de diario e incidencias con autoría y cierre trazable."""
from datetime import datetime, timezone

from PySide6.QtCore import QDate, QDateTime, Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QDateEdit, QDateTimeEdit,
    QComboBox, QLineEdit, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QInputDialog, QListWidget, QListWidgetItem,
    QDialogButtonBox, QLabel,
)
from sqlalchemy import select, or_

from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.models import DiaryDay, DiaryEntry, Incident, Stay
from gestion_centro.domain.service import (
    record_diary_entry, record_incident, close_diary_day, revise_diary_entry,
    correct_diary_entry, has_health_access, list_diary_records,
)
from gestion_centro.domain.documents_service import list_active_stays
from gestion_centro.domain.health_service import read_health_profile, list_medication_plans


class DiaryDialog(QDialog):
    SHIFTS = {"Mañana": "morning", "Tarde": "afternoon", "Noche": "night"}
    CATEGORIES = {
        "Actividades realizadas": "activity",
        "Comportamientos positivos": "positive",
        "Comportamientos negativos": "negative",
        "Observaciones": "observation",
    }
    INCIDENT_TYPES = {
        "Conducta": "behavior", "Salud": "health", "Seguridad": "safety",
        "Conflicto": "conflict", "Fuga": "escape", "Daños": "damage", "Otros": "other",
    }
    SEVERITIES = {"Baja": "low", "Media": "medium", "Alta": "high", "Crítica": "critical"}

    def __init__(self, factory, actor_id):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        with session_scope(factory) as session:
            self.health_access = has_health_access(session, actor_account_id=actor_id)
        self.setWindowTitle("Diario e incidencias")
        self.resize(980, 640)
        layout = QVBoxLayout(self)
        intro = QLabel("Completa los apartados del día. Las enfermedades y los tratamientos se consultan automáticamente desde las fichas sanitarias. Las anotaciones quedan vinculadas a su autor.")
        intro.setWordWrap(True)
        intro.setObjectName("formIntro")
        layout.addWidget(intro)
        self.day_state = QLabel()
        self.day_state.setObjectName("recordState")
        layout.addWidget(self.day_state)
        form = QFormLayout()
        self.day = QDateEdit()
        self.day.setCalendarPopup(True)
        self.day.setDate(QDate.currentDate())
        self.shift = QComboBox()
        for label, key in self.SHIFTS.items(): self.shift.addItem(label, key)
        self.category = QComboBox()
        for label, key in self.CATEGORIES.items():
            if key != "health" or self.health_access:
                self.category.addItem(label, key)
        self.happened = QDateTimeEdit()
        self.happened.setCalendarPopup(True)
        self.happened.setDateTime(QDateTime.currentDateTime())
        self.shift.hide()
        self.happened.hide()
        self.content = QTextEdit()
        self.content.setMinimumHeight(130)
        self.content.setPlaceholderText("Describe los hechos con claridad. El texto se ajustará automáticamente al ancho del cuadro.")
        self.participant_hint = QLineEdit("Sin menores vinculados")
        self.participant_hint.setReadOnly(True)
        self.selected_stay_ids = []
        form.addRow("Fecha del parte", self.day)
        form.addRow("Apartado", self.category)
        form.addRow("Contenido", self.content)
        select_stays = QPushButton("Vincular menores / estancias…")
        select_stays.clicked.connect(self.choose_stays)
        form.addRow("Personas vinculadas", self.participant_hint)
        form.addRow("", select_stays)
        layout.addLayout(form)
        layout.addWidget(QLabel("Enfermedades y tratamientos · consulta de expedientes presentes en la fecha seleccionada"))
        self.health_summary = QTextEdit()
        self.health_summary.setReadOnly(True)
        self.health_summary.setMaximumHeight(145)
        self.health_summary.setPlaceholderText("La información sanitaria se consulta desde los expedientes y no se vuelve a escribir en el parte.")
        layout.addWidget(self.health_summary)
        actions = QHBoxLayout()
        self.add_button = QPushButton("Guardar apartado")
        self.add_button.clicked.connect(self.add_entry)
        self.incident_button = QPushButton("Registrar incidencia")
        self.incident_button.clicked.connect(self.add_incident)
        self.incident_button.hide()
        self.close_button = QPushButton("Cerrar parte del día")
        self.close_button.clicked.connect(self.close_day)
        self.revise_button = QPushButton("Corregir mi anotación")
        self.revise_button.clicked.connect(self.revise_entry)
        refresh = QPushButton("Actualizar")
        refresh.clicked.connect(self.refresh)
        for b in (self.add_button, self.close_button, self.revise_button, refresh): actions.addWidget(b)
        layout.addLayout(actions)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Hora", "Apartado / tipo", "Contenido", "Autor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
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
            stays = list_active_stays(session, actor_account_id=self.actor_id)
            rows = [(s.id, f"{(s.minor.nif_nie or s.minor.passport_number or "Sin NIF/NIE")} · {s.minor.given_names} {s.minor.family_names}") for s in stays]
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
                day = session.get(DiaryDay, entry.diary_day_id)
                if day is not None and day.closed_at is not None:
                    new_content, ok = QInputDialog.getMultiLineText(
                        self, "Rectificar anotación cerrada",
                        "Texto de la rectificación (el original se conserva):", "")
                    if not ok or not new_content.strip():
                        return
                    reason, ok = QInputDialog.getText(
                        self, "Motivo de rectificación", "Motivo:")
                    if not ok or not reason.strip():
                        return
                    local = QDateTime.currentDateTime().toPython()
                    moment = local.astimezone(timezone.utc) if local.tzinfo else local.astimezone().astimezone(timezone.utc)
                    correct_diary_entry(session, actor_account_id=self.actor_id,
                        original_entry_id=entry.id, content=new_content,
                        happened_at=moment, reason=reason)
                    message = "Se ha añadido una rectificación vinculada. El original permanece en el historial."
                else:
                    new_content, ok = QInputDialog.getMultiLineText(
                        self, "Corregir anotación propia",
                        "Nueva versión del texto (se conservará la anterior):", entry.content)
                    if not ok:
                        return
                    revise_diary_entry(session, actor_account_id=self.actor_id,
                        original_entry_id=entry.id, content=new_content)
                    message = "Se ha guardado una nueva versión. La anterior permanece en el historial."
            self.refresh()
            QMessageBox.information(self, "Corrección guardada", message)
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo corregir", str(exc))

    def add_incident(self):
        title, ok = QInputDialog.getText(self, "Incidencia", "Título:")
        if not ok or not title.strip(): return
        description, ok = QInputDialog.getMultiLineText(self, "Incidencia", "Descripción objetiva:")
        if not ok or not description.strip(): return
        incident_types = [label for label, key in self.INCIDENT_TYPES.items()
            if key != "health" or self.health_access]
        type_label, ok = QInputDialog.getItem(self, "Incidencia", "Tipo:", incident_types, 0, False)
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
            day, entries, incidents = list_diary_records(
                session, actor_account_id=self.actor_id, diary_date=selected)
            category_labels = {
                "activity": "Actividades realizadas",
                "positive": "Comportamientos positivos",
                "negative": "Comportamientos negativos",
                "observation": "Observaciones",
                "general": "General (histórico)",
                "health": "Salud (histórico)",
                "maintenance": "Mantenimiento (histórico)",
                "other": "Otros (histórico)",
            }
            rows = [(x.happened_at, category_labels.get(x.category, x.category),
                x.content, x.author_name_snapshot,
                {"kind": "entry", "id": x.id}) for x in entries]
            rows += [(x.happened_at, f"Incidencia · {x.severity}",
                f"{x.title} · {x.description} [{x.status}]", x.author_name_snapshot,
                {"kind": "incident", "id": x.id}) for x in incidents]
            rows.sort(key=lambda x: x[0])
            is_closed = bool(day and day.closed_at)
            health_rows = []
            health_stays = session.scalars(
                select(Stay).where(
                    Stay.started_on <= selected,
                    or_(Stay.ended_on.is_(None), Stay.ended_on >= selected),
                ).order_by(Stay.started_on, Stay.id)
            ).all()
            for stay in health_stays:
                minor = stay.minor
                profile = read_health_profile(session, actor_account_id=self.actor_id, minor_id=minor.id)
                plans = list_medication_plans(session, actor_account_id=self.actor_id, minor_id=minor.id)
                details = []
                if profile and profile.relevant_conditions:
                    details.append(f"Enfermedades/condiciones: {profile.relevant_conditions}")
                if profile and profile.allergies:
                    details.append(f"Alergias: {profile.allergies}")
                active_plans = [plan for plan in plans if plan.active
                    and plan.starts_on <= selected
                    and (plan.ends_on is None or plan.ends_on >= selected)]
                details.extend(
                    f"Tratamiento: {plan.medication_name} · {plan.prescribed_dose} · {plan.schedule_text}"
                    for plan in active_plans
                )
                if details:
                    health_rows.append(f"{minor.given_names} {minor.family_names}\n" + "\n".join(details))
            health_text = "\n\n".join(health_rows) if health_rows else (
                "No hay enfermedades o tratamientos activos registrados para los menores que se encuentran actualmente en el centro."
            )
        self.health_summary.setPlainText(health_text)
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
        self.revise_button.setEnabled(bool(rows))
        self.day_state.setText("PARTE CERRADO · Solo consulta" if is_closed else "PARTE ABIERTO · Puedes completar o corregir tus apartados")
        self.day_state.setProperty("closed", is_closed)
        self.day_state.style().unpolish(self.day_state)
        self.day_state.style().polish(self.day_state)
