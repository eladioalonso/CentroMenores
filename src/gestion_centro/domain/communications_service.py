"""Casos de uso de comunicaciones compartidas."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from gestion_centro.auth.models import AccessAudit, UserAccount
from gestion_centro.domain.communications import Communication, CommunicationContribution

def _actor(session: Session, account_id: str) -> UserAccount:
    actor = session.get(UserAccount, account_id)
    if actor is None or not actor.active or not actor.professional.active:
        raise PermissionError("La cuenta no está activa")
    return actor

def _audit(session: Session, actor: UserAccount, event: str, details: str) -> None:
    session.add(AccessAudit(account_id=actor.id, username_snapshot=actor.username, event=event, details=details))

def create_communication(session: Session, *, actor_account_id: str, title: str, content: str):
    actor = _actor(session, actor_account_id)
    if not title.strip() or not content.strip():
        raise ValueError("El título y la primera aportación son obligatorios")
    item = Communication(title=title.strip(), created_by_account_id=actor.id,
        created_by_name_snapshot=actor.professional.display_name)
    session.add(item)
    session.flush()
    session.add(CommunicationContribution(communication_id=item.id, author_account_id=actor.id,
        author_name_snapshot=actor.professional.display_name, content=content.strip()))
    _audit(session, actor, "communication_created", item.id)
    return item

def add_communication_contribution(session: Session, *, actor_account_id: str, communication_id: str, content: str):
    actor = _actor(session, actor_account_id)
    item = session.get(Communication, communication_id)
    if item is None or item.deleted_at is not None:
        raise ValueError("La comunicación no existe o está en papelera")
    if item.status != "draft":
        raise ValueError("La comunicación está cerrada")
    if not content.strip():
        raise ValueError("La aportación no puede estar vacía")
    contribution = CommunicationContribution(communication_id=item.id, author_account_id=actor.id,
        author_name_snapshot=actor.professional.display_name, content=content.strip())
    item.updated_at = datetime.now(timezone.utc)
    session.add(contribution)
    _audit(session, actor, "communication_contribution_added", item.id)
    return contribution

def close_communication(session: Session, *, actor_account_id: str, communication_id: str, reason: str):
    actor = _actor(session, actor_account_id)
    item = session.get(Communication, communication_id)
    if item is None or item.deleted_at is not None or item.status != "draft":
        raise ValueError("La comunicación no existe o no está abierta")
    if not reason.strip():
        raise ValueError("El cierre requiere un motivo")
    item.status, item.closed_at, item.closed_by_account_id = "closed", datetime.now(timezone.utc), actor.id
    item.updated_at = item.closed_at
    _audit(session, actor, "communication_closed", f"{item.id}: {reason.strip()}")
    return item

def reopen_communication(session: Session, *, actor_account_id: str, communication_id: str, reason: str):
    actor = _actor(session, actor_account_id)
    if actor.role != "admin":
        raise PermissionError("Solo administración puede reabrir una comunicación")
    item = session.get(Communication, communication_id)
    if item is None or item.deleted_at is not None or item.status != "closed":
        raise ValueError("La comunicación no existe o no está cerrada")
    if not reason.strip():
        raise ValueError("La reapertura requiere un motivo")
    item.status, item.closed_at, item.closed_by_account_id = "draft", None, None
    item.updated_at = datetime.now(timezone.utc)
    _audit(session, actor, "communication_reopened", f"{item.id}: {reason.strip()}")
    return item

def move_communication_to_trash(session: Session, *, actor_account_id: str, communication_id: str):
    actor = _actor(session, actor_account_id)
    item = session.get(Communication, communication_id)
    if item is None or item.deleted_at is not None:
        raise ValueError("La comunicación no existe o ya está en papelera")
    if actor.role != "admin" and item.created_by_account_id != actor.id:
        raise PermissionError("Solo puedes enviar a papelera tus propias comunicaciones")
    item.deleted_at, item.deleted_by_account_id = datetime.now(timezone.utc), actor.id
    _audit(session, actor, "communication_trashed", item.id)
    return item

def restore_communication(session: Session, *, actor_account_id: str, communication_id: str):
    actor = _actor(session, actor_account_id)
    if actor.role != "admin":
        raise PermissionError("Solo administración puede recuperar comunicaciones")
    item = session.get(Communication, communication_id)
    if item is None or item.deleted_at is None:
        raise ValueError("La comunicación no está en papelera")
    if item.deleted_at < datetime.now(timezone.utc) - timedelta(days=60):
        raise ValueError("El plazo de recuperación de 2 meses ha vencido")
    item.deleted_at, item.deleted_by_account_id = None, None
    item.updated_at = datetime.now(timezone.utc)
    _audit(session, actor, "communication_restored", item.id)
    return item

def list_communications(session: Session, *, actor_account_id: str,
                        include_trash: bool = False, include_closed: bool = True):
    actor = _actor(session, actor_account_id)
    statement = select(Communication).order_by(Communication.updated_at.desc())
    if not include_trash:
        statement = statement.where(Communication.deleted_at.is_(None))
    if not include_closed:
        statement = statement.where(Communication.status == "draft")
    _audit(session, actor, "communications_accessed",
           f"papelera:{include_trash}; cerradas:{include_closed}")
    return session.scalars(statement).all()


def list_communication_contributions(session: Session, *, actor_account_id: str,
                                     communication_id: str):
    actor = _actor(session, actor_account_id)
    item = session.get(Communication, communication_id)
    if item is None or item.deleted_at is not None:
        raise ValueError("La comunicación no existe o está en papelera")
    _audit(session, actor, "communication_history_accessed", communication_id)
    return session.scalars(select(CommunicationContribution).where(
        CommunicationContribution.communication_id == communication_id
    ).order_by(CommunicationContribution.created_at)).all()


def stale_communications(session: Session, *, actor_account_id: str,
                         now: datetime | None = None):
    actor = _actor(session, actor_account_id)
    moment = now or datetime.now(timezone.utc)
    _audit(session, actor, "stale_communications_accessed", "borradores de más de 7 días")
    return session.scalars(select(Communication).where(
        Communication.status == "draft", Communication.deleted_at.is_(None),
        Communication.updated_at <= moment - timedelta(days=7)
    ).order_by(Communication.updated_at)).all()


def revise_communication_contribution(session: Session, *, actor_account_id: str,
                                      contribution_id: str, corrected_content: str):
    """Añade una rectificación vinculada; nunca sobrescribe una aportación compartida."""
    actor = _actor(session, actor_account_id)
    original = session.get(CommunicationContribution, contribution_id)
    if original is None:
        raise ValueError("La aportación original no existe")
    if original.author_account_id != actor.id:
        raise PermissionError("Solo puedes rectificar tus propias aportaciones")
    item = session.get(Communication, original.communication_id)
    if item is None or item.deleted_at is not None or item.status != "draft":
        raise ValueError("La comunicación está cerrada o no disponible")
    if not corrected_content.strip():
        raise ValueError("La rectificación no puede estar vacía")
    correction = CommunicationContribution(
        communication_id=item.id, author_account_id=actor.id,
        author_name_snapshot=actor.professional.display_name,
        content=f"RECTIFICACIÓN de la aportación {original.id}: {corrected_content.strip()}",
    )
    item.updated_at = datetime.now(timezone.utc)
    session.add(correction)
    _audit(session, actor, "communication_contribution_revised",
           f"Original:{original.id}; rectificación:{correction.id}")
    return correction
