"""Servicios de autenticación sin bloqueo permanente de cuentas."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import select
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
