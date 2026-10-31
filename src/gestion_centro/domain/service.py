"""Servicios transaccionales del núcleo de expedientes."""

from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gestion_centro.auth.models import AccessAudit, UserAccount
from gestion_centro.domain.models import Event, EventStayLink, Minor, Stay


def create_minor(
    session: Session, *, actor_account_id: str, internal_code: str, given_names: str, family_names: str
) -> Minor:
    actor = _active_author(session, actor_account_id)
    code = internal_code.strip().upper()
    if not code or not given_names.strip() or not family_names.strip():
        raise ValueError("El código y el nombre completo son obligatorios")
    if session.scalar(select(Minor.id).where(Minor.internal_code == code)) is not None:
        raise ValueError("El identificador interno ya existe")
    minor = Minor(internal_code=code, given_names=given_names.strip(), family_names=family_names.strip())
    session.add(minor)
    session.flush()
    _audit(session, actor, "minor_created", f"Expediente: {minor.id}")
    return minor


def open_stay(session: Session, *, actor_account_id: str, minor_id: str, started_on: date) -> Stay:
    actor = _active_author(session, actor_account_id)
    minor = session.get(Minor, minor_id)
    if minor is None or not minor.active:
        raise ValueError("El expediente no existe o está inactivo")
    active = session.scalar(select(Stay.id).where(Stay.minor_id == minor_id, Stay.status == "active"))
    if active is not None:
        raise ValueError("El menor ya tiene una estancia activa")
    sequence = session.scalar(
        select(func.coalesce(func.max(Stay.sequence_number), 0)).where(Stay.minor_id == minor_id)
    ) + 1
    stay = Stay(minor_id=minor_id, sequence_number=sequence, started_on=started_on, status="active")
    session.add(stay)
    session.flush()
    _audit(session, actor, "stay_opened", f"Estancia: {stay.id}")
    return stay


def close_stay(session: Session, *, actor_account_id: str, stay_id: str, ended_on: date, reason: str) -> None:
    actor = _active_author(session, actor_account_id)
    stay = session.get(Stay, stay_id)
    if stay is None or stay.status != "active":
        raise ValueError("La estancia no existe o ya está cerrada")
    if ended_on < stay.started_on:
        raise ValueError("La fecha de cierre no puede ser anterior al inicio")
    if not reason.strip():
        raise ValueError("Es obligatorio indicar el motivo del cierre")
    stay.status = "closed"
    stay.ended_on = ended_on
    stay.closure_reason = reason.strip()
    _audit(session, actor, "stay_closed", f"Estancia: {stay.id}")


def record_event(
    session: Session, *, author_account_id: str, title: str, description: str,
    happened_at: datetime, stay_ids: list[str],
) -> Event:
    author = _active_author(session, author_account_id)
    if not title.strip() or not description.strip():
        raise ValueError("El título y la descripción son obligatorios")
    if len(stay_ids) != len(set(stay_ids)):
        raise ValueError("No se puede asociar dos veces la misma estancia")
    stays = [session.get(Stay, stay_id) for stay_id in stay_ids]
    if any(stay is None for stay in stays):
        raise ValueError("Una de las estancias seleccionadas no existe")
    event = Event(
        title=title.strip(), description=description.strip(), happened_at=happened_at,
        author_account_id=author.id, author_name_snapshot=author.professional.display_name,
    )
    session.add(event)
    session.flush()
    for stay in stays:
        minor = stay.minor
        session.add(EventStayLink(
            event_id=event.id, stay_id=stay.id, participation_role="participant",
            minor_code_snapshot=minor.internal_code,
            minor_name_snapshot=f"{minor.given_names} {minor.family_names}",
        ))
    session.flush()
    _audit(session, author, "event_recorded", f"Acontecimiento: {event.id}; vínculos: {len(stay_ids)}")
    return event


def _active_author(session: Session, account_id: str) -> UserAccount:
    account = session.get(UserAccount, account_id)
    if account is None or not account.active or not account.professional.active:
        raise PermissionError("Se requiere una cuenta y un profesional activos")
    return account


def _audit(session: Session, actor: UserAccount, event: str, details: str) -> None:
    session.add(AccessAudit(
        account_id=actor.id, username_snapshot=actor.username, event=event, details=details,
    ))


VALID_SHIFTS = {"morning", "afternoon", "night"}
VALID_CATEGORIES = {"general", "activity", "health", "observation", "positive", "negative", "maintenance", "other"}
VALID_SEVERITIES = {"low", "medium", "high", "critical"}
VALID_INCIDENT_TYPES = {"behavior", "health", "safety", "conflict", "escape", "damage", "other"}


def _diary_deadline(diary_date: date, reference: datetime) -> datetime:
    from datetime import timedelta
    return datetime.combine(diary_date + timedelta(days=2), datetime.min.time(), tzinfo=reference.tzinfo)


def _ensure_diary_open(session: Session, day, actor: UserAccount, now: datetime | None = None) -> None:
    moment = now or datetime.now(timezone.utc)
    deadline = _diary_deadline(day.diary_date, moment)
    if day.closed_at is None and moment >= deadline:
        day.closed_at = deadline
        day.closed_by_account_id = None
        _audit(session, actor, "diary_day_auto_closed", f"Fecha: {day.diary_date.isoformat()}; cierre automático por plazo")
    if day.closed_at is not None:
        raise ValueError("El diario está cerrado; debe registrarse una rectificación")


def close_expired_diary_days(session: Session, *, now: datetime | None = None) -> int:
    """Cierra diarios vencidos; llamar al iniciar la aplicación y en tareas de mantenimiento."""
    from gestion_centro.domain.models import DiaryDay
    moment = now or datetime.now(timezone.utc)
    days = session.scalars(select(DiaryDay).where(DiaryDay.closed_at.is_(None))).all()
    closed = 0
    for day in days:
        deadline = _diary_deadline(day.diary_date, moment)
        if moment >= deadline:
            day.closed_at = deadline
            day.closed_by_account_id = None
            closed += 1
    return closed


def _get_or_create_diary_day(session: Session, diary_date: date):
    from gestion_centro.domain.models import DiaryDay
    day = session.scalar(select(DiaryDay).where(DiaryDay.diary_date == diary_date))
    if day is None:
        day = DiaryDay(diary_date=diary_date)
        session.add(day)
        session.flush()
    return day


def record_diary_entry(
    session: Session, *, actor_account_id: str, diary_date: date, shift: str,
    category: str, content: str, happened_at: datetime, stay_ids: list[str] | None = None,
    now: datetime | None = None,
):
    from gestion_centro.domain.models import DiaryEntry, DiaryEntryStayLink
    actor = _active_author(session, actor_account_id)
    if shift not in VALID_SHIFTS or category not in VALID_CATEGORIES:
        raise ValueError("Turno o categoría no válidos")
    if not content.strip():
        raise ValueError("El contenido de la anotación es obligatorio")
    day = _get_or_create_diary_day(session, diary_date)
    _ensure_diary_open(session, day, actor, now=now)
    ids = stay_ids or []
    if len(ids) != len(set(ids)):
        raise ValueError("Hay estancias duplicadas")
    stays = [session.get(Stay, stay_id) for stay_id in ids]
    if any(stay is None for stay in stays):
        raise ValueError("Una estancia vinculada no existe")
    entry = DiaryEntry(
        diary_day_id=day.id, shift=shift, category=category, content=content.strip(),
        happened_at=happened_at, author_account_id=actor.id,
        author_name_snapshot=actor.professional.display_name,
    )
    session.add(entry)
    session.flush()
    for stay in stays:
        minor = stay.minor
        session.add(DiaryEntryStayLink(
            entry_id=entry.id, stay_id=stay.id, minor_code_snapshot=minor.internal_code,
            minor_name_snapshot=f"{minor.given_names} {minor.family_names}",
        ))
    _audit(session, actor, "diary_entry_recorded", f"Anotación: {entry.id}")
    return entry


def close_diary_day(session: Session, *, actor_account_id: str, diary_date: date, now: datetime | None = None):
    from datetime import timedelta
    from gestion_centro.domain.models import DiaryDay
    actor = _active_author(session, actor_account_id)
    day = session.scalar(select(DiaryDay).where(DiaryDay.diary_date == diary_date))
    if day is None:
        raise ValueError("No existe el diario de esa fecha")
    if day.closed_at is not None:
        raise ValueError("El diario ya está cerrado")
    moment = now or datetime.now(timezone.utc)
    deadline = _diary_deadline(diary_date, moment)
    if moment >= deadline:
        day.closed_at = deadline
        day.closed_by_account_id = None
        _audit(session, actor, "diary_day_auto_closed", f"Fecha: {diary_date.isoformat()}; cierre automático por plazo")
        return day
    day.closed_at = moment
    day.closed_by_account_id = actor.id
    _audit(session, actor, "diary_day_closed", f"Fecha: {diary_date.isoformat()}")
    return day


def correct_diary_entry(
    session: Session, *, actor_account_id: str, original_entry_id: str, content: str,
    happened_at: datetime, reason: str,
):
    from gestion_centro.domain.models import DiaryEntry
    actor = _active_author(session, actor_account_id)
    original = session.get(DiaryEntry, original_entry_id)
    if original is None:
        raise ValueError("La anotación original no existe")
    if not content.strip() or not reason.strip():
        raise ValueError("La rectificación y su motivo son obligatorios")
    correction = DiaryEntry(
        diary_day_id=original.diary_day_id, shift=original.shift, category="other",
        content=f"RECTIFICACIÓN ({reason.strip()}): {content.strip()}",
        happened_at=happened_at, author_account_id=actor.id,
        author_name_snapshot=actor.professional.display_name, correction_of_id=original.id,
    )
    session.add(correction)
    session.flush()
    _audit(session, actor, "diary_entry_corrected", f"Original: {original.id}; rectificación: {correction.id}")
    return correction


def record_incident(
    session: Session, *, actor_account_id: str, diary_date: date, title: str,
    description: str, incident_type: str, severity: str, happened_at: datetime,
    participants: list[tuple[str, str, str | None]], now: datetime | None = None,
):
    from gestion_centro.domain.models import Incident, IncidentParticipant
    actor = _active_author(session, actor_account_id)
    if incident_type not in VALID_INCIDENT_TYPES or severity not in VALID_SEVERITIES:
        raise ValueError("Tipo o gravedad de incidencia no válidos")
    if not title.strip() or not description.strip():
        raise ValueError("El título y la descripción son obligatorios")
    day = _get_or_create_diary_day(session, diary_date)
    _ensure_diary_open(session, day, actor, now=now)
    seen = set()
    stays = []
    for stay_id, role, factual_note in participants:
        if stay_id in seen:
            raise ValueError("Una estancia no puede repetirse en la incidencia")
        seen.add(stay_id)
        if role not in {"affected", "witness", "involved", "reporting"}:
            raise ValueError("Rol de participación no válido")
        stay = session.get(Stay, stay_id)
        if stay is None:
            raise ValueError("Una estancia vinculada no existe")
        stays.append((stay, role, factual_note))
    incident = Incident(
        diary_day_id=day.id, title=title.strip(), description=description.strip(),
        incident_type=incident_type, severity=severity, happened_at=happened_at,
        author_account_id=actor.id, author_name_snapshot=actor.professional.display_name,
    )
    session.add(incident)
    session.flush()
    for stay, role, factual_note in stays:
        minor = stay.minor
        session.add(IncidentParticipant(
            incident_id=incident.id, stay_id=stay.id, role=role,
            factual_note=factual_note, minor_code_snapshot=minor.internal_code,
            minor_name_snapshot=f"{minor.given_names} {minor.family_names}",
        ))
    _audit(session, actor, "incident_recorded", f"Incidencia: {incident.id}")
    return incident


def close_incident(
    session: Session, *, actor_account_id: str, incident_id: str, note: str, now: datetime | None = None,
):
    from gestion_centro.domain.models import Incident
    actor = _active_author(session, actor_account_id)
    incident = session.get(Incident, incident_id)
    if incident is None or incident.status != "open":
        raise ValueError("La incidencia no existe o no está abierta")
    if not note.strip():
        raise ValueError("El cierre requiere una nota")
    incident.status = "closed"
    incident.closed_at = now or datetime.now(timezone.utc)
    incident.closed_by_account_id = actor.id
    incident.closure_note = note.strip()
    _audit(session, actor, "incident_closed", f"Incidencia: {incident.id}")


def reopen_incident(
    session: Session, *, actor_account_id: str, incident_id: str, reason: str,
):
    from gestion_centro.domain.models import Incident
    actor = _active_author(session, actor_account_id)
    incident = session.get(Incident, incident_id)
    if incident is None or incident.status != "closed":
        raise ValueError("La incidencia no existe o no está cerrada")
    if not reason.strip():
        raise ValueError("La reapertura requiere un motivo")
    incident.status = "open"
    incident.closed_at = None
    incident.closed_by_account_id = None
    # El motivo del cierre anterior se conserva; la reapertura queda en auditoría.
    _audit(session, actor, "incident_reopened", f"Incidencia: {incident.id}; motivo: {reason.strip()}")
