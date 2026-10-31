"""Servicios transaccionales del núcleo de expedientes."""

from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gestion_centro.auth.models import UserAccount
from gestion_centro.domain.models import Event, EventStayLink, Minor, Stay


def create_minor(
    session: Session, *, internal_code: str, given_names: str, family_names: str
) -> Minor:
    code = internal_code.strip().upper()
    if not code or not given_names.strip() or not family_names.strip():
        raise ValueError("El código y el nombre completo son obligatorios")
    if session.scalar(select(Minor.id).where(Minor.internal_code == code)) is not None:
        raise ValueError("El identificador interno ya existe")
    minor = Minor(internal_code=code, given_names=given_names.strip(), family_names=family_names.strip())
    session.add(minor)
    session.flush()
    return minor


def open_stay(session: Session, *, minor_id: str, started_on: date) -> Stay:
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
    return stay


def close_stay(session: Session, *, stay_id: str, ended_on: date, reason: str) -> None:
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


def record_event(
    session: Session, *, author_account_id: str, title: str, description: str,
    happened_at: datetime, stay_ids: list[str],
) -> Event:
    author = session.get(UserAccount, author_account_id)
    if author is None or not author.active:
        raise PermissionError("Se requiere una cuenta activa")
    if not title.strip() or not description.strip():
        raise ValueError("El título y la descripción son obligatorios")
    if len(stay_ids) != len(set(stay_ids)):
        raise ValueError("No se puede asociar dos veces la misma estancia")
    event = Event(
        title=title.strip(), description=description.strip(), happened_at=happened_at,
        author_account_id=author.id, author_name_snapshot=author.professional.display_name,
    )
    session.add(event)
    session.flush()
    for stay_id in stay_ids:
        stay = session.get(Stay, stay_id)
        if stay is None:
            raise ValueError("Una de las estancias seleccionadas no existe")
        minor = stay.minor
        session.add(EventStayLink(
            event_id=event.id, stay_id=stay.id, participation_role="participant",
            minor_code_snapshot=minor.internal_code,
            minor_name_snapshot=f"{minor.given_names} {minor.family_names}",
        ))
    session.flush()
    return event
