"""Pruebas de humo de la navegación principal de escritorio."""

from PySide6.QtWidgets import QApplication, QPushButton, QTabWidget

from gestion_centro.app import MainWindow, CredentialsDialog
from gestion_centro.auth.service import Role


def _application() -> QApplication:
    app = QApplication.instance()
    return app if app is not None else QApplication([])


def _window(role: Role) -> MainWindow:
    _application()
    # Los objetos de infraestructura no se usan hasta que se abre cada diálogo.
    return MainWindow(
        "Profesional de prueba",
        role,
        factory=object(),
        account_id="account-test",
        paths=object(),
    )


def _button_labels(window: MainWindow) -> set[str]:
    return {button.text() for button in window.findChildren(QPushButton)}


def test_educator_sees_all_ordinary_modules():
    window = _window(Role.EDUCATOR)
    try:
        labels = _button_labels(window)
        expected = {
            "Ayuda y preguntas frecuentes",
            "Expedientes y estancias",
            "Diario e incidencias",
            "Agenda común y tareas",
            "Calendario",
            "Documentación personal",
            "Autorizaciones",
            "Salidas",
            "Seguimiento educativo y escolaridad",
            "Ficha sanitaria y medicación",
            "Comunicaciones internas",
            "Informes externos",
        }
        assert expected <= labels
        assert "Administrar cuentas" not in labels
        assert "Copias de seguridad" not in labels
        assert "Mantenimiento y diagnóstico" not in labels
        assert "Estadísticas y memoria" not in labels
    finally:
        window.close()


def test_administrator_sees_ordinary_and_administration_modules():
    window = _window(Role.ADMIN)
    try:
        labels = _button_labels(window)
        expected = {
            "Ayuda y preguntas frecuentes",
            "Administrar cuentas",
            "Copias de seguridad",
            "Mantenimiento y diagnóstico",
            "Estadísticas y memoria",
            "Expedientes y estancias",
            "Diario e incidencias",
            "Agenda común y tareas",
            "Calendario",
            "Documentación personal",
            "Autorizaciones",
            "Salidas",
            "Seguimiento educativo y escolaridad",
            "Ficha sanitaria y medicación",
            "Comunicaciones internas",
            "Informes externos",
        }
        assert expected <= labels
    finally:
        window.close()


def test_navigation_is_grouped_by_daily_work_and_secondary_functions():
    window = _window(Role.EDUCATOR)
    try:
        tabs = window.findChild(QTabWidget)
        assert tabs is not None
        assert [tabs.tabText(i) for i in range(tabs.count())] == [
            "Día a día", "Gestión y consultas"
        ]
        assert tabs.widget(0).findChildren(QPushButton)
        assert len(tabs.widget(0).findChildren(QPushButton)) == 4
        assert len(tabs.widget(1).findChildren(QPushButton)) == 7
    finally:
        window.close()


def test_administration_is_separate_tab_only_for_admin():
    educator = _window(Role.EDUCATOR)
    admin = _window(Role.ADMIN)
    try:
        assert educator.findChild(QTabWidget).count() == 2
        assert admin.findChild(QTabWidget).tabText(2) == "Administración"
        assert len(admin.findChild(QTabWidget).widget(2).findChildren(QPushButton)) == 4
    finally:
        educator.close()
        admin.close()



def test_login_account_selector_fills_username_and_requires_password():
    app = _application()
    dialog = CredentialsDialog(
        available_accounts=[("Ana Educadora", "ana"), ("Luis Educador", "luis")]
    )
    try:
        assert dialog.account_selector.count() == 2
        assert dialog.username.text() == "ana"
        assert dialog.username.isReadOnly()
        dialog.account_selector.setCurrentIndex(1)
        assert dialog.username.text() == "luis"
        assert dialog.password.text() == ""
    finally:
        dialog.close()


def test_main_window_exposes_logout_action():
    window = _window(Role.EDUCATOR)
    try:
        logout = next(button for button in window.findChildren(QPushButton)
                      if button.text() == "Cerrar sesión")
        logout.click()
        assert window.logout_requested is True
    finally:
        window.close()
