"""Casos de uso para borradores e informes de incidencias."""
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from gestion_centro.auth.models import AccessAudit, UserAccount
from gestion_centro.domain.models import DiaryEntry
from gestion_centro.domain.incident_reports import IncidentReport, IncidentReportVersion, IncidentReportEntry


def _actor(session: Session, account_id: str) -> UserAccount:
    actor = session.get(UserAccount, account_id)
    if actor is None or not actor.active or not actor.professional.active:
        raise PermissionError("Se requiere una cuenta y un profesional activos")
    return actor


def _audit(session: Session, actor: UserAccount, event: str, details: str) -> None:
    session.add(AccessAudit(account_id=actor.id, username_snapshot=actor.username,
                            event=event, details=details))


def save_incident_report(session: Session, *, actor_account_id: str,
                         title: str, recipient: str | None, content: str,
                         entry_ids: list[str], report_id: str | None = None,
                         issue: bool = False) -> IncidentReport:
    actor = _actor(session, actor_account_id)
    clean_title = title.strip()
    clean_content = content.strip()
    clean_recipient = (recipient or "").strip() or None
    if not clean_title or not clean_content:
        raise ValueError("El título y el contenido del informe son obligatorios")
    ids = list(dict.fromkeys(entry_ids))
    if not ids:
        raise ValueError("Selecciona al menos una anotación del parte diario")
    entries = session.scalars(select(DiaryEntry).where(DiaryEntry.id.in_(ids))).all()
    if len(entries) != len(ids):
        raise ValueError("Una o varias anotaciones seleccionadas ya no existen")
    entries_by_id = {entry.id: entry for entry in entries}
    ordered_ids = sorted(ids, key=lambda item: (
        entries_by_id[item].happened_at, entries_by_id[item].recorded_at, item
    ))
    now = datetime.now(timezone.utc)
    report = session.get(IncidentReport, report_id) if report_id else None
    if report is None:
        if report_id:
            raise ValueError("El informe que intentas modificar no existe")
        report = IncidentReport(
            title=clean_title, recipient=clean_recipient, status="draft",
            created_by_account_id=actor.id,
            created_by_name_snapshot=actor.professional.display_name,
            updated_at=now,
        )
        session.add(report)
        session.flush()
    elif report.status in {"issued", "rectified"}:
        if not issue:
            raise ValueError("Un informe emitido no se modifica; crea una nueva versión rectificada")
        report.status = "rectified"
    report.title = clean_title
    report.recipient = clean_recipient
    report.updated_at = now
    latest_number = session.scalar(select(IncidentReportVersion.version_number)
        .where(IncidentReportVersion.report_id == report.id)
        .order_by(IncidentReportVersion.version_number.desc()).limit(1)) or 0
    version_status = "rectified" if report.status == "rectified" else ("issued" if issue else "draft")
    version = IncidentReportVersion(
        report_id=report.id, version_number=latest_number + 1,
        status=version_status, content=clean_content,
        created_by_account_id=actor.id,
        created_by_name_snapshot=actor.professional.display_name,
        created_at=now,
    )
    session.add(version)
    session.flush()
    for entry_id in ordered_ids:
        session.add(IncidentReportEntry(version_id=version.id, entry_id=entry_id))
    if issue:
        report.status = "rectified" if version_status == "rectified" else "issued"
        report.issued_at = now
        report.issued_by_account_id = actor.id
        report.issued_by_name_snapshot = actor.professional.display_name
    elif report.status not in {"issued", "rectified"}:
        report.status = "draft"
    _audit(session, actor, "incident_report_version_created",
           f"informe:{report.id}; version:{version.version_number}; estado:{version.status}; hechos:{len(ids)}")
    return report


def list_incident_reports(session: Session, *, actor_account_id: str) -> list[IncidentReport]:
    actor = _actor(session, actor_account_id)
    _audit(session, actor, "incident_reports_accessed", "Listado general")
    return session.scalars(select(IncidentReport).order_by(
        IncidentReport.updated_at.desc(), IncidentReport.created_at.desc()
    )).all()


def get_incident_report(session: Session, *, actor_account_id: str,
                        report_id: str) -> IncidentReport:
    actor = _actor(session, actor_account_id)
    report = session.get(IncidentReport, report_id)
    if report is None:
        raise ValueError("El informe no existe")
    _audit(session, actor, "incident_report_opened", report.id)
    return report
