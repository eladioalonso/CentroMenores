"""Interfaz de escritorio con acceso y bloqueo por inactividad."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
import hashlib
import mimetypes
import shutil
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QEvent, QObject, QTimer, Qt, QLockFile, QDateTime, QDate, QUrl
from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QVBoxLayout, QWidget, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QComboBox,
    QDateTimeEdit, QDateEdit, QTextEdit, QFileDialog, QDesktopServices, QCheckBox,
)
from sqlalchemy import func, select

from gestion_centro.auth.models import UserAccount, AccessAudit
from gestion_centro.auth.service import (
    AuthStatus, Role, authenticate, create_professional_account,
    admin_create_professional_account, admin_reset_password,
    admin_set_account_active, admin_change_role,
)
from gestion_centro.paths import data_paths, ensure_data_directories
from gestion_centro.persistence.database import build_engine, build_session_factory, session_scope
from gestion_centro.persistence.migrations import upgrade_database
from gestion_centro.domain.service import (
    close_expired_diary_days, create_agenda_item, list_agenda_items,
    set_agenda_item_status,
)
from gestion_centro.domain.models import Stay
from gestion_centro.domain.documents import PersonalDocument
from gestion_centro.domain.documents_service import register_document, list_documents
from gestion_centro.operations_ui import AuthorizationsDialog, OutingsDialog
from gestion_centro.backups_ui import BackupDialog
from gestion_centro.persistence.backups import create_backup
from gestion_centro.care_ui import EducationDialog, HealthDialog
from gestion_centro.expedientes_ui import ExpedientesDialog
from gestion_centro.maintenance_ui import MaintenanceDialog
from gestion_centro.reports_ui import ReportsDialog
from gestion_centro.external_reports_ui import ExternalReportsDialog
from gestion_centro.diary_ui import DiaryDialog
from gestion_centro.calendar_ui import CalendarDialog
from gestion_centro.help_ui import HelpDialog
from gestion_centro.domain.communications_service import (
    create_communication, add_communication_contribution, close_communication,
    list_communications, move_communication_to_trash, restore_communication,
    reopen_communication,
)
from gestion_centro.domain.communications import CommunicationContribution

IDLE_LIMIT_MS = 15 * 60 * 1000


class CredentialsDialog(QDialog):
    def __init__(self, *, first_admin: bool = False, fixed_username: str | None = None) -> None:
        super().__init__()
        self.first_admin = first_admin
        self.fixed_username = fixed_username
        self.setWindowTitle("Crear administrador inicial" if first_admin else "Iniciar sesión")
        self.username = QLineEdit(fixed_username or "")
        self.username.setMaxLength(80)
        self.username.setReadOnly(fixed_username is not None)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.name = QLineEdit()
        self.name.setMaxLength(160)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        if first_admin:
            form.addRow("Nombre profesional", self.name)
        form.addRow("Usuario", self.username)
        form.addRow("Contraseña", self.password)
        layout.addLayout(form)
        if first_admin:
            note = QLabel("La contraseña debe tener al menos 12 caracteres. El administrador podrá restablecerla si se pierde.")
            note.setWordWrap(True)
            layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str, str]:
        return self.name.text().strip(), self.username.text().strip(), self.password.text()

    def accept(self) -> None:
        name, username, password = self.values()
        if not username or not password or (self.first_admin and not name):
            QMessageBox.warning(self, "Datos incompletos", "Completa todos los campos.")
            return
        if self.first_admin and len(password) < 12:
            QMessageBox.warning(self, "Contraseña insuficiente", "Usa al menos 12 caracteres.")
            return
        super().accept()


class IdleMonitor(QObject):
    """Reinicia el contador ante actividad y bloquea tras 15 minutos."""

    ACTIVITY_EVENTS = {
        QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease,
        QEvent.Type.MouseMove, QEvent.Type.KeyPress, QEvent.Type.KeyRelease,
        QEvent.Type.Wheel, QEvent.Type.TouchBegin, QEvent.Type.TouchUpdate,
    }

    def __init__(self, app: QApplication, on_timeout) -> None:
        super().__init__(app)
        self.app = app
        self.on_timeout = on_timeout
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(IDLE_LIMIT_MS)
        self.timer.timeout.connect(self._timeout)
        app.installEventFilter(self)
        self.timer.start()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() in self.ACTIVITY_EVENTS and self.timer.isActive():
            self.timer.start()
        return False

    def _timeout(self) -> None:
        self.app.removeEventFilter(self)
        self.on_timeout()

    def resume(self) -> None:
        self.app.installEventFilter(self)
        self.timer.start()

    def stop(self) -> None:
        self.timer.stop()
        self.app.removeEventFilter(self)



class AccountManagementDialog(QDialog):
    def __init__(self, factory, actor_id: str) -> None:
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.setWindowTitle("Administración de cuentas")
        self.resize(760, 420)
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Profesional", "Usuario", "Perfil", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        for label, callback in [("Crear cuenta", self.create_account),
            ("Restablecer contraseña", self.reset_password),
            ("Cambiar perfil", self.change_role),
            ("Activar / desactivar", self.toggle_active)]:
            button = QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.refresh()

    def refresh(self) -> None:
        with session_scope(self.factory) as session:
            accounts = session.scalars(select(UserAccount).order_by(UserAccount.username)).all()
            rows = [(a.id, a.professional.display_name, a.username,
                "Administrador" if a.role == Role.ADMIN.value else "Educador",
                "Activa" if a.active and a.professional.active else "Inactiva") for a in accounts]
        self.table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            account_id, *display = values
            for col, value in enumerate(display):
                item = QTableWidgetItem(value)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, account_id)
                self.table.setItem(row, col, item)

    def selected_account_id(self) -> str | None:
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def create_account(self) -> None:
        name, ok = QInputDialog.getText(self, "Nueva cuenta", "Nombre profesional:")
        if not ok or not name.strip(): return
        username, ok = QInputDialog.getText(self, "Nueva cuenta", "Usuario:")
        if not ok or not username.strip(): return
        password, ok = QInputDialog.getText(self, "Nueva cuenta", "Contraseña (mínimo 12 caracteres):", QLineEdit.EchoMode.Password)
        if not ok: return
        role_text, ok = QInputDialog.getItem(self, "Nueva cuenta", "Perfil:", ["Educador", "Administrador"], 0, False)
        if not ok: return
        try:
            with session_scope(self.factory) as session:
                admin_create_professional_account(session, actor_account_id=self.actor_id,
                    display_name=name, username=username, password=password,
                    role=Role.ADMIN if role_text == "Administrador" else Role.EDUCATOR)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo crear la cuenta", str(exc))

    def reset_password(self) -> None:
        target_id = self.selected_account_id()
        if not target_id:
            QMessageBox.information(self, "Selecciona una cuenta", "Selecciona primero una cuenta.")
            return
        password, ok = QInputDialog.getText(self, "Restablecer contraseña",
            "Nueva contraseña (mínimo 12 caracteres):", QLineEdit.EchoMode.Password)
        if not ok: return
        try:
            with session_scope(self.factory) as session:
                admin_reset_password(session, actor_account_id=self.actor_id,
                    target_account_id=target_id, new_password=password)
            QMessageBox.information(self, "Contraseña restablecida", "La nueva contraseña se ha guardado.")
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo restablecer", str(exc))

    def change_role(self) -> None:
        target_id = self.selected_account_id()
        if not target_id:
            QMessageBox.information(self, "Selecciona una cuenta", "Selecciona primero una cuenta.")
            return
        role_text, ok = QInputDialog.getItem(self, "Cambiar perfil", "Nuevo perfil:",
            ["Educador", "Administrador"], 0, False)
        if not ok: return
        try:
            with session_scope(self.factory) as session:
                admin_change_role(session, actor_account_id=self.actor_id,
                    target_account_id=target_id,
                    role=Role.ADMIN if role_text == "Administrador" else Role.EDUCATOR)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo cambiar el perfil", str(exc))

    def toggle_active(self) -> None:
        target_id = self.selected_account_id()
        if not target_id:
            QMessageBox.information(self, "Selecciona una cuenta", "Selecciona primero una cuenta.")
            return
        row = self.table.currentRow()
        active = self.table.item(row, 3).text() == "Activa"
        action = "desactivar" if active else "activar"
        if QMessageBox.question(self, "Confirmar operación", f"¿Quieres {action} esta cuenta?") != QMessageBox.StandardButton.Yes:
            return
        try:
            with session_scope(self.factory) as session:
                admin_set_account_active(session, actor_account_id=self.actor_id,
                    target_account_id=target_id, active=not active)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo cambiar el estado", str(exc))


class AgendaDialog(QDialog):
    """Agenda compartida con asignación individual y filtros básicos."""

    KIND_LABELS = {
        "task": "Tarea", "appointment": "Cita", "activity": "Actividad",
        "meeting": "Reunión", "call": "Llamada", "contact": "Contacto",
        "vaccine": "Vacuna", "birthday": "Cumpleaños", "event": "Evento",
    }
    STATUS_LABELS = {
        "pending": "Pendiente", "in_progress": "En curso",
        "done": "Completada", "cancelled": "Cancelada",
    }

    def __init__(self, factory, actor_id: str) -> None:
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.setWindowTitle("Agenda común y tareas")
        self.resize(980, 640)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.kind = QComboBox()
        for key, label in self.KIND_LABELS.items():
            self.kind.addItem(label, key)
        self.title = QLineEdit()
        self.title.setMaxLength(180)
        self.description = QTextEdit()
        self.description.setMaximumHeight(64)
        self.starts = QDateTimeEdit()
        self.starts.setCalendarPopup(True)
        self.starts.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.starts.setDateTime(QDateTime.currentDateTime())
        self.assignment = QComboBox()
        self.assignment.addItem("Todo el equipo", "team")
        self.assignment.addItem("Una persona", "individual")
        self.assignee = QComboBox()
        with session_scope(factory) as session:
            accounts = session.scalars(select(UserAccount).where(
                UserAccount.active.is_(True)).order_by(UserAccount.username)).all()
            for account in accounts:
                if account.professional.active:
                    self.assignee.addItem(account.professional.display_name, account.id)
        self.assignee.setEnabled(False)
        self.assignment.currentIndexChanged.connect(
            lambda: self.assignee.setEnabled(self.assignment.currentData() == "individual"))
        form.addRow("Tipo", self.kind)
        form.addRow("Título", self.title)
        form.addRow("Descripción", self.description)
        form.addRow("Fecha y hora", self.starts)
        form.addRow("Asignación", self.assignment)
        form.addRow("Responsable individual", self.assignee)
        layout.addLayout(form)
        create = QPushButton("Añadir a la agenda")
        create.clicked.connect(self.create_item)
        layout.addWidget(create)

        filters = QHBoxLayout()
        self.kind_filter = QComboBox()
        self.kind_filter.addItem("Todos los tipos", None)
        for key, label in self.KIND_LABELS.items():
            self.kind_filter.addItem(label, key)
        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos los estados", None)
        for key, label in self.STATUS_LABELS.items():
            self.status_filter.addItem(label, key)
        self.kind_filter.currentIndexChanged.connect(self.refresh)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(QLabel("Filtrar tipo"))
        filters.addWidget(self.kind_filter)
        filters.addWidget(QLabel("Filtrar estado"))
        filters.addWidget(self.status_filter)
        layout.addLayout(filters)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Fecha", "Tipo / título", "Estado", "Asignación", "Responsable"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        self.status = QComboBox()
        for key, label in self.STATUS_LABELS.items():
            self.status.addItem(label, key)
        actions.addWidget(self.status)
        update = QPushButton("Cambiar estado")
        update.clicked.connect(self.change_status)
        actions.addWidget(update)
        refresh = QPushButton("Actualizar")
        refresh.clicked.connect(self.refresh)
        actions.addWidget(refresh)
        layout.addLayout(actions)
        self.refresh()

    def refresh(self) -> None:
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        with session_scope(self.factory) as session:
            items = list_agenda_items(session, start=now - timedelta(days=365),
                end=now + timedelta(days=730), kind=self.kind_filter.currentData(),
                status=self.status_filter.currentData())
            rows = []
            for item in items:
                assignee = session.get(UserAccount, item.assigned_account_id) if item.assigned_account_id else None
                responsible = (assignee.professional.display_name
                    if assignee and assignee.professional else "—")
                rows.append((item.id, item.starts_at.astimezone().strftime("%d/%m/%Y %H:%M"),
                    f"{self.KIND_LABELS.get(item.kind, item.kind)} · {item.title}",
                    self.STATUS_LABELS.get(item.status, item.status),
                    "Equipo" if item.assignment_scope == "team" else "Individual",
                    responsible))
        self.table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            item_id, *display = values
            for col, value in enumerate(display):
                cell = QTableWidgetItem(value)
                if col == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, item_id)
                self.table.setItem(row, col, cell)

    def create_item(self) -> None:
        from datetime import timezone
        title = self.title.text().strip()
        if not title:
            QMessageBox.warning(self, "Falta el título", "El título es obligatorio.")
            return
        scope = self.assignment.currentData()
        if scope == "individual" and not self.assignee.currentData():
            QMessageBox.warning(self, "Falta responsable", "Selecciona el profesional responsable.")
            return
        local_value = self.starts.dateTime().toPython()
        starts_at = local_value.astimezone(timezone.utc) if local_value.tzinfo else local_value.astimezone().astimezone(timezone.utc)
        try:
            with session_scope(self.factory) as session:
                create_agenda_item(session, actor_account_id=self.actor_id,
                    kind=self.kind.currentData(), title=title, description=self.description.toPlainText(),
                    starts_at=starts_at, assignment_scope=scope,
                    assigned_account_id=self.assignee.currentData() if scope == "individual" else None)
            self.title.clear()
            self.description.clear()
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

    def change_status(self) -> None:
        row = self.table.currentRow()
        cell = self.table.item(row, 0) if row >= 0 else None
        if cell is None:
            QMessageBox.information(self, "Selecciona un elemento", "Selecciona primero una tarea o cita.")
            return
        try:
            with session_scope(self.factory) as session:
                set_agenda_item_status(session, actor_account_id=self.actor_id,
                    item_id=cell.data(Qt.ItemDataRole.UserRole), status=self.status.currentData())
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo cambiar el estado", str(exc))


class CommunicationsDialog(QDialog):
    """Bandeja compartida con lectura cronológica, papelera y reapertura admin."""
    def __init__(self, factory, actor_id: str) -> None:
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.show_trash = False
        self.setWindowTitle("Comunicaciones internas")
        self.resize(900, 600)
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Título", "Estado", "Última actualización", "Creada por"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        controls = [
            ("Nueva", self.create_item), ("Ver aportaciones", self.view_notes),
            ("Añadir aportación", self.add_note), ("Cerrar", self.close_item),
            ("Enviar a papelera", self.trash_item), ("Reabrir", self.reopen_item),
            ("Papelera / bandeja", self.toggle_trash), ("Recuperar", self.restore_item),
            ("Actualizar", self.refresh),
        ]
        for label, callback in controls:
            button = QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.refresh()

    def refresh(self) -> None:
        with session_scope(self.factory) as session:
            items = list_communications(session, include_trash=self.show_trash)
            rows = [(x.id, x.title, "En papelera" if x.deleted_at else
                ("Abierta" if x.status == "draft" else "Cerrada"),
                x.updated_at.astimezone().strftime("%d/%m/%Y %H:%M"),
                x.created_by_name_snapshot) for x in items]
        self.table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            item_id, *display = values
            for col, value in enumerate(display):
                cell = QTableWidgetItem(value)
                if col == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, item_id)
                self.table.setItem(row, col, cell)

    def selected_id(self):
        row = self.table.currentRow()
        cell = self.table.item(row, 0) if row >= 0 else None
        return cell.data(Qt.ItemDataRole.UserRole) if cell else None

    def create_item(self) -> None:
        title, ok = QInputDialog.getText(self, "Nueva comunicación", "Título:")
        if not ok or not title.strip(): return
        content, ok = QInputDialog.getMultiLineText(self, "Nueva comunicación", "Primera aportación:")
        if not ok or not content.strip(): return
        try:
            with session_scope(self.factory) as session:
                create_communication(session, actor_account_id=self.actor_id, title=title, content=content)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

    def view_notes(self) -> None:
        item_id = self.selected_id()
        if not item_id: return
        with session_scope(self.factory) as session:
            notes = session.scalars(select(CommunicationContribution)
                .where(CommunicationContribution.communication_id == item_id)
                .order_by(CommunicationContribution.created_at)).all()
            lines = [f"{n.created_at.astimezone().strftime('%d/%m/%Y %H:%M')} · {n.author_name_snapshot}\n{n.content}" for n in notes]
        QMessageBox.information(self, "Historial de aportaciones", "\n\n".join(lines) or "Sin aportaciones.")

    def add_note(self) -> None:
        item_id = self.selected_id()
        if not item_id:
            QMessageBox.information(self, "Selecciona", "Selecciona una comunicación.")
            return
        content, ok = QInputDialog.getMultiLineText(self, "Aportación", "Texto:")
        if not ok or not content.strip(): return
        try:
            with session_scope(self.factory) as session:
                add_communication_contribution(session, actor_account_id=self.actor_id,
                    communication_id=item_id, content=content)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo añadir", str(exc))

    def close_item(self) -> None:
        item_id = self.selected_id()
        if not item_id: return
        reason, ok = QInputDialog.getText(self, "Cerrar comunicación", "Motivo:")
        if not ok or not reason.strip(): return
        try:
            with session_scope(self.factory) as session:
                close_communication(session, actor_account_id=self.actor_id,
                    communication_id=item_id, reason=reason)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo cerrar", str(exc))

    def trash_item(self) -> None:
        item_id = self.selected_id()
        if not item_id: return
        if QMessageBox.question(self, "Papelera", "¿Enviar esta comunicación a la papelera?") != QMessageBox.StandardButton.Yes:
            return
        try:
            with session_scope(self.factory) as session:
                move_communication_to_trash(session, actor_account_id=self.actor_id, communication_id=item_id)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo mover", str(exc))

    def toggle_trash(self) -> None:
        self.show_trash = not self.show_trash
        self.refresh()

    def restore_item(self) -> None:
        item_id = self.selected_id()
        if not item_id: return
        try:
            with session_scope(self.factory) as session:
                restore_communication(session, actor_account_id=self.actor_id, communication_id=item_id)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo recuperar", str(exc))

    def reopen_item(self) -> None:
        item_id = self.selected_id()
        if not item_id: return
        reason, ok = QInputDialog.getText(self, "Reabrir comunicación", "Motivo (solo administración):")
        if not ok or not reason.strip(): return
        try:
            with session_scope(self.factory) as session:
                reopen_communication(session, actor_account_id=self.actor_id,
                    communication_id=item_id, reason=reason)
            self.refresh()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo reabrir", str(exc))


class DocumentsDialog(QDialog):
    """Registro y consulta de documentos personales con almacenamiento portable."""
    CATEGORIES = {
        "Identificación": "identity", "Sanitaria": "health",
        "Administrativa": "administrative", "Educativa": "education",
        "Familiar": "family", "Otros": "other",
    }

    def __init__(self, factory, actor_id: str, paths) -> None:
        super().__init__()
        self.factory, self.actor_id, self.paths = factory, actor_id, paths
        self.setWindowTitle("Documentación personal")
        self.resize(900, 540)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.stay = QComboBox()
        with session_scope(factory) as session:
            stays = session.scalars(select(Stay).where(Stay.status == "active").order_by(Stay.started_on.desc())).all()
            values = [(s.id, f"{s.minor.internal_code} · {s.minor.given_names} {s.minor.family_names}") for s in stays]
        for stay_id, label in values:
            self.stay.addItem(label, stay_id)
        self.category = QComboBox()
        for label, key in self.CATEGORIES.items():
            self.category.addItem(label, key)
        self.title = QLineEdit()
        self.title.setMaxLength(180)
        self.supersedes = QComboBox()
        self.supersedes.addItem("Documento nuevo (versión 1)", None)
        self.expiry = QDateEdit(QDate.currentDate().addYears(1))
        self.expiry.setCalendarPopup(True)
        self.no_expiry = QCheckBox("Sin caducidad")
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(48)
        self.file_label = QLabel("Ningún archivo seleccionado")
        self.selected_file: Path | None = None
        choose = QPushButton("Seleccionar archivo…")
        choose.clicked.connect(self.choose_file)
        form.addRow("Estancia activa", self.stay)
        form.addRow("Categoría", self.category)
        form.addRow("Título", self.title)
        form.addRow("Sustituye a (nueva versión)", self.supersedes)
        form.addRow("Caduca el", self.expiry)
        form.addRow("", self.no_expiry)
        form.addRow("Notas", self.notes)
        form.addRow("Archivo", choose)
        form.addRow("Seleccionado", self.file_label)
        layout.addLayout(form)
        save = QPushButton("Guardar documento")
        save.clicked.connect(self.save_document)
        layout.addWidget(save)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Título", "Categoría", "Archivo", "Versión", "Caducidad"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        open_button = QPushButton("Abrir documento seleccionado")
        open_button.clicked.connect(self.open_selected)
        actions.addWidget(open_button)
        layout.addLayout(actions)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stay.currentIndexChanged.connect(self.refresh)
        self.category.currentIndexChanged.connect(self.refresh_supersedes)
        self.refresh()

    def refresh_supersedes(self):
        selected = self.supersedes.currentData()
        self.supersedes.blockSignals(True)
        self.supersedes.clear()
        self.supersedes.addItem("Documento nuevo (versión 1)", None)
        stay_id = self.stay.currentData()
        if stay_id:
            with session_scope(self.factory) as session:
                docs = session.scalars(select(PersonalDocument).where(
                    PersonalDocument.stay_id == stay_id,
                    PersonalDocument.category == self.category.currentData()
                ).order_by(PersonalDocument.created_at.desc())).all()
                for doc in docs:
                    self.supersedes.addItem(
                        f"{doc.title} · v{doc.version} · {doc.original_filename}",
                        doc.id
                    )
        index = self.supersedes.findData(selected)
        self.supersedes.setCurrentIndex(index if index >= 0 else 0)
        self.supersedes.blockSignals(False)

    def choose_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Seleccionar documento")
        if filename:
            self.selected_file = Path(filename)
            self.file_label.setText(self.selected_file.name)

    def refresh(self):
        stay_id = self.stay.currentData()
        if not stay_id:
            self.table.setRowCount(0)
            self.refresh_supersedes()
            return
        self.refresh_supersedes()
        with session_scope(self.factory) as session:
            docs = list_documents(session, actor_account_id=self.actor_id, stay_id=stay_id)
            rows = [(d.id, d.title, d.category, d.original_filename, str(d.version),
                     d.expires_on.strftime("%d/%m/%Y") if d.expires_on else "—") for d in docs]
        self.table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            doc_id, *display = values
            for col, value in enumerate(display):
                cell = QTableWidgetItem(value)
                if col == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, doc_id)
                self.table.setItem(row, col, cell)

    def open_selected(self):
        row = self.table.currentRow()
        cell = self.table.item(row, 0) if row >= 0 else None
        if cell is None:
            QMessageBox.information(self, "Selecciona", "Selecciona un documento.")
            return
        try:
            with session_scope(self.factory) as session:
                doc = session.get(PersonalDocument, cell.data(Qt.ItemDataRole.UserRole))
                if doc is None:
                    raise ValueError("El documento ya no existe.")
                relative = Path(doc.relative_path)
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError("La ruta del documento no es segura.")
                target = (self.paths.root / relative).resolve()
                if self.paths.root.resolve() not in target.parents or not target.is_file():
                    raise ValueError("No se encuentra el archivo dentro de la carpeta portable.")
                with target.open("rb") as stream:
                    actual = hashlib.file_digest(stream, "sha256").hexdigest()
                if actual != doc.sha256:
                    raise ValueError("El hash no coincide. El archivo puede haber sido alterado.")
                actor = session.get(UserAccount, self.actor_id)
                if actor is None or not actor.active:
                    raise PermissionError("La cuenta ya no está activa.")
                session.add(AccessAudit(account_id=actor.id,
                    username_snapshot=actor.username, event="personal_document_opened",
                    details=f"{doc.id}; estancia:{doc.stay_id}"))
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(target))):
                raise OSError("Windows no ha podido abrir el documento.")
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "No se pudo abrir", str(exc))

    def save_document(self):
        stay_id = self.stay.currentData()
        if not stay_id or self.selected_file is None or not self.selected_file.is_file():
            QMessageBox.warning(self, "Faltan datos", "Selecciona una estancia y un archivo válido.")
            return
        title = self.title.text().strip()
        if not title:
            QMessageBox.warning(self, "Falta el título", "El título documental es obligatorio.")
            return
        source = self.selected_file
        if source.stat().st_size <= 0 or source.stat().st_size > 25 * 1024 * 1024:
            QMessageBox.warning(self, "Tamaño no permitido", "El archivo debe ocupar entre 1 byte y 25 MB.")
            return
        with source.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        relative_dir = Path(str(uuid4()))
        target_dir = self.paths.documents / relative_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        try:
            shutil.copy2(source, target)
            relative_path = target.relative_to(self.paths.root).as_posix()
            mime_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
            with session_scope(self.factory) as session:
                register_document(
                    session, actor_account_id=self.actor_id, stay_id=stay_id,
                    category=self.category.currentData(), title=title,
                    original_filename=source.name, relative_path=relative_path,
                    mime_type=mime_type, size_bytes=target.stat().st_size,
                    sha256=digest, expires_on=None if self.no_expiry.isChecked() else self.expiry.date().toPython(),
                    notes=self.notes.toPlainText(), supersedes_id=self.supersedes.currentData(),
                )
            self.title.clear()
            self.notes.clear()
            self.selected_file = None
            self.file_label.setText("Ningún archivo seleccionado")
            self.refresh()
        except (OSError, ValueError, PermissionError) as exc:
            target.unlink(missing_ok=True)
            try:
                target_dir.rmdir()
            except OSError:
                pass
            QMessageBox.warning(self, "No se pudo guardar", str(exc))


class MainWindow(QMainWindow):
    def __init__(self, display_name: str, role: Role, factory=None, account_id: str | None = None, paths=None) -> None:
        super().__init__()
        self.setWindowTitle("Gestión del Centro")
        self.resize(1100, 720)
        self.setMinimumSize(900, 600)
        page = QWidget()
        layout = QVBoxLayout(page)
        heading = QLabel("Gestión del Centro")
        heading.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(heading)
        layout.addWidget(QLabel(f"Sesión iniciada: {display_name} · Perfil: {'Administrador' if role is Role.ADMIN else 'Educador'}"))
        help_button = QPushButton("Ayuda y preguntas frecuentes")
        help_button.clicked.connect(lambda: HelpDialog(self).exec())
        layout.addWidget(help_button)
        if role is Role.ADMIN and factory is not None and account_id is not None:
            manage = QPushButton("Administrar cuentas")
            manage.clicked.connect(lambda: AccountManagementDialog(factory, account_id).exec())
            layout.addWidget(manage)
            backups = QPushButton("Copias de seguridad")
            backups.clicked.connect(lambda: BackupDialog(paths, factory, account_id).exec())
            layout.addWidget(backups)
            maintenance = QPushButton("Mantenimiento y diagnóstico")
            maintenance.clicked.connect(lambda: MaintenanceDialog(paths, factory, account_id).exec())
            layout.addWidget(maintenance)
            reports = QPushButton("Estadísticas y memoria")
            reports.clicked.connect(lambda: ReportsDialog(factory, account_id).exec())
            layout.addWidget(reports)
        if factory is not None and account_id is not None:
            expedientes = QPushButton("Expedientes y estancias")
            expedientes.clicked.connect(lambda: ExpedientesDialog(factory, account_id).exec())
            layout.addWidget(expedientes)
            diary = QPushButton("Diario e incidencias")
            diary.clicked.connect(lambda: DiaryDialog(factory, account_id).exec())
            layout.addWidget(diary)
            agenda = QPushButton("Agenda común y tareas")
            agenda.clicked.connect(lambda: AgendaDialog(factory, account_id).exec())
            layout.addWidget(agenda)
            calendar = QPushButton("Calendario día / semana / mes / año")
            calendar.clicked.connect(lambda: CalendarDialog(factory, account_id).exec())
            layout.addWidget(calendar)
            documents = QPushButton("Documentación personal")
            documents.clicked.connect(lambda: DocumentsDialog(factory, account_id, paths).exec())
            layout.addWidget(documents)
            authorizations = QPushButton("Autorizaciones")
            authorizations.clicked.connect(lambda: AuthorizationsDialog(factory, account_id).exec())
            layout.addWidget(authorizations)
            outings = QPushButton("Salidas")
            outings.clicked.connect(lambda: OutingsDialog(factory, account_id).exec())
            layout.addWidget(outings)
            education = QPushButton("Seguimiento educativo y escolaridad")
            education.clicked.connect(lambda: EducationDialog(factory, account_id).exec())
            layout.addWidget(education)
            health = QPushButton("Ficha sanitaria y medicación")
            health.clicked.connect(lambda: HealthDialog(factory, account_id).exec())
            layout.addWidget(health)
            communications = QPushButton("Comunicaciones internas")
            communications.clicked.connect(lambda: CommunicationsDialog(factory, account_id).exec())
            layout.addWidget(communications)
            external_reports = QPushButton("Informes externos")
            external_reports.clicked.connect(lambda: ExternalReportsDialog(factory, account_id).exec())
            layout.addWidget(external_reports)
        notice = QLabel(
            "Núcleo técnico en desarrollo. Todavía no está habilitado para introducir datos reales "
            "de menores ni para uso asistencial."
        )
        notice.setWordWrap(True)
        notice.setStyleSheet("padding: 18px;")
        layout.addWidget(notice)
        self.setCentralWidget(page)


def main() -> int:
    demo_mode = "--demo" in sys.argv
    qt_args = [arg for arg in sys.argv if arg != "--demo"]
    app = QApplication(qt_args)
    app.setApplicationName("Gestión del Centro")
    if demo_mode:
        demo_root = (Path(sys.executable).resolve().parent / "demo_data"
                     if getattr(sys, "frozen", False)
                     else Path(__file__).resolve().parents[2] / ".centro_demo")
        paths = data_paths(demo_root)
    else:
        paths = data_paths()
    ensure_data_directories(paths)
    instance_lock = QLockFile(str(paths.root / ".gestion_centro.lock"))
    instance_lock.setStaleLockTime(0)
    if not instance_lock.tryLock(100):
        QMessageBox.warning(None, "Aplicación ya abierta", "Ya hay otra instancia de Gestión del Centro utilizando esta carpeta de datos.")
        return 1
    engine = build_engine(paths.database)
    try:
        upgrade_database(engine)
    except Exception as exc:
        QMessageBox.critical(None, "Error de base de datos", f"No se pudo preparar la base de datos de forma segura:\n{exc}")
        engine.dispose()
        instance_lock.unlock()
        return 1
    factory = build_session_factory(engine)

    # Copia diaria local: una por día UTC. La sincronización externa queda pendiente
    # hasta que el administrador conecte la unidad USB desde la interfaz.
    daily_stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    if not any(paths.backups.glob(f"daily-{daily_stamp}T*.zip")):
        try:
            create_backup(paths, kind="daily")
        except (OSError, ValueError) as exc:
            QMessageBox.warning(None, "Copia diaria no creada",
                f"No se pudo completar la copia diaria. Comprueba el espacio y los permisos.\n{exc}")

    # El autocierre se ejecuta en una transacción propia al arrancar para que
    # permanezca guardado aunque después se rechace una anotación tardía.
    with session_scope(factory) as session:
        close_expired_diary_days(session)
        first_admin = session.scalar(select(func.count()).select_from(UserAccount)) == 0

    authenticated = None
    login_failures = 0
    while authenticated is None:
        dialog = CredentialsDialog(first_admin=first_admin)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            engine.dispose()
            instance_lock.unlock()
            return 0
        name, username, password = dialog.values()
        try:
            with session_scope(factory) as session:
                if first_admin:
                    create_professional_account(
                        session, display_name=name, username=username,
                        password=password, role=Role.ADMIN,
                    )
                    first_admin = False
                result = authenticate(session, username=username, password=password)
            if result.status is AuthStatus.SUCCESS:
                authenticated = result
                login_failures = 0
            else:
                login_failures += 1
            if result.status is AuthStatus.RETRY_FLOW_CLOSED or login_failures >= 5:
                QMessageBox.warning(None, "Acceso cerrado", "Cinco intentos fallidos. El proceso de acceso se cerrará.")
                engine.dispose()
                instance_lock.unlock()
                return 1
            elif result.status is not AuthStatus.SUCCESS:
                QMessageBox.warning(None, "Acceso no válido", "Usuario o contraseña incorrectos, o cuenta inactiva.")
        except ValueError as exc:
            QMessageBox.warning(None, "No se pudo crear la cuenta", str(exc))

    with session_scope(factory) as session:
        account = session.get(UserAccount, authenticated.account_id)
        display_name = account.professional.display_name if account else "Profesional"
        username = account.username if account else ""
        role = authenticated.role or Role.EDUCATOR

    window = MainWindow(display_name, role, factory, authenticated.account_id, paths)
    if demo_mode:
        window.setWindowTitle("Gestión del Centro · DEMOSTRACIÓN · datos separados")
    monitor = None

    def lock_session() -> None:
        nonlocal monitor
        window.hide()
        QMessageBox.information(None, "Sesión bloqueada", "La sesión se ha bloqueado por 15 minutos de inactividad. Introduce de nuevo tu contraseña para continuar.")
        failures = 0
        while True:
            lock_dialog = CredentialsDialog(fixed_username=username)
            if lock_dialog.exec() != QDialog.DialogCode.Accepted:
                app.quit()
                return
            _, _, lock_password = lock_dialog.values()
            with session_scope(factory) as session:
                result = authenticate(session, username=username, password=lock_password)
            if result.status is AuthStatus.SUCCESS and result.account_id == authenticated.account_id:
                window.show()
                monitor.resume()
                return
            failures += 1
            if failures >= 5 or result.status is AuthStatus.RETRY_FLOW_CLOSED:
                QMessageBox.warning(None, "Acceso cerrado", "Se ha cerrado la sesión tras cinco intentos fallidos.")
                app.quit()
                return
            QMessageBox.warning(None, "Contraseña incorrecta", "La contraseña no es válida. La sesión continúa bloqueada.")

    monitor = IdleMonitor(app, lock_session)
    window.show()
    result = app.exec()
    monitor.stop()
    with session_scope(factory) as session:
        from gestion_centro.auth.models import AccessAudit
        session.add(AccessAudit(account_id=authenticated.account_id, username_snapshot=username, event="logout"))
    engine.dispose()
    instance_lock.unlock()
    return result
