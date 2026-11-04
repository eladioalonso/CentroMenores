from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import pytest

from gestion_centro.auth.service import (
    Role, admin_reset_password, admin_set_account_active, authenticate,
    create_professional_account, verify_password, admin_set_health_access,
    change_own_password,
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


def test_admin_can_create_account_and_change_role():
    from gestion_centro.auth.service import admin_create_professional_account, admin_change_role

    with session_for_test() as session:
        admin = create_professional_account(session, display_name="Admin", username="admin", password="contraseña inicial segura", role=Role.ADMIN)
        session.flush()
        target = admin_create_professional_account(session, actor_account_id=admin.id,
            display_name="Nuevo profesional", username="nuevo",
            password="contraseña nueva segura", role=Role.EDUCATOR)
        admin_change_role(session, actor_account_id=admin.id,
            target_account_id=target.id, role=Role.ADMIN)
        assert target.role == Role.ADMIN.value


def test_non_admin_cannot_create_account_or_reset_password():
    from gestion_centro.auth.service import admin_create_professional_account

    with session_for_test() as session:
        educator = create_professional_account(session, display_name="Educador", username="educador", password="contraseña educador segura", role=Role.EDUCATOR)
        session.flush()
        with pytest.raises(PermissionError):
            admin_create_professional_account(session, actor_account_id=educator.id,
                display_name="Intruso", username="intruso",
                password="contraseña intruso segura", role=Role.ADMIN)
        with pytest.raises(PermissionError):
            admin_reset_password(session, actor_account_id=educator.id,
                target_account_id=educator.id, new_password="contraseña restablecida")


def test_health_access_is_explicit_audited_and_independent_of_admin_role():
    from gestion_centro.auth.models import AccessAudit
    with session_for_test() as session:
        admin = create_professional_account(session, display_name="Admin", username="admin",
            password="contraseña inicial segura", role=Role.ADMIN)
        educator = create_professional_account(session, display_name="Educador", username="educador",
            password="contraseña educador segura", role=Role.EDUCATOR)
        session.flush()
        assert admin.health_access is False
        assert educator.health_access is False
        admin_set_health_access(session, actor_account_id=admin.id,
            target_account_id=educator.id, allowed=True)
        assert educator.health_access is True
        admin_set_health_access(session, actor_account_id=admin.id,
            target_account_id=educator.id, allowed=False)
        assert educator.health_access is False
        events = [item.event for item in session.query(AccessAudit).all()]
        assert "health_access_granted" in events
        assert "health_access_revoked" in events


def test_non_admin_cannot_grant_health_access():
    with session_for_test() as session:
        educator = create_professional_account(session, display_name="Educador", username="educador",
            password="contraseña educador segura", role=Role.EDUCATOR)
        target = create_professional_account(session, display_name="Otro", username="otro",
            password="contraseña otro segura", role=Role.EDUCATOR)
        session.flush()
        with pytest.raises(PermissionError):
            admin_set_health_access(session, actor_account_id=educator.id,
                target_account_id=target.id, allowed=True)
        assert target.health_access is False


def test_professional_can_change_own_password_and_audit_it():
    from gestion_centro.auth.models import AccessAudit
    with session_for_test() as session:
        account = create_professional_account(
            session, display_name="Profesional", username="profesional",
            password="contraseña anterior segura", role=Role.EDUCATOR,
        )
        session.flush()
        change_own_password(
            session, account_id=account.id,
            current_password="contraseña anterior segura",
            new_password="contraseña nueva segura 2026",
        )
        assert verify_password("contraseña nueva segura 2026", account.password_hash)
        assert not verify_password("contraseña anterior segura", account.password_hash)
        assert session.query(AccessAudit).filter_by(
            event="password_changed_by_user"
        ).count() == 1


def test_professional_cannot_change_password_with_wrong_current_password():
    with session_for_test() as session:
        account = create_professional_account(
            session, display_name="Profesional", username="profesional",
            password="contraseña anterior segura", role=Role.EDUCATOR,
        )
        session.flush()
        with pytest.raises(ValueError, match="actual"):
            change_own_password(
                session, account_id=account.id,
                current_password="incorrecta",
                new_password="contraseña nueva segura 2026",
            )
        assert verify_password("contraseña anterior segura", account.password_hash)
