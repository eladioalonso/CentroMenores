"""Servicios de documentación, autorizaciones y salidas."""
from datetime import date, datetime, timezone
from pathlib import PurePosixPath
from sqlalchemy import select
from sqlalchemy.orm import Session
from gestion_centro.auth.models import AccessAudit, UserAccount
from gestion_centro.domain.models import Stay
from gestion_centro.domain.documents import PersonalDocument, Authorization, Outing, OutingStay, OutingAuthorization

DOCUMENT_CATEGORIES = {"identity", "health", "administrative", "education", "family", "other"}
AUTHORIZATION_TYPES = {"general", "family_visit", "outing", "activity", "medical", "image", "travel", "other"}
OUTING_KINDS = {"family", "activity", "school", "health", "administrative", "other"}
OUTING_STATUSES = {"planned", "in_progress", "returned", "cancelled"}


def _actor(session: Session, account_id: str, *, health: bool = False) -> UserAccount:
    actor = session.get(UserAccount, account_id)
    if actor is None or not actor.active or not actor.professional.active:
        raise PermissionError("Se requiere una cuenta y un profesional activos")
    if health and not actor.health_access:
        raise PermissionError("La cuenta no tiene autorización para gestionar documentos sanitarios")
    return actor


def _audit(session: Session, actor: UserAccount, event: str, details: str):
    session.add(AccessAudit(account_id=actor.id, username_snapshot=actor.username, event=event, details=details))


def _active_stays(session: Session, stay_ids: list[str]) -> list[Stay]:
    if not stay_ids or len(stay_ids) != len(set(stay_ids)):
        raise ValueError("Selecciona al menos una estancia y no repitas ninguna")
    stays = [session.get(Stay, item) for item in stay_ids]
    if any(s is None or s.status != "active" for s in stays):
        raise ValueError("Todas las estancias deben existir y estar activas")
    return stays


def register_document(session: Session, *, actor_account_id: str, stay_id: str, category: str,
                      title: str, original_filename: str, relative_path: str, mime_type: str,
                      size_bytes: int, sha256: str, document_date: date | None = None,
                      expires_on: date | None = None, notes: str | None = None,
                      supersedes_id: str | None = None):
    actor = _actor(session, actor_account_id, health=(category == "health"))
    stay = session.get(Stay, stay_id)
    if stay is None or stay.status != "active":
        raise ValueError("La estancia no existe o está cerrada")
    if category not in DOCUMENT_CATEGORIES or not title.strip():
        raise ValueError("Categoría o título documental no válido")
    if not original_filename.strip() or not mime_type.strip() or size_bytes <= 0 or size_bytes > 25 * 1024 * 1024:
        raise ValueError("El archivo debe tener tamaño válido y no superar 25 MB")
    allowed_mimes = {"application/pdf", "image/jpeg", "image/png", "image/webp", "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    if mime_type not in allowed_mimes:
        raise ValueError("Tipo de archivo no permitido")
    if len(sha256) != 64 or any(ch not in "0123456789abcdef" for ch in sha256.lower()):
        raise ValueError("El hash SHA-256 no es válido")
    path = PurePosixPath(relative_path)
    if path.is_absolute() or ".." in path.parts or "\\" in relative_path or ":" in relative_path or not relative_path.strip():
        raise ValueError("La ruta documental debe ser relativa y segura")
    if expires_on and document_date and expires_on < document_date:
        raise ValueError("La caducidad no puede preceder a la fecha del documento")
    version = 1
    if supersedes_id:
        previous = session.get(PersonalDocument, supersedes_id)
        if previous is None or previous.stay_id != stay_id or previous.category != category:
            raise ValueError("La versión anterior no corresponde a este documento")
        if session.scalar(select(PersonalDocument.id).where(PersonalDocument.supersedes_id == previous.id)):
            raise ValueError("La versión seleccionada ya tiene una versión posterior")
        version = previous.version + 1
    doc = PersonalDocument(stay_id=stay.id, category=category, title=title.strip(),
        original_filename=original_filename.strip(), relative_path=relative_path,
        mime_type=mime_type.strip(), size_bytes=size_bytes, sha256=sha256.lower(),
        document_date=document_date, expires_on=expires_on, version=version,
        supersedes_id=supersedes_id, notes=notes.strip() if notes else None,
        uploaded_by_account_id=actor.id, uploaded_by_name_snapshot=actor.professional.display_name)
    session.add(doc); session.flush()
    _audit(session, actor, "personal_document_registered", f"{doc.id}; estancia:{stay.id}")
    return doc


def list_documents(session: Session, *, actor_account_id: str, stay_id: str):
    actor = _actor(session, actor_account_id)
    if session.get(Stay, stay_id) is None:
        raise ValueError("La estancia no existe")
    _audit(session, actor, "personal_documents_accessed", stay_id)
    query = select(PersonalDocument).where(PersonalDocument.stay_id == stay_id)
    if not actor.health_access:
        query = query.where(PersonalDocument.category != "health")
    return session.scalars(query.order_by(PersonalDocument.created_at.desc())).all()



def list_active_stays(session: Session, *, actor_account_id: str):
    actor = _actor(session, actor_account_id)
    _audit(session, actor, "active_stays_accessed", "Selector de estancias")
    return session.scalars(
        select(Stay).where(Stay.status == "active").order_by(Stay.started_on.desc())
    ).all()


def list_authorizations(session: Session, *, actor_account_id: str, stay_id: str):
    actor = _actor(session, actor_account_id)
    if session.get(Stay, stay_id) is None:
        raise ValueError("La estancia no existe")
    query = select(Authorization).where(Authorization.stay_id == stay_id)
    if not actor.health_access:
        query = query.where(Authorization.authorization_type != "medical")
    _audit(session, actor, "authorizations_accessed", f"Estancia: {stay_id}")
    return session.scalars(query.order_by(Authorization.valid_from.desc())).all()


def list_valid_authorizations(session: Session, *, actor_account_id: str, stay_id: str,
                              on_date: date | None = None):
    actor = _actor(session, actor_account_id)
    if session.get(Stay, stay_id) is None:
        raise ValueError("La estancia no existe")
    day = on_date or date.today()
    query = select(Authorization).where(
        Authorization.stay_id == stay_id, Authorization.status == "valid",
        Authorization.valid_from <= day,
    ).where((Authorization.valid_until.is_(None)) | (Authorization.valid_until >= day))
    if not actor.health_access:
        query = query.where(Authorization.authorization_type != "medical")
    _audit(session, actor, "valid_authorizations_accessed", f"Estancia: {stay_id}; fecha: {day.isoformat()}")
    return session.scalars(query.order_by(Authorization.valid_from.desc())).all()


def list_outings(session: Session, *, actor_account_id: str, stay_id: str):
    actor = _actor(session, actor_account_id)
    if session.get(Stay, stay_id) is None:
        raise ValueError("La estancia no existe")
    query = (select(Outing).join(OutingStay, Outing.id == OutingStay.outing_id)
             .where(OutingStay.stay_id == stay_id))
    if not actor.health_access:
        query = query.where(Outing.kind != "health")
    _audit(session, actor, "outings_accessed", f"Estancia: {stay_id}")
    return session.scalars(query.order_by(Outing.planned_departure.desc())).all()

def record_authorization(session: Session, *, actor_account_id: str, stay_id: str,
                         authorization_type: str, scope: str, issuer: str,
                         valid_from: date, valid_until: date | None = None,
                         conditions: str | None = None, document_id: str | None = None):
    actor = _actor(session, actor_account_id, health=(authorization_type == "medical"))
    stay = session.get(Stay, stay_id)
    if stay is None or stay.status != "active":
        raise ValueError("La estancia no existe o está cerrada")
    if authorization_type not in AUTHORIZATION_TYPES or not scope.strip() or not issuer.strip():
        raise ValueError("Tipo, alcance y emisor son obligatorios")
    if valid_until and valid_until < valid_from:
        raise ValueError("La vigencia final precede al inicio")
    if document_id:
        doc = session.get(PersonalDocument, document_id)
        if doc is None or doc.stay_id != stay_id:
            raise ValueError("El documento justificativo no corresponde a esta estancia")
        if doc.category == "health" and not actor.health_access:
            raise PermissionError("La cuenta no tiene autorización para consultar documentos sanitarios")
    item = Authorization(stay_id=stay_id, authorization_type=authorization_type,
        scope=scope.strip(), issuer=issuer.strip(), valid_from=valid_from, valid_until=valid_until,
        conditions=conditions.strip() if conditions else None, status="valid",
        document_id=document_id, recorded_by_account_id=actor.id,
        recorded_by_name_snapshot=actor.professional.display_name)
    session.add(item); session.flush()
    _audit(session, actor, "authorization_recorded", item.id)
    return item


def check_authorization(session: Session, *, actor_account_id: str, stay_id: str,
                        authorization_type: str, on_date: date, required_scope: str | None = None):
    actor = _actor(session, actor_account_id, health=(authorization_type == "medical"))
    matches = session.scalars(select(Authorization).where(
        Authorization.stay_id == stay_id, Authorization.authorization_type == authorization_type,
        Authorization.status == "valid", Authorization.valid_from <= on_date)).all()
    valid = [a for a in matches if a.valid_until is None or a.valid_until >= on_date]
    if required_scope:
        valid = [a for a in valid if required_scope.casefold() in a.scope.casefold()]
    _audit(session, actor, "authorization_checked", f"{stay_id}:{authorization_type}:{on_date.isoformat()}")
    return valid


def set_authorization_status(session: Session, *, actor_account_id: str, authorization_id: str,
                             status: str, reason: str):
    authorization = session.get(Authorization, authorization_id)
    actor = _actor(session, actor_account_id,
        health=bool(authorization and authorization.authorization_type == "medical"))
    if authorization is None or status not in {"valid", "revoked", "expired"}:
        raise ValueError("Autorización o estado no válido")
    if not reason.strip():
        raise ValueError("Todo cambio de estado requiere un motivo")
    authorization.status = status
    _audit(session, actor, "authorization_status_changed",
           f"{authorization.id}:{status}:{reason.strip()}")
    return authorization


def create_outing(session: Session, *, actor_account_id: str, kind: str, destination: str,
                  purpose: str, planned_departure: datetime, planned_return: datetime,
                  responsible_account_id: str, stay_ids: list[str],
                  authorization_ids: list[str] | None = None, restrictions_checked: bool = False):
    actor = _actor(session, actor_account_id, health=(kind == "health"))
    responsible = _actor(session, responsible_account_id)
    if kind not in OUTING_KINDS or not destination.strip() or not purpose.strip():
        raise ValueError("Tipo, destino y finalidad son obligatorios")
    if planned_return <= planned_departure:
        raise ValueError("La vuelta prevista debe ser posterior a la salida")
    if not restrictions_checked:
        raise ValueError("Debes confirmar la revisión de restricciones individuales")
    stays = _active_stays(session, stay_ids)
    auth_ids = authorization_ids or []
    if len(auth_ids) != len(set(auth_ids)):
        raise ValueError("Hay autorizaciones duplicadas")
    auths = [session.get(Authorization, item) for item in auth_ids]
    stay_set = {s.id for s in stays}
    outing_date = planned_departure.date()
    if any(a is None or a.stay_id not in stay_set or a.status != "valid"
           or a.valid_from > outing_date or (a.valid_until is not None and a.valid_until < outing_date)
           for a in auths):
        raise ValueError("Una autorización no es válida o está fuera de vigencia")
    required_type = {"family": "family_visit", "activity": "activity", "health": "medical",
                     "school": "general", "administrative": "general"}.get(kind)
    if required_type:
        authorized_stays = {a.stay_id for a in auths if a.authorization_type in {required_type, "general"}}
        if not stay_set.issubset(authorized_stays):
            raise ValueError("Falta autorización vigente para una o varias estancias")
    outing = Outing(kind=kind, destination=destination.strip(), purpose=purpose.strip(),
        planned_departure=planned_departure, planned_return=planned_return,
        responsible_account_id=responsible.id, status="planned",
        restrictions_checked=True, created_by_account_id=actor.id,
        created_by_name_snapshot=actor.professional.display_name)
    session.add(outing); session.flush()
    session.add_all([OutingStay(outing_id=outing.id, stay_id=s.id) for s in stays])
    session.add_all([OutingAuthorization(outing_id=outing.id, authorization_id=a.id) for a in auths])
    _audit(session, actor, "outing_created", f"{outing.id}; estancias:{len(stays)}")
    return outing


def set_outing_status(session: Session, *, actor_account_id: str, outing_id: str,
                      status: str, actual_at: datetime | None = None):
    outing = session.get(Outing, outing_id)
    actor = _actor(session, actor_account_id, health=bool(outing and outing.kind == "health"))
    if outing is None or status not in OUTING_STATUSES:
        raise ValueError("Salida o estado no válido")
    allowed_transitions = {"planned": {"in_progress", "cancelled"},
        "in_progress": {"returned", "cancelled"}, "returned": set(), "cancelled": set()}
    if status != outing.status and status not in allowed_transitions[outing.status]:
        raise ValueError("Transición de estado no permitida")
    moment = actual_at or datetime.now(timezone.utc)
    if status == "in_progress":
        outing.actual_departure = moment
    elif status == "returned":
        if outing.actual_departure is None:
            raise ValueError("No se puede registrar el regreso sin salida real")
        if moment < outing.actual_departure:
            raise ValueError("El regreso no puede preceder a la salida")
        outing.actual_return = moment
    outing.status = status
    _audit(session, actor, "outing_status_changed", f"{outing.id}:{status}")
    return outing
