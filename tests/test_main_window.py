"""Pruebas de humo de la navegación principal de escritorio."""

from PySide6.QtWidgets import QApplication, QPushButton, QTabWidget

from gestion_centro.app import MainWindow, CredentialsDialog
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from PySide6.QtWidgets import QFrame, QLabel
from gestion_centro.persistence.base import Base
from gestion_centro.auth.models import Professional, UserAccount
from gestion_centro.domain.models import Minor, Stay
from gestion_centro.domain.documents import Outing, OutingStay
from gestion_centro.auth.service import Role


# Mantener viva la envoltura Python de QApplication durante toda la suite.
# Si solo se conserva la instancia C++ de Qt, su destrucción al finalizar
# puede provocar una salida anómala del intérprete en Windows.
_APP: QApplication | None = None


def _application() -> QApplication:
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


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
            "Inicio", "Parte diario", "Menores", "Documentación", "Calendario",
            "Expedientes", "Seguimiento educativo", "Ficha sanitaria y medicación",
            "Salidas", "Autorizaciones", "Documentos de menores", "Informes externos",
            "Calendario y agenda común", "Organizar tareas",
        }
        assert expected <= labels
        assert "Administración" not in labels
        assert "Administrar cuentas" not in labels
        assert "Copias de seguridad" not in labels
    finally:
        window.close()

def test_administrator_sees_ordinary_and_administration_modules():
    window = _window(Role.ADMIN)
    try:
        labels = _button_labels(window)
        expected = {
            "Inicio", "Parte diario", "Menores", "Documentación", "Calendario",
            "Administración", "Expedientes", "Seguimiento educativo",
            "Ficha sanitaria y medicación", "Salidas", "Autorizaciones",
            "Documentos de menores", "Informes externos", "Calendario y agenda común",
            "Organizar tareas", "Administrar cuentas", "Copias de seguridad",
            "Mantenimiento y diagnóstico", "Estadísticas y memoria",
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
            "Inicio", "Parte diario", "Menores", "Documentación", "Calendario"
        ]
        nav = [button.text() for button in window.findChildren(QPushButton, "navigationButton")]
        assert nav == ["Inicio", "Parte diario", "Menores", "Documentación", "Calendario"]
        assert not tabs.tabBar().isVisible()
    finally:
        window.close()

def test_administration_is_separate_tab_only_for_admin():
    educator = _window(Role.EDUCATOR)
    admin = _window(Role.ADMIN)
    try:
        assert educator.findChild(QTabWidget).count() == 5
        assert admin.findChild(QTabWidget).count() == 6
        assert admin.findChild(QTabWidget).tabText(5) == "Administración"
        assert len(admin.findChild(QTabWidget).widget(5).findChildren(QPushButton)) == 4
    finally:
        educator.close()
        admin.close()

def test_first_admin_setup_ignores_preseeded_demo_accounts():
    _application()
    dialog = CredentialsDialog(
        first_admin=True,
        available_accounts=[("educador", "educador")],
    )
    try:
        dialog.show()
        assert dialog.account_selector.count() == 0
        assert not dialog.username.isReadOnly()
        assert dialog.name.isVisible()
    finally:
        dialog.close()


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


def test_dashboard_counts_residents_outside_and_overdue_returns():
    _application()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)
    with factory() as session:
        professional = Professional(display_name="Educador ficticio")
        session.add(professional)
        session.flush()
        account = UserAccount(
            professional_id=professional.id, username="dashboard-test",
            password_hash="hash-ficticio", role="educator",
        )
        session.add(account)
        session.flush()
        stays = []
        for index in range(2):
            minor = Minor(
                given_names=f"Caso {index}", family_names="Ficticio",
            )
            session.add(minor)
            session.flush()
            stay = Stay(
                minor_id=minor.id, sequence_number=1,
                started_on=date.today(), status="active",
            )
            session.add(stay)
            session.flush()
            stays.append(stay)
        outing = Outing(
            kind="family", destination="Destino ficticio", purpose="Prueba",
            planned_departure=now - timedelta(hours=2),
            planned_return=now - timedelta(hours=1),
            actual_departure=now - timedelta(hours=2),
            responsible_account_id=account.id, status="in_progress",
            restrictions_checked=True, created_by_account_id=account.id,
            created_by_name_snapshot="Educador ficticio",
        )
        session.add(outing)
        session.flush()
        session.add(OutingStay(outing_id=outing.id, stay_id=stays[0].id))
        session.flush()
        account_id = account.id
        session.commit()

    window = MainWindow(
        "Educador ficticio", Role.EDUCATOR,
        factory=factory, account_id=account_id, paths=object(),
    )
    try:
        cards = {}
        for frame in window.findChildren(QFrame):
            if frame.objectName() != "dashboardCard":
                continue
            title = frame.findChild(QLabel, "dashboardCardTitle")
            value = frame.findChild(QLabel, "dashboardCardValue")
            if title is not None and value is not None:
                cards[title.text()] = value.text()
        assert cards["Menores presentes"] == "1"
        assert cards["Menores fuera del centro"] == "1"
        assert cards["Retornos atrasados"] == "1"
    finally:
        window.close()
        engine.dispose()
