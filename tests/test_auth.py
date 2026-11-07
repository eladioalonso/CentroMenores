from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from gestion_centro.auth.models import AccessAudit, Professional, UserAccount
from gestion_centro.auth.service import (
    AuthStatus, Role, authenticate, create_professional_account, hash_password, verify_password,
    admin_set_account_active, admin_change_role, admin_set_health_access,
    admin_reset_password, list_audit_events,
)
from gestion_centro.persistence.base import Base


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_password_hash_is_salted_and_verified():
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")
    assert first != second
    assert verify_password("correct horse battery staple", first)
    assert not verify_password("incorrect password", first)


def test_account_creation_and_successful_login():
    with make_session() as session:
        account = create_professional_account(
            session, display_name="Profesional ficticio", username="Educador1",
            password="contraseña segura 2026", role=Role.EDUCATOR,
        )
        session.commit()
        result = authenticate(session, username="educador1", password="contraseña segura 2026")
        assert result.status is AuthStatus.SUCCESS
        assert result.account_id == account.id
        assert result.role is Role.EDUCATOR
        session.commit()


def test_five_failed_attempts_close_flow_without_locking_account():
    with make_session() as session:
        account = create_professional_account(
            session, display_name="Admin ficticio", username="admin",
            password="contraseña segura 2026", role=Role.ADMIN,
        )
        session.commit()
        for _ in range(4):
            result = authenticate(session, username="admin", password="incorrecta")
            assert result.status is AuthStatus.INVALID
        result = authenticate(session, username="admin", password="incorrecta")
        assert result.status is AuthStatus.RETRY_FLOW_CLOSED
        assert account.active is True
        assert account.failed_attempts == 0
        assert authenticate(session, username="admin", password="contraseña segura 2026").status is AuthStatus.SUCCESS


def test_deactivated_account_keeps_professional_and_audit_history():
    with make_session() as session:
        account = create_professional_account(
            session, display_name="Educador", username="educador",
            password="contraseña segura 2026", role=Role.EDUCATOR,
        )
        session.commit()
        professional_id, account_id = account.professional_id, account.id
        account.active = False
        session.commit()
        assert session.get(Professional, professional_id) is not None
        assert session.get(UserAccount, account_id) is not None
        assert authenticate(session, username="educador", password="contraseña segura 2026").status is AuthStatus.INACTIVE
        assert session.scalar(select(AccessAudit).where(AccessAudit.event == "login_inactive")) is not None

def test_admin_operations_reject_inactive_professional_even_if_account_is_active():
    import pytest

    with make_session() as session:
        admin = create_professional_account(
            session, display_name="Admin ficticio", username="admin-inactive-prof",
            password="contraseña segura 2026", role=Role.ADMIN,
        )
        target = create_professional_account(
            session, display_name="Educador ficticio", username="target-inactive-prof",
            password="contraseña segura 2026", role=Role.EDUCATOR,
        )
        admin.professional.active = False
        assert admin.active is True
        with pytest.raises(PermissionError, match="profesional activos"):
            admin_set_account_active(
                session, actor_account_id=admin.id, target_account_id=target.id, active=False)
        with pytest.raises(PermissionError, match="profesional activos"):
            admin_change_role(
                session, actor_account_id=admin.id, target_account_id=target.id, role=Role.ADMIN)
        with pytest.raises(PermissionError, match="profesional activos"):
            admin_set_health_access(
                session, actor_account_id=admin.id, target_account_id=target.id, allowed=True)
        with pytest.raises(PermissionError, match="profesional activos"):
            admin_reset_password(
                session, actor_account_id=admin.id, target_account_id=target.id,
                new_password="otra contraseña segura 2026")
        with pytest.raises(PermissionError, match="profesional activos"):
            list_audit_events(session, actor_account_id=admin.id)


def test_last_usable_admin_cannot_be_disabled_or_demoted_if_other_admin_professional_is_inactive():
    import pytest

    with make_session() as session:
        first = create_professional_account(
            session, display_name="Admin uno", username="admin-one",
            password="contraseña segura 2026", role=Role.ADMIN,
        )
        second = create_professional_account(
            session, display_name="Admin dos", username="admin-two",
            password="contraseña segura 2026", role=Role.ADMIN,
        )
        second.professional.active = False
        with pytest.raises(ValueError, match="último administrador activo"):
            admin_set_account_active(
                session, actor_account_id=first.id, target_account_id=first.id, active=False)
        with pytest.raises(ValueError, match="último administrador activo"):
            admin_change_role(
                session, actor_account_id=first.id, target_account_id=first.id, role=Role.EDUCATOR)

