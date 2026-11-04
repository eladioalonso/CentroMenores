"""Servicios de autenticación sin bloqueo permanente de cuentas."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gestion_centro.auth.models import AccessAudit, Professional, UserAccount


class Role(StrEnum):
    ADMIN = "admin"
    EDUCATOR = "educator"


class AuthStatus(StrEnum):
    SUCCESS = "success"
    INVALID = "invalid"
    INACTIVE = "inactive"
    RETRY_FLOW_CLOSED = "retry_flow_closed"


@dataclass(frozen=True, slots=True)
class AuthResult:
    status: AuthStatus
    account_id: str | None = None
    professional_id: str | None = None
    role: Role | None = None
    remaining_attempts: int = 5


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("La contraseña debe tener al menos 12 caracteres")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$16384$8$1$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt_b64, digest_b64 = encoded.split("$")
        if algorithm != "scrypt":
            return False
        salt = base64.b64decode(salt_b64, validate=True)
        expected = base64.b64decode(digest_b64, validate=True)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_professional_account(
    session: Session, *, display_name: str, username: str, password: str, role: Role
) -> UserAccount:
    name, login = display_name.strip(), username.strip().casefold()
    if not name or not login:
        raise ValueError("El nombre y el usuario son obligatorios")
    if session.scalar(select(UserAccount).where(UserAccount.username == login)):
        raise ValueError("El nombre de usuario ya existe")
    professional = Professional(display_name=name)
    account = UserAccount(
        professional=professional, username=login, password_hash=hash_password(password),
        role=role.value, active=True,
    )
    session.add(account)
    session.flush()
    session.add(AccessAudit(account_id=account.id, username_snapshot=login, event="account_created"))
    return account


def authenticate(session: Session, *, username: str, password: str) -> AuthResult:
    login = username.strip().casefold()
    account = session.scalar(select(UserAccount).where(UserAccount.username == login))
    if account is None:
        session.add(AccessAudit(username_snapshot=login or "(vacío)", event="login_failed"))
        return AuthResult(AuthStatus.INVALID)
    if not account.active or not account.professional.active:
        session.add(AccessAudit(account_id=account.id, username_snapshot=login, event="login_inactive"))
        return AuthResult(AuthStatus.INACTIVE)
    if not verify_password(password, account.password_hash):
        account.failed_attempts += 1
        session.add(AccessAudit(account_id=account.id, username_snapshot=login, event="login_failed"))
        if account.failed_attempts >= 5:
            account.failed_attempts = 0
            return AuthResult(AuthStatus.RETRY_FLOW_CLOSED, remaining_attempts=0)
        return AuthResult(AuthStatus.INVALID, remaining_attempts=5 - account.failed_attempts)
    account.failed_attempts = 0
    account.updated_at = datetime.now(timezone.utc)
    session.add(AccessAudit(account_id=account.id, username_snapshot=login, event="login_success"))
    return AuthResult(
        AuthStatus.SUCCESS, account.id, account.professional_id, Role(account.role), 5
    )


def set_account_active(session: Session, account_id: str, active: bool) -> None:
    account = session.get(UserAccount, account_id)
    if account is None:
        raise ValueError("La cuenta no existe")
    account.active = active
    account.updated_at = datetime.now(timezone.utc)
    session.add(AccessAudit(
        account_id=account.id, username_snapshot=account.username,
        event="account_reactivated" if active else "account_deactivated",
    ))


def admin_reset_password(
    session: Session, *, actor_account_id: str, target_account_id: str, new_password: str
) -> None:
    """Permite al administrador restablecer, pero nunca consultar, una contraseña."""
    actor = session.get(UserAccount, actor_account_id)
    target = session.get(UserAccount, target_account_id)
    if actor is None or not actor.active or actor.role != Role.ADMIN.value:
        raise PermissionError("Se requiere una cuenta administradora activa")
    if target is None:
        raise ValueError("La cuenta indicada no existe")
    target.password_hash = hash_password(new_password)
    target.failed_attempts = 0
    target.updated_at = datetime.now(timezone.utc)
    session.add(AccessAudit(
        account_id=actor.id, username_snapshot=actor.username,
        event="admin_password_reset", details=f"Cuenta restablecida: {target.id}",
    ))


def admin_set_account_active(
    session: Session, *, actor_account_id: str, target_account_id: str, active: bool
) -> None:
    """Activa o desactiva cuentas con control de permisos y protección del último admin."""
    actor = session.get(UserAccount, actor_account_id)
    target = session.get(UserAccount, target_account_id)
    if actor is None or not actor.active or actor.role != Role.ADMIN.value:
        raise PermissionError("Se requiere una cuenta administradora activa")
    if target is None:
        raise ValueError("La cuenta indicada no existe")
    if not active and target.role == Role.ADMIN.value and target.active:
        active_admins = session.scalar(
            select(func.count()).select_from(UserAccount).where(
                UserAccount.role == Role.ADMIN.value, UserAccount.active.is_(True)
            )
        )
        if active_admins <= 1:
            raise ValueError("No se puede desactivar al último administrador activo")
    target.active = active
    target.updated_at = datetime.now(timezone.utc)
    session.add(AccessAudit(
        account_id=actor.id, username_snapshot=actor.username,
        event="admin_account_activated" if active else "admin_account_deactivated",
        details=f"Cuenta afectada: {target.id}",
    ))


def _require_admin(session: Session, actor_account_id: str) -> UserAccount:
    actor = session.get(UserAccount, actor_account_id)
    if actor is None or not actor.active or actor.role != Role.ADMIN.value:
        raise PermissionError("Se requiere una cuenta administradora activa")
    return actor


def admin_create_professional_account(
    session: Session, *, actor_account_id: str, display_name: str,
    username: str, password: str, role: Role,
) -> UserAccount:
    actor = _require_admin(session, actor_account_id)
    account = create_professional_account(
        session, display_name=display_name, username=username, password=password, role=role
    )
    session.add(AccessAudit(
        account_id=actor.id, username_snapshot=actor.username,
        event="admin_account_created", details=f"Cuenta creada: {account.id}; perfil: {role.value}",
    ))
    return account


def admin_change_role(
    session: Session, *, actor_account_id: str, target_account_id: str, role: Role
) -> None:
    actor = _require_admin(session, actor_account_id)
    target = session.get(UserAccount, target_account_id)
    if target is None:
        raise ValueError("La cuenta indicada no existe")
    if target.role == Role.ADMIN.value and role is Role.EDUCATOR:
        active_admins = session.scalar(select(func.count()).select_from(UserAccount).where(
            UserAccount.role == Role.ADMIN.value, UserAccount.active.is_(True)
        ))
        if target.active and active_admins <= 1:
            raise ValueError("No se puede retirar el perfil al último administrador activo")
    target.role = role.value
    target.updated_at = datetime.now(timezone.utc)
    session.add(AccessAudit(
        account_id=actor.id, username_snapshot=actor.username,
        event="admin_role_changed", details=f"Cuenta: {target.id}; nuevo perfil: {role.value}",
    ))



def admin_set_health_access(
    session: Session, *, actor_account_id: str, target_account_id: str, allowed: bool
) -> None:
    """Asigna autorización sanitaria explícita; el rol administrador no la concede por defecto."""
    actor = _require_admin(session, actor_account_id)
    target = session.get(UserAccount, target_account_id)
    if target is None:
        raise ValueError("La cuenta indicada no existe")
    target.health_access = bool(allowed)
    target.updated_at = datetime.now(timezone.utc)
    session.add(AccessAudit(
        account_id=actor.id, username_snapshot=actor.username,
        event="health_access_granted" if allowed else "health_access_revoked",
        details=f"Cuenta afectada: {target.id}",
    ))
