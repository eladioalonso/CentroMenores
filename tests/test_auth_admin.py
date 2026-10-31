from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import pytest

from gestion_centro.auth.service import (
    Role, admin_reset_password, admin_set_account_active, authenticate,
    create_professional_account, verify_password,
)
from gestion_centro.auth.models import UserAccount
from gestion_centro.persistence.base import Base


def session_for_test():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_admin_can_reset_password_without_reading_old_password():
    with session_for_test() as session:
        admin = create_professional_account(session, display_name="Admin", username="admin", password="contraseña inicial segura", role=Role.ADMIN)
        educator = create_professional_account(session, display_name="Educador", username="educador", password="contraseña educador segura", role=Role.EDUCATOR)
        session.flush()
        admin_reset_password(session, actor_account_id=admin.id, target_account_id=educator.id, new_password="nueva contraseña segura 2026")
        assert verify_password("nueva contraseña segura 2026", educator.password_hash)
        assert authenticate(session, username="educador", password="nueva contraseña segura 2026").account_id == educator.id


def test_non_admin_cannot_manage_accounts():
    with session_for_test() as session:
        educator = create_professional_account(session, display_name="Educador", username="educador", password="contraseña educador segura", role=Role.EDUCATOR)
        target = create_professional_account(session, display_name="Otro", username="otro", password="contraseña otro segura", role=Role.EDUCATOR)
        session.flush()
        with pytest.raises(PermissionError):
            admin_set_account_active(session, actor_account_id=educator.id, target_account_id=target.id, active=False)


def test_last_active_admin_cannot_be_deactivated():
    with session_for_test() as session:
        admin = create_professional_account(session, display_name="Admin", username="admin", password="contraseña inicial segura", role=Role.ADMIN)
        session.flush()
        with pytest.raises(ValueError, match="último administrador"):
            admin_set_account_active(session, actor_account_id=admin.id, target_account_id=admin.id, active=False)
        assert session.get(UserAccount, admin.id).active is True
