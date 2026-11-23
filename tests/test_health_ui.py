from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gestion_centro.auth.service import Role, create_professional_account
from gestion_centro.care_ui import HealthDialog
from gestion_centro.domain.service import create_minor
from gestion_centro.persistence.base import Base


_APP = None


def _application():
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


def test_health_module_lists_inactive_minors_without_special_health_flag():
    _application()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as session:
        actor = create_professional_account(
            session, display_name="Educadora ficticia", username="health-inactive-ui",
            password="contraseña de prueba segura", role=Role.EDUCATOR,
        )
        minor = create_minor(
            session, actor_account_id=actor.id,
            given_names="Caso histórico", family_names="Ficticio",
        )
        minor.active = False
        actor_id, minor_id = actor.id, minor.id
        session.commit()

    dialog = HealthDialog(factory, actor_id)
    try:
        assert dialog.stay.count() == 2
        assert dialog.stay.itemData(1) == minor_id
        assert dialog.stay.itemText(1).endswith("· Inactivo")
        assert dialog.stay.currentData() is None
    finally:
        dialog.close()
        engine.dispose()



def test_health_dialog_preselects_minor_when_opened_from_workspace_without_active_stay():
    _application()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as session:
        actor = create_professional_account(
            session, display_name="Educador ficticio", username="health-preselect-ui",
            password="contraseña de prueba segura", role=Role.EDUCATOR,
        )
        minor = create_minor(
            session, actor_account_id=actor.id,
            given_names="Caso sin estancia", family_names="Ficticio",
        )
        actor_id, minor_id = actor.id, minor.id
        session.commit()

    dialog = HealthDialog(factory, actor_id, minor_id=minor_id)
    try:
        assert dialog.stay.currentData() == minor_id
    finally:
        dialog.close()
        engine.dispose()
