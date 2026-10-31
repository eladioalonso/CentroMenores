"""Interfaz de escritorio con acceso y bloqueo por inactividad."""

from __future__ import annotations

import sys

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QVBoxLayout, QWidget,
)
from sqlalchemy import func, select

from gestion_centro.auth.models import UserAccount
from gestion_centro.auth.service import (
    AuthStatus, Role, authenticate, create_professional_account,
)
from gestion_centro.paths import data_paths, ensure_data_directories
from gestion_centro.persistence.base import Base
from gestion_centro.persistence.database import build_engine, build_session_factory, session_scope

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


class MainWindow(QMainWindow):
    def __init__(self, display_name: str, role: Role) -> None:
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
        notice = QLabel(
            "Núcleo técnico en desarrollo. Todavía no está habilitado para introducir datos reales "
            "de menores ni para uso asistencial."
        )
        notice.setWordWrap(True)
        notice.setStyleSheet("padding: 18px;")
        layout.addWidget(notice)
        self.setCentralWidget(page)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Gestión del Centro")
    paths = data_paths()
    ensure_data_directories(paths)
    engine = build_engine(paths.database)
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)

    with session_scope(factory) as session:
        first_admin = session.scalar(select(func.count()).select_from(UserAccount)) == 0

    authenticated = None
    while authenticated is None:
        dialog = CredentialsDialog(first_admin=first_admin)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            engine.dispose()
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
            elif result.status is AuthStatus.RETRY_FLOW_CLOSED:
                QMessageBox.warning(None, "Acceso cerrado", "Cinco intentos fallidos. Inicia de nuevo el proceso de acceso.")
            else:
                QMessageBox.warning(None, "Acceso no válido", "Usuario o contraseña incorrectos, o cuenta inactiva.")
        except ValueError as exc:
            QMessageBox.warning(None, "No se pudo crear la cuenta", str(exc))

    with session_scope(factory) as session:
        account = session.get(UserAccount, authenticated.account_id)
        display_name = account.professional.display_name if account else "Profesional"
        username = account.username if account else ""
        role = authenticated.role or Role.EDUCATOR

    window = MainWindow(display_name, role)
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
    engine.dispose()
    return result
