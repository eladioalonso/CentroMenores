"""Servicios para informes externos con mínimo de datos y doble revisión."""
from datetime import datetime, timezone, date
from sqlalchemy import select
from sqlalchemy.orm import Session
from gestion_centro.auth.models import AccessAudit, UserAccount
from gestion_centro.domain.models import Stay
from gestion_centro.domain.documents import Authorization
from gestion_centro.domain.external_reports import ExternalReport

ALLOWED_REPORT_FIELDS = {"identity_basic", "stay_dates", "education", "schooling"}


def _actor(session: Session, account_id: str) -> UserAccount:
    actor = session.get(UserAccount, account_id)
    if actor is None or not actor.active or not actor.professional.active:
        raise PermissionError("Se requiere una cuenta y un profesional activos")
    return actor


def _audit(session: Session, actor: UserAccount, event: str, details: str):
    session.add(AccessAudit(account_id=actor.id, username_snapshot=actor.username,
        event=event, details=details))


def create_external_report(session: Session, *, actor_account_id: str, stay_id: str,
        authorization_id: str, recipient: str, purpose: str,
        included_fields: list[str], content: str):
    actor = _actor(session, actor_account_id)
    stay = session.get(Stay, stay_id)
    authorization = session.get(Authorization, authorization_id)
    today = date.today()
    if stay is None or stay.status != "active":
        raise ValueError("La estancia no existe o está cerrada")
    if authorization is None or authorization.stay_id != stay_id or authorization.status != "valid":
        raise ValueError("Selecciona una autorización vigente de esta estancia")
    if authorization.valid_from > today or (authorization.valid_until and authorization.valid_until < today):
        raise ValueError("La autorización está fuera de vigencia")
    fields = set(included_fields)
    if not fields or not fields.issubset(ALLOWED_REPORT_FIELDS):
        raise ValueError("La selección de campos no es válida")
    if not recipient.strip() or not purpose.strip() or not content.strip():
        raise ValueError("Destinatario, finalidad y contenido son obligatorios")
    report = ExternalReport(stay_id=stay_id, authorization_id=authorization_id,
        recipient=recipient.strip(), purpose=purpose.strip(),
        included_fields=",".join(sorted(fields)), content=content.strip(),
        status="draft", created_by_account_id=actor.id,
        created_by_name_snapshot=actor.professional.display_name)
    session.add(report); session.flush()
    _audit(session, actor, "external_report_created",
        f"{report.id}; estancia:{stay_id}; campos:{report.included_fields}")
    return report


def review_external_report(session: Session, *, actor_account_id: str, report_id: str):
    actor = _actor(session, actor_account_id)
    report = session.get(ExternalReport, report_id)
    if report is None or report.status != "draft":
        raise ValueError("Solo se pueden revisar informes pendientes")
    if report.created_by_account_id == actor.id:
        raise PermissionError("La revisión debe realizarla otro profesional")
    authorization = session.get(Authorization, report.authorization_id)
    today = date.today()
    if authorization is None or authorization.status != "valid" or authorization.valid_from > today or (
        authorization.valid_until and authorization.valid_until < today
    ):
        raise ValueError("La autorización ya no está vigente; no se puede aprobar el informe")
    report.status = "reviewed"
    report.reviewed_by_account_id = actor.id
    report.reviewed_by_name_snapshot = actor.professional.display_name
    report.reviewed_at = datetime.now(timezone.utc)
    _audit(session, actor, "external_report_reviewed", report.id)
    return report


def mark_external_report_delivered(session: Session, *, actor_account_id: str,
        report_id: str, delivery_reference: str):
    actor = _actor(session, actor_account_id)
    report = session.get(ExternalReport, report_id)
    if report is None or report.status != "reviewed":
        raise ValueError("Solo se pueden entregar informes revisados")
    if not delivery_reference.strip():
        raise ValueError("Indica el justificante o referencia de entrega")
    report.status = "delivered"
    report.delivery_reference = delivery_reference.strip()
    report.delivered_by_account_id = actor.id
    report.delivered_by_name_snapshot = actor.professional.display_name
    report.delivered_at = datetime.now(timezone.utc)
    _audit(session, actor, "external_report_delivered", f"{report.id}:{delivery_reference.strip()}")
    return report


def list_external_reports(session: Session, *, actor_account_id: str, stay_id: str):
    actor = _actor(session, actor_account_id)
    if session.get(Stay, stay_id) is None:
        raise ValueError("La estancia no existe")
    _audit(session, actor, "external_reports_accessed", stay_id)
    return session.scalars(select(ExternalReport).where(
        ExternalReport.stay_id == stay_id).order_by(ExternalReport.created_at.desc())).all()
