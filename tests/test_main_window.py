"""Pruebas de humo de la navegación principal de escritorio."""

from PySide6.QtWidgets import QApplication, QPushButton

from gestion_centro.app import MainWindow
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
            "Calendario día / semana / mes / año",
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
            "Calendario día / semana / mes / año",
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
