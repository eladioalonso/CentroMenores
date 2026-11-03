"""Interfaces de seguimiento educativo y sanitario."""
from datetime import date, datetime, timezone

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QLineEdit, QTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QHBoxLayout, QInputDialog, QTabWidget, QWidget, QLabel,
)
from sqlalchemy import select

from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.models import Minor, Stay
from gestion_centro.domain.education import EducationGoal, SchoolPlacement
from gestion_centro.domain.education_service import (
    create_education_goal, add_education_update, set_education_goal_status,
    create_school_placement, add_school_record, list_school_placements,
    revise_education_update,
)
from gestion_centro.domain.health import HealthProfile, MedicationPlan, MedicationAdministration, VaccineRecord
from gestion_centro.domain.health_service import (
    read_health_profile, save_health_profile, add_medication_plan,
    record_medication_administration, add_vaccine_record, list_medication_plans,
    set_medication_schedules, list_daily_medication_schedule,
)


class StaySelectorDialog(QDialog):
    def __init__(self, factory, title, stay_id=None):
        super().__init__()
        self.factory = factory
        self.setWindowTitle(title)
        self.resize(860, 520)
        layout = QVBoxLayout(self)
        self.stay = QComboBox()
        with session_scope(factory) as session:
            stays = session.scalars(select(Stay).where(Stay.status == "active")
                .order_by(Stay.started_on.desc())).all()
            for s in stays:
                self.stay.addItem(f"{s.minor.internal_code} · {s.minor.given_names} {s.minor.family_names}", s.id)
        if stay_id is not None:
            index = self.stay.findData(stay_id)
            if index >= 0:
                self.stay.setCurrentIndex(index)
        layout.addWidget(QLabel("Residente:"))
        layout.addWidget(self.stay)
        self.body = QVBoxLayout()
        layout.addLayout(self.body)


class EducationDialog(StaySelectorDialog):
    def __init__(self, factory, actor_id, stay_id=None):
        super().__init__(factory, "Seguimiento educativo y escolaridad", stay_id=stay_id)
        self.actor_id = actor_id
        form = QFormLayout()
        self.goal_title = QLineEdit()
        self.goal_description = QTextEdit()
        self.goal_description.setMaximumHeight(60)
        form.addRow("Objetivo", self.goal_title)
        form.addRow("Descripción", self.goal_description)
        self.body.addLayout(form)
        add = QPushButton("Crear objetivo")
        add.clicked.connect(self.create_goal)
        self.body.addWidget(add)
        self.goals = QTableWidget(0, 3)
        self.goals.setHorizontalHeaderLabels(["Objetivo", "Estado", "Fecha objetivo"])
        self.goals.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.goals.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.goals.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.body.addWidget(self.goals)
        self.updates = QTableWidget(0, 6)
        self.updates.setHorizontalHeaderLabels(["ID", "Fecha", "Área", "Observación", "Actuación", "Respuesta / seguimiento"])
        self.updates.setColumnHidden(0, True)
        self.updates.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.updates.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.updates.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.body.addWidget(self.updates)
        actions = QHBoxLayout()
        for label, callback in [("Añadir seguimiento", self.add_update),
                                ("Rectificar mi seguimiento", self.revise_update),
                                ("Cambiar estado", self.change_status),
                                ("Nueva escolarización", self.add_school)]:
            b = QPushButton(label); b.clicked.connect(callback); actions.addWidget(b)
        self.body.addLayout(actions)
        self.schools = QTableWidget(0, 4)
        self.schools.setHorizontalHeaderLabels(["Centro", "Curso", "Desde", "Hasta"])
        self.schools.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schools.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.schools.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.body.addWidget(self.schools)
        self.school_records = QTableWidget(0, 4)
        self.school_records.setHorizontalHeaderLabels(["Fecha", "Tipo", "Descripción", "Autor"])
        self.school_records.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.school_records.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.body.addWidget(self.school_records)
        school_actions = QHBoxLayout()
        add_record = QPushButton("Añadir registro al centro seleccionado")
        add_record.clicked.connect(self.add_school_record_ui)
        school_actions.addWidget(add_record)
        end_placement = QPushButton("Finalizar escolarización seleccionada")
        end_placement.clicked.connect(self.end_school_placement)
        school_actions.addWidget(end_placement)
        self.body.addLayout(school_actions)
        self.schools.itemSelectionChanged.connect(self.refresh_school_records)
        self.stay.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        stay_id = self.stay.currentData()
        with session_scope(self.factory) as session:
            rows = session.scalars(select(EducationGoal).where(EducationGoal.stay_id == stay_id)
                .order_by(EducationGoal.created_at.desc())).all() if stay_id else []
            data = [(g.id, g.title, g.status, g.target_date.isoformat() if g.target_date else "—") for g in rows]
            updates = [(u.id, u.created_at, u.category, u.objective_description, u.actions_taken,
                u.response_observed + (" · Seguimiento: " + u.follow_up if u.follow_up else ""))
                for g in rows for u in g.updates]
            placements = list_school_placements(session, stay_id=stay_id) if stay_id else []
            school_data = [(p.id, p.school_name, p.course, p.started_on.strftime("%d/%m/%Y"),
                p.ended_on.strftime("%d/%m/%Y") if p.ended_on else "En curso") for p in placements]
        self.goals.setRowCount(len(data))
        for i, values in enumerate(data):
            item_id, *display = values
            for col, value in enumerate(display):
                cell = QTableWidgetItem(value)
                if col == 0: cell.setData(Qt.ItemDataRole.UserRole, item_id)
                self.goals.setItem(i, col, cell)
        updates.sort(key=lambda row: row[0], reverse=True)
        self.updates.setRowCount(len(updates))
        for i, (update_id, created, category, observation, actions, response) in enumerate(updates):
            values = [update_id, created.astimezone().strftime("%d/%m/%Y %H:%M"), category, observation, actions, response]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if col == 0: cell.setData(Qt.ItemDataRole.UserRole, update_id)
                self.updates.setItem(i, col, cell)
        self.schools.setRowCount(len(school_data))
        for i, values in enumerate(school_data):
            placement_id, *display = values
            for col, value in enumerate(display):
                cell = QTableWidgetItem(value)
                if col == 0: cell.setData(Qt.ItemDataRole.UserRole, placement_id)
                self.schools.setItem(i, col, cell)
        if self.schools.rowCount():
            self.schools.selectRow(0)
        else:
            self.school_records.setRowCount(0)

    def selected_placement_id(self):
        row = self.schools.currentRow()
        cell = self.schools.item(row, 0) if row >= 0 else None
        return cell.data(Qt.ItemDataRole.UserRole) if cell else None

    def refresh_school_records(self):
        placement_id = self.selected_placement_id()
        with session_scope(self.factory) as session:
            placement = session.get(SchoolPlacement, placement_id) if placement_id else None
            rows = [(r.occurred_on, r.record_type, r.description, r.author_name_snapshot)
                for r in placement.records] if placement else []
        rows.sort(key=lambda x: x[0], reverse=True)
        self.school_records.setRowCount(len(rows))
        for i, values in enumerate(rows):
            display = [values[0].strftime("%d/%m/%Y"), values[1], values[2], values[3]]
            for col, value in enumerate(display):
                self.school_records.setItem(i, col, QTableWidgetItem(value))

    def create_goal(self):
        if not self.stay.currentData(): return
        try:
            with session_scope(self.factory) as session:
                create_education_goal(session, actor_account_id=self.actor_id,
                    stay_id=self.stay.currentData(), title=self.goal_title.text(),
                    description=self.goal_description.toPlainText())
            self.goal_title.clear(); self.goal_description.clear(); self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo crear", str(exc))

    def selected_goal(self):
        row = self.goals.currentRow()
        cell = self.goals.item(row, 0) if row >= 0 else None
        return cell.data(Qt.ItemDataRole.UserRole) if cell else None

    def add_update(self):
        goal_id = self.selected_goal()
        if not goal_id:
            QMessageBox.information(self, "Selecciona", "Selecciona un objetivo.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo seguimiento educativo")
        dialog.resize(620, 560)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        category = QComboBox()
        mapping = [
            ("Autonomía", "autonomy"), ("Convivencia", "coexistence"),
            ("Emocional", "emotional"), ("Social", "social"),
            ("Aprendizaje", "learning"), ("Hábitos de salud", "health_habits"),
            ("Otra", "other"),
        ]
        for label, value in mapping:
            category.addItem(label, value)
        observation = QTextEdit()
        observation.setPlaceholderText("Describe hechos observables, evitando interpretaciones.")
        actions = QTextEdit()
        actions.setPlaceholderText("Indica qué actuaciones se realizaron.")
        response = QTextEdit()
        response.setPlaceholderText("Describe la respuesta observada.")
        follow_up = QTextEdit()
        follow_up.setPlaceholderText("Opcional: qué queda pendiente y cuándo revisarlo.")
        for widget in (observation, actions, response):
            widget.setMinimumHeight(75)
        follow_up.setMinimumHeight(60)
        form.addRow("Área", category)
        form.addRow("Observación objetiva", observation)
        form.addRow("Actuaciones realizadas", actions)
        form.addRow("Respuesta observada", response)
        form.addRow("Seguimiento pendiente (opcional)", follow_up)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        save = QPushButton("Guardar seguimiento")
        cancel = QPushButton("Cancelar")
        save.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            with session_scope(self.factory) as session:
                add_education_update(
                    session, actor_account_id=self.actor_id, goal_id=goal_id,
                    category=category.currentData(),
                    objective_description=observation.toPlainText(),
                    actions_taken=actions.toPlainText(),
                    response_observed=response.toPlainText(),
                    follow_up=follow_up.toPlainText(),
                )
            QMessageBox.information(self, "Guardado", "Seguimiento añadido al historial.")
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

    def revise_update(self):
        row = self.updates.currentRow()
        cell = self.updates.item(row, 0) if row >= 0 else None
        update_id = cell.data(Qt.ItemDataRole.UserRole) if cell else None
        if not update_id:
            QMessageBox.information(self, "Selecciona", "Selecciona primero un seguimiento.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Rectificar mi seguimiento")
        dialog.resize(560, 430)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        observation = QTextEdit()
        actions = QTextEdit()
        response = QTextEdit()
        follow_up = QTextEdit()
        observation.setMinimumHeight(65)
        actions.setMinimumHeight(65)
        response.setMinimumHeight(65)
        form.addRow("Observación corregida", observation)
        form.addRow("Actuaciones", actions)
        form.addRow("Respuesta observada", response)
        form.addRow("Seguimiento pendiente (opcional)", follow_up)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        save = QPushButton("Guardar rectificación")
        cancel = QPushButton("Cancelar")
        save.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            with session_scope(self.factory) as session:
                revise_education_update(session, actor_account_id=self.actor_id,
                    update_id=update_id,
                    objective_description=observation.toPlainText(),
                    actions_taken=actions.toPlainText(),
                    response_observed=response.toPlainText(),
                    follow_up=follow_up.toPlainText())
            QMessageBox.information(self, "Rectificación guardada",
                "Se ha añadido una rectificación vinculada. El seguimiento original se conserva.")
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo rectificar", str(exc))

    def change_status(self):
        goal_id = self.selected_goal()
        if not goal_id: return
        label, ok = QInputDialog.getItem(self, "Estado del objetivo", "Estado:",
            ["Activo", "Alcanzado", "Pausado", "Cerrado"], 0, False)
        if not ok: return
        value = {"Activo":"active","Alcanzado":"achieved","Pausado":"paused","Cerrado":"closed"}[label]
        try:
            with session_scope(self.factory) as session:
                set_education_goal_status(session, actor_account_id=self.actor_id, goal_id=goal_id, status=value)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo cambiar", str(exc))

    def add_school(self):
        name, ok = QInputDialog.getText(self, "Escolarización", "Centro educativo:")
        if not ok or not name.strip(): return
        course, ok = QInputDialog.getText(self, "Escolarización", "Curso:")
        if not ok or not course.strip(): return
        try:
            with session_scope(self.factory) as session:
                create_school_placement(session, actor_account_id=self.actor_id,
                    stay_id=self.stay.currentData(), school_name=name, course=course,
                    started_on=date.today())
            QMessageBox.information(self, "Escolarización", "Centro registrado.")
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

    def add_school_record_ui(self):
        placement_id = self.selected_placement_id()
        if not placement_id:
            QMessageBox.information(self, "Selecciona centro", "Selecciona primero un centro escolar.")
            return
        label, ok = QInputDialog.getItem(self, "Registro escolar", "Tipo:",
            ["Asistencia", "Comportamiento", "Reunión", "Tarea", "Logro", "Otro"], 0, False)
        if not ok: return
        record_type = {"Asistencia":"attendance","Comportamiento":"behavior","Reunión":"meeting",
            "Tarea":"task","Logro":"achievement","Otro":"other"}[label]
        description, ok = QInputDialog.getMultiLineText(self, "Registro escolar", "Descripción objetiva:")
        if not ok or not description.strip(): return
        try:
            with session_scope(self.factory) as session:
                add_school_record(session, actor_account_id=self.actor_id,
                    placement_id=placement_id, record_type=record_type,
                    occurred_on=date.today(), description=description)
            self.refresh_school_records()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

    def end_school_placement(self):
        placement_id = self.selected_placement_id()
        if not placement_id: return
        ended_on = QDate.currentDate().toPython()
        if QMessageBox.question(self, "Finalizar escolarización",
            "¿Registrar hoy como fecha de finalización del centro seleccionado?") != QMessageBox.StandardButton.Yes:
            return
        try:
            with session_scope(self.factory) as session:
                from gestion_centro.domain.education_service import end_school_placement
                end_school_placement(session, actor_account_id=self.actor_id,
                    placement_id=placement_id, ended_on=ended_on)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo finalizar", str(exc))


class HealthDialog(StaySelectorDialog):
    def __init__(self, factory, actor_id, stay_id=None):
        super().__init__(factory, "Ficha sanitaria y medicación", stay_id=None)
        self.actor_id = actor_id
        # La ficha sanitaria se selecciona por expediente permanente, no por ingreso.
        preferred_minor_id = None
        with session_scope(factory) as session:
            if stay_id:
                selected_stay = session.get(Stay, stay_id)
                preferred_minor_id = selected_stay.minor_id if selected_stay else None
            minors = session.scalars(select(Minor).order_by(Minor.active.desc(), Minor.internal_code)).all()
            self.stay.clear()
            self.stay.addItem("Selecciona un residente…", None)
            for minor in minors:
                status = "" if minor.active else " · Inactivo"
                self.stay.addItem(
                    f"{minor.internal_code} · {minor.given_names} {minor.family_names}{status}",
                    minor.id,
                )
        if preferred_minor_id:
            index = self.stay.findData(preferred_minor_id)
            if index >= 0:
                self.stay.setCurrentIndex(index)
        self.resize(1050, 720)
        self.tabs = QTabWidget()
        self.body.addWidget(self.tabs)

        profile_tab = QWidget()
        profile_layout = QVBoxLayout(profile_tab)
        form = QFormLayout()
        self.allergies = QTextEdit(); self.allergies.setMaximumHeight(65)
        self.conditions = QTextEdit(); self.conditions.setMaximumHeight(65)
        self.emergency = QTextEdit(); self.emergency.setMaximumHeight(65)
        form.addRow("Alergias", self.allergies)
        form.addRow("Condiciones relevantes", self.conditions)
        form.addRow("Instrucciones de emergencia", self.emergency)
        profile_layout.addLayout(form)
        save = QPushButton("Guardar ficha sanitaria")
        save.clicked.connect(self.save_profile)
        profile_layout.addWidget(save)
        profile_layout.addStretch(1)
        self.tabs.addTab(profile_tab, "Ficha sanitaria")

        medication_tab = QWidget()
        medication_layout = QVBoxLayout(medication_tab)
        self.plans = QTableWidget(0, 4)
        self.plans.setHorizontalHeaderLabels(["Medicamento", "Dosis prescrita", "Pauta", "Vigencia"])
        self.plans.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.plans.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.plans.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        medication_layout.addWidget(self.plans)
        plan_actions = QHBoxLayout()
        for label, callback in [("Registrar pauta prescrita", self.add_plan),
                                ("Configurar horarios", self.configure_schedule)]:
            button = QPushButton(label); button.clicked.connect(callback); plan_actions.addWidget(button)
        medication_layout.addLayout(plan_actions)
        self.tabs.addTab(medication_tab, "Medicación y pautas")

        administration_tab = QWidget()
        administration_layout = QVBoxLayout(administration_tab)
        filters = QHBoxLayout()
        self.admin_day = QDateEdit(QDate.currentDate())
        self.admin_day.setCalendarPopup(True)
        self.admin_shift_filter = QComboBox()
        self.admin_shift_filter.addItem("Todos los turnos", None)
        self.admin_shift_filter.addItem("Mañana", "morning")
        self.admin_shift_filter.addItem("Tarde", "afternoon")
        self.admin_shift_filter.addItem("Noche", "night")
        filters.addWidget(QLabel("Fecha"))
        filters.addWidget(self.admin_day)
        filters.addWidget(QLabel("Turno"))
        filters.addWidget(self.admin_shift_filter)
        filters.addStretch(1)
        administration_layout.addLayout(filters)
        self.administrations = QTableWidget(0, 7)
        self.administrations.setHorizontalHeaderLabels(["Hora prevista", "Turno", "Medicamento", "Dosis", "Estado", "Motivo / nota", "Registrado por"])
        self.administrations.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.administrations.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        administration_layout.addWidget(self.administrations)
        administer_button = QPushButton("Registrar resultado de administración")
        administer_button.clicked.connect(self.administer)
        administration_layout.addWidget(administer_button)
        self.tabs.addTab(administration_tab, "Administraciones")

        vaccine_tab = QWidget()
        vaccine_layout = QVBoxLayout(vaccine_tab)
        self.vaccines = QTableWidget(0, 3)
        self.vaccines.setHorizontalHeaderLabels(["Vacuna", "Fecha", "Dosis / referencia"])
        self.vaccines.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vaccines.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        vaccine_layout.addWidget(self.vaccines)
        vaccine_button = QPushButton("Registrar vacuna")
        vaccine_button.clicked.connect(self.add_vaccine)
        vaccine_layout.addWidget(vaccine_button)
        self.tabs.addTab(vaccine_tab, "Vacunas")

        self.admin_day.dateChanged.connect(self.refresh)
        self.admin_shift_filter.currentIndexChanged.connect(self.refresh)
        self.stay.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        minor_id = self.stay.currentData()
        if not minor_id:
            self.allergies.clear(); self.conditions.clear(); self.emergency.clear()
            self.plans.setRowCount(0); self.administrations.setRowCount(0); self.vaccines.setRowCount(0)
            return
        with session_scope(self.factory) as session:
            profile = read_health_profile(session, actor_account_id=self.actor_id, minor_id=minor_id)
            plans = list_medication_plans(session, actor_account_id=self.actor_id, minor_id=minor_id)
            vaccine_rows = session.scalars(
                select(VaccineRecord).where(VaccineRecord.minor_id == minor_id)
                .order_by(VaccineRecord.administered_on.desc())
            ).all()
            daily_rows = list_daily_medication_schedule(
                session, actor_account_id=self.actor_id, minor_id=minor_id,
                day=self.admin_day.date().toPython()
            )
            administration_rows = [
                row for row in daily_rows
                if self.admin_shift_filter.currentData() is None
                or row[1].shift == self.admin_shift_filter.currentData()
            ]
        self.allergies.setPlainText((profile.allergies or "") if profile else "")
        self.conditions.setPlainText((profile.relevant_conditions or "") if profile else "")
        self.emergency.setPlainText((profile.emergency_instructions or "") if profile else "")
        self.plans.setRowCount(len(plans))
        for i, plan in enumerate(plans):
            values = [
                plan.medication_name, plan.prescribed_dose, plan.schedule_text,
                f"{plan.starts_on:%d/%m/%Y} – {plan.ends_on:%d/%m/%Y}"
                if plan.ends_on else "Sin fecha final",
            ]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if col == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, plan.id)
                self.plans.setItem(i, col, cell)
        admin_rows = sorted(administration_rows, key=lambda item: item[2])
        self.administrations.setRowCount(len(admin_rows))
        for i, (plan, schedule, planned_at, record) in enumerate(admin_rows):
            status_label = {
                "administered": "Administrada", "refused": "Rechazada",
                "not_available": "No disponible",
            }.get(record.status, "Pendiente") if record else "Pendiente"
            values = [
                schedule.time_of_day,
                {"morning": "Mañana", "afternoon": "Tarde", "night": "Noche"}.get(
                    schedule.shift, schedule.shift
                ),
                plan.medication_name, plan.prescribed_dose, status_label,
                (record.note or "—") if record else "—",
                record.recorded_by_name_snapshot if record else "—",
            ]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if col == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, (
                        plan.id, planned_at.isoformat(), schedule.shift,
                        record.id if record else None,
                    ))
                self.administrations.setItem(i, col, cell)
        self.vaccines.setRowCount(len(vaccine_rows))
        for i, record in enumerate(vaccine_rows):
            values = [
                record.vaccine_name, record.administered_on.strftime("%d/%m/%Y"),
                record.dose_reference or "—",
            ]
            for col, value in enumerate(values):
                self.vaccines.setItem(i, col, QTableWidgetItem(value))

    def save_profile(self):
        if not self.stay.currentData():
            QMessageBox.information(self, "Selecciona residente", "Selecciona un residente antes de guardar.")
            return
        try:
            with session_scope(self.factory) as session:
                save_health_profile(
                    session, actor_account_id=self.actor_id, minor_id=self.stay.currentData(),
                    allergies=self.allergies.toPlainText(),
                    relevant_conditions=self.conditions.toPlainText(),
                    emergency_instructions=self.emergency.toPlainText(),
                )
            QMessageBox.information(self, "Ficha sanitaria", "Datos guardados y auditados.")
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

    def _read_schedules(self, text):
        schedules = []
        for line in text.splitlines():
            if not line.strip():
                continue
            parts = [part.strip() for part in line.split("|", 1)]
            if len(parts) != 2:
                raise ValueError("Usa el formato HH:MM|morning, HH:MM|afternoon o HH:MM|night.")
            schedules.append((parts[0], parts[1].lower()))
        if not schedules:
            raise ValueError("Indica al menos un horario prescrito.")
        return schedules

    def add_plan(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Registrar pauta prescrita")
        dialog.resize(520, 420)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        medication = QLineEdit()
        dose = QLineEdit()
        instructions = QTextEdit(); instructions.setMaximumHeight(75)
        reference = QLineEdit()
        schedules = QTextEdit()
        schedules.setPlaceholderText("Una por línea: 08:00|morning")
        schedules.setMaximumHeight(90)
        form.addRow("Medicamento", medication)
        form.addRow("Dosis prescrita", dose)
        form.addRow("Pauta / instrucciones", instructions)
        form.addRow("Referencia de prescripción", reference)
        form.addRow("Horarios prescritos", schedules)
        layout.addLayout(form)
        hint = QLabel("Los horarios deben corresponder a la prescripción vigente. No se modifica aquí la pauta clínica.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        buttons = QHBoxLayout()
        save = QPushButton("Guardar pauta")
        cancel = QPushButton("Cancelar")
        save.clicked.connect(dialog.accept)
        cancel.clicked.connect(dialog.reject)
        buttons.addWidget(save); buttons.addWidget(cancel)
        layout.addLayout(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if not self.stay.currentData():
            QMessageBox.information(self, "Selecciona residente", "Selecciona un residente antes de registrar una pauta.")
            return
        try:
            parsed_schedules = self._read_schedules(schedules.toPlainText())
            if not medication.text().strip() or not dose.text().strip() or not reference.text().strip():
                raise ValueError("Medicamento, dosis y referencia de prescripción son obligatorios.")
            with session_scope(self.factory) as session:
                plan = add_medication_plan(
                    session, actor_account_id=self.actor_id, minor_id=self.stay.currentData(),
                    medication_name=medication.text().strip(), prescribed_dose=dose.text().strip(),
                    schedule_text=instructions.toPlainText().strip(),
                    prescriber_reference=reference.text().strip(), starts_on=date.today(),
                )
                set_medication_schedules(
                    session, actor_account_id=self.actor_id, plan_id=plan.id,
                    schedules=parsed_schedules,
                )
            self.refresh()
            QMessageBox.information(self, "Pauta registrada", "La pauta y sus horarios han quedado registrados.")
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo registrar", str(exc))

    def configure_schedule(self):
        row = self.plans.currentRow()
        cell = self.plans.item(row, 0) if row >= 0 else None
        if not cell:
            QMessageBox.information(self, "Selecciona pauta", "Selecciona primero una pauta.")
            return
        schedule_text, ok = QInputDialog.getMultiLineText(
            self, "Horarios prescritos",
            "Una hora por línea: HH:MM|morning, HH:MM|afternoon o HH:MM|night",
        )
        if not ok:
            return
        try:
            schedules = self._read_schedules(schedule_text)
            with session_scope(self.factory) as session:
                set_medication_schedules(
                    session, actor_account_id=self.actor_id,
                    plan_id=cell.data(Qt.ItemDataRole.UserRole), schedules=schedules,
                )
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudieron configurar horarios", str(exc))

    def administer(self):
        row = self.administrations.currentRow()
        cell = self.administrations.item(row, 0) if row >= 0 else None
        if not cell:
            QMessageBox.information(self, "Selecciona dosis", "Selecciona una dosis prevista del cuadrante.")
            return
        plan_id, planned_iso, shift, existing_record_id = cell.data(Qt.ItemDataRole.UserRole)
        if existing_record_id:
            QMessageBox.information(self, "Ya registrada", "Esta dosis ya tiene un registro.")
            return
        label, ok = QInputDialog.getItem(
            self, "Administración", "Resultado:",
            ["Administrada", "Rechazada", "No disponible"], 0, False,
        )
        if not ok:
            return
        status = {
            "Administrada": "administered", "Rechazada": "refused",
            "No disponible": "not_available",
        }[label]
        note = ""
        if status != "administered":
            note, ok = QInputDialog.getMultiLineText(self, "Motivo", "Motivo obligatorio:")
            if not ok or not note.strip():
                return
        try:
            with session_scope(self.factory) as session:
                record_medication_administration(
                    session, actor_account_id=self.actor_id, plan_id=plan_id,
                    scheduled_at=datetime.fromisoformat(planned_iso),
                    status=status, shift=shift, note=note,
                )
            self.refresh()
            QMessageBox.information(self, "Administración", "Registro añadido.")
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo registrar", str(exc))

    def add_vaccine(self):
        if not self.stay.currentData():
            QMessageBox.information(self, "Selecciona residente", "Selecciona un residente antes de registrar una vacuna.")
            return
        name, ok = QInputDialog.getText(self, "Vacunación", "Vacuna administrada:")
        if not ok or not name.strip():
            return
        try:
            with session_scope(self.factory) as session:
                add_vaccine_record(
                    session, actor_account_id=self.actor_id, minor_id=self.stay.currentData(),
                    vaccine_name=name, administered_on=date.today(),
                )
            self.refresh()
            QMessageBox.information(self, "Vacunación", "Registro añadido.")
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo registrar", str(exc))
