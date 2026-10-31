"""Interfaces de seguimiento educativo y sanitario."""
from datetime import date, datetime, timezone

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QLineEdit, QTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QHBoxLayout, QInputDialog,
)
from sqlalchemy import select

from gestion_centro.persistence.database import session_scope
from gestion_centro.domain.models import Stay
from gestion_centro.domain.education import EducationGoal, SchoolPlacement
from gestion_centro.domain.education_service import (
    create_education_goal, add_education_update, set_education_goal_status,
    create_school_placement, add_school_record,
)
from gestion_centro.domain.health import HealthProfile, MedicationPlan, MedicationAdministration, VaccineRecord
from gestion_centro.domain.health_service import (
    read_health_profile, save_health_profile, add_medication_plan,
    record_medication_administration, add_vaccine_record, list_medication_plans,
)


class StaySelectorDialog(QDialog):
    def __init__(self, factory, title):
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
        layout.addWidget(self.stay)
        self.body = QVBoxLayout()
        layout.addLayout(self.body)


class EducationDialog(StaySelectorDialog):
    def __init__(self, factory, actor_id):
        super().__init__(factory, "Seguimiento educativo y escolaridad")
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
        self.updates = QTableWidget(0, 5)
        self.updates.setHorizontalHeaderLabels(["Fecha", "Área", "Observación", "Actuación", "Respuesta / seguimiento"])
        self.updates.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.updates.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.body.addWidget(self.updates)
        actions = QHBoxLayout()
        for label, callback in [("Añadir seguimiento", self.add_update),
                                ("Cambiar estado", self.change_status),
                                ("Nueva escolarización", self.add_school)]:
            b = QPushButton(label); b.clicked.connect(callback); actions.addWidget(b)
        self.body.addLayout(actions)
        self.stay.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        stay_id = self.stay.currentData()
        with session_scope(self.factory) as session:
            rows = session.scalars(select(EducationGoal).where(EducationGoal.stay_id == stay_id)
                .order_by(EducationGoal.created_at.desc())).all() if stay_id else []
            data = [(g.id, g.title, g.status, g.target_date.isoformat() if g.target_date else "—") for g in rows]
            updates = [(u.created_at, u.category, u.objective_description, u.actions_taken,
                u.response_observed + (" · Seguimiento: " + u.follow_up if u.follow_up else ""))
                for g in rows for u in g.updates]
        self.goals.setRowCount(len(data))
        for i, values in enumerate(data):
            item_id, *display = values
            for col, value in enumerate(display):
                cell = QTableWidgetItem(value)
                if col == 0: cell.setData(Qt.ItemDataRole.UserRole, item_id)
                self.goals.setItem(i, col, cell)
        updates.sort(key=lambda row: row[0], reverse=True)
        self.updates.setRowCount(len(updates))
        for i, (created, category, observation, actions, response) in enumerate(updates):
            values = [created.astimezone().strftime("%d/%m/%Y %H:%M"), category, observation, actions, response]
            for col, value in enumerate(values): self.updates.setItem(i, col, QTableWidgetItem(value))

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
        category, ok = QInputDialog.getItem(self, "Seguimiento", "Área:",
            ["Autonomía", "Convivencia", "Emocional", "Social", "Aprendizaje", "Hábitos de salud", "Otra"], 0, False)
        if not ok: return
        mapping = {"Autonomía":"autonomy","Convivencia":"coexistence","Emocional":"emotional",
                   "Social":"social","Aprendizaje":"learning","Hábitos de salud":"health_habits","Otra":"other"}
        fields = []
        for prompt in ["Observación objetiva:", "Actuaciones realizadas:", "Respuesta observada:", "Seguimiento pendiente (opcional):"]:
            value, ok = QInputDialog.getMultiLineText(self, "Seguimiento educativo", prompt)
            if not ok: return
            fields.append(value)
        try:
            with session_scope(self.factory) as session:
                add_education_update(session, actor_account_id=self.actor_id, goal_id=goal_id,
                    category=mapping[category], objective_description=fields[0],
                    actions_taken=fields[1], response_observed=fields[2], follow_up=fields[3])
            QMessageBox.information(self, "Guardado", "Seguimiento añadido al historial.")
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

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
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))


class HealthDialog(StaySelectorDialog):
    def __init__(self, factory, actor_id):
        super().__init__(factory, "Ficha sanitaria y medicación")
        self.actor_id = actor_id
        form = QFormLayout()
        self.allergies = QTextEdit(); self.allergies.setMaximumHeight(55)
        self.conditions = QTextEdit(); self.conditions.setMaximumHeight(55)
        self.emergency = QTextEdit(); self.emergency.setMaximumHeight(55)
        form.addRow("Alergias", self.allergies)
        form.addRow("Condiciones relevantes", self.conditions)
        form.addRow("Instrucciones de emergencia", self.emergency)
        self.body.addLayout(form)
        save = QPushButton("Guardar ficha sanitaria"); save.clicked.connect(self.save_profile)
        self.body.addWidget(save)
        self.plans = QTableWidget(0, 4)
        self.plans.setHorizontalHeaderLabels(["Medicamento", "Dosis prescrita", "Pauta", "Vigencia"])
        self.plans.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.plans.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.plans.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.body.addWidget(self.plans)
        actions = QHBoxLayout()
        for label, callback in [("Registrar pauta prescrita", self.add_plan),
                                ("Registrar administración", self.administer),
                                ("Registrar vacuna", self.add_vaccine)]:
            b = QPushButton(label); b.clicked.connect(callback); actions.addWidget(b)
        self.body.addLayout(actions)
        self.administrations = QTableWidget(0, 5)
        self.administrations.setHorizontalHeaderLabels(["Fecha / hora", "Medicamento", "Resultado", "Motivo / nota", "Registrado por"])
        self.administrations.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.administrations.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.body.addWidget(self.administrations)
        self.vaccines = QTableWidget(0, 3)
        self.vaccines.setHorizontalHeaderLabels(["Vacuna", "Fecha", "Dosis / referencia"])
        self.vaccines.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vaccines.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.body.addWidget(self.vaccines)
        self.stay.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        stay_id = self.stay.currentData()
        if not stay_id: return
        with session_scope(self.factory) as session:
            profile = read_health_profile(session, actor_account_id=self.actor_id, stay_id=stay_id)
            plans = list_medication_plans(session, actor_account_id=self.actor_id, stay_id=stay_id)
            vaccine_rows = session.scalars(select(VaccineRecord).where(VaccineRecord.stay_id == stay_id).order_by(VaccineRecord.administered_on.desc())).all()
            administration_rows = [(a, p.medication_name) for p in plans for a in p.administrations]
        self.allergies.setPlainText(profile.allergies or "" if profile else "")
        self.conditions.setPlainText(profile.relevant_conditions or "" if profile else "")
        self.emergency.setPlainText(profile.emergency_instructions or "" if profile else "")
        self.plans.setRowCount(len(plans))
        for i, p in enumerate(plans):
            values = [p.medication_name, p.prescribed_dose, p.schedule_text,
                      f"{p.starts_on:%d/%m/%Y} – {p.ends_on:%d/%m/%Y}" if p.ends_on else "Sin fecha final"]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if col == 0: cell.setData(Qt.ItemDataRole.UserRole, p.id)
                self.plans.setItem(i, col, cell)
        admin_rows = sorted(administration_rows, key=lambda x: x[0].scheduled_at, reverse=True)
        self.administrations.setRowCount(len(admin_rows))
        for i, (record, medication) in enumerate(admin_rows):
            values = [record.scheduled_at.astimezone().strftime("%d/%m/%Y %H:%M"), medication, record.status, record.note or "—", record.recorded_by_name_snapshot]
            for col, value in enumerate(values): self.administrations.setItem(i, col, QTableWidgetItem(value))
        self.vaccines.setRowCount(len(vaccine_rows))
        for i, record in enumerate(vaccine_rows):
            values = [record.vaccine_name, record.administered_on.strftime("%d/%m/%Y"), record.dose_reference or "—"]
            for col, value in enumerate(values): self.vaccines.setItem(i, col, QTableWidgetItem(value))

    def save_profile(self):
        try:
            with session_scope(self.factory) as session:
                save_health_profile(session, actor_account_id=self.actor_id,
                    stay_id=self.stay.currentData(), allergies=self.allergies.toPlainText(),
                    relevant_conditions=self.conditions.toPlainText(),
                    emergency_instructions=self.emergency.toPlainText())
            QMessageBox.information(self, "Ficha sanitaria", "Datos guardados y auditados.")
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

    def add_plan(self):
        fields = []
        for prompt in ["Medicamento:", "Dosis indicada en prescripción:", "Pauta indicada:", "Referencia de prescripción:"]:
            value, ok = QInputDialog.getText(self, "Nueva pauta", prompt)
            if not ok or not value.strip(): return
            fields.append(value)
        try:
            with session_scope(self.factory) as session:
                add_medication_plan(session, actor_account_id=self.actor_id, stay_id=self.stay.currentData(),
                    medication_name=fields[0], prescribed_dose=fields[1], schedule_text=fields[2],
                    prescriber_reference=fields[3], starts_on=date.today())
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo registrar", str(exc))

    def administer(self):
        row = self.plans.currentRow()
        cell = self.plans.item(row, 0) if row >= 0 else None
        if not cell:
            QMessageBox.information(self, "Selecciona pauta", "Selecciona una pauta.")
            return
        label, ok = QInputDialog.getItem(self, "Administración", "Resultado:",
            ["Administrada", "Rechazada", "No disponible"], 0, False)
        if not ok: return
        status = {"Administrada":"administered","Rechazada":"refused","No disponible":"not_available"}[label]
        note = ""
        if status != "administered":
            note, ok = QInputDialog.getMultiLineText(self, "Motivo", "Motivo obligatorio:")
            if not ok or not note.strip(): return
        try:
            with session_scope(self.factory) as session:
                record_medication_administration(session, actor_account_id=self.actor_id,
                    plan_id=cell.data(Qt.ItemDataRole.UserRole), scheduled_at=datetime.now(timezone.utc),
                    status=status, note=note)
            QMessageBox.information(self, "Administración", "Registro añadido.")
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo registrar", str(exc))

    def add_vaccine(self):
        name, ok = QInputDialog.getText(self, "Vacunación", "Vacuna administrada:")
        if not ok or not name.strip(): return
        try:
            with session_scope(self.factory) as session:
                add_vaccine_record(session, actor_account_id=self.actor_id, stay_id=self.stay.currentData(),
                    vaccine_name=name, administered_on=date.today())
            QMessageBox.information(self, "Vacunación", "Registro añadido.")
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo registrar", str(exc))
