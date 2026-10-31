"""Estadísticas agregadas sin nombres, identificadores ni contenido de expedientes."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gestion_centro.auth.models import AccessAudit, UserAccount
from gestion_centro.domain.models import (
    Stay, DiaryEntry, DiaryDay, Incident, AgendaItem, Event,
)


def aggregate_statistics(session: Session, *, actor_account_id: str,
                         start_date: date, end_date: date) -> dict:
    actor = session.get(UserAccount, actor_account_id)
    if actor is None or not actor.active or not actor.professional.active:
        raise PermissionError("Se requiere una cuenta activa")
    if end_date < start_date:
        raise ValueError("El periodo final no puede preceder al inicial")

    def count(query) -> int:
        return int(session.scalar(query) or 0)

    start_dt = __import__("datetime").datetime.combine(start_date, __import__("datetime").time.min)
    end_dt = __import__("datetime").datetime.combine(end_date, __import__("datetime").time.max)
    result = {
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "stays_started": count(select(func.count()).select_from(Stay).where(
            Stay.started_on >= start_date, Stay.started_on <= end_date)),
        "stays_closed": count(select(func.count()).select_from(Stay).where(
            Stay.ended_on >= start_date, Stay.ended_on <= end_date)),
        "diary_entries": count(select(func.count()).select_from(DiaryEntry).where(
            DiaryEntry.recorded_at >= start_dt, DiaryEntry.recorded_at <= end_dt)),
        "incidents": count(select(func.count()).select_from(Incident).where(
            Incident.recorded_at >= start_dt, Incident.recorded_at <= end_dt)),
        "events": count(select(func.count()).select_from(Event).where(
            Event.recorded_at >= start_dt, Event.recorded_at <= end_dt)),
        "agenda_items_created": count(select(func.count()).select_from(AgendaItem).where(
            AgendaItem.created_at >= start_dt, AgendaItem.created_at <= end_dt)),
        "open_stays_at_end": count(select(func.count()).select_from(Stay).where(
            Stay.started_on <= end_date,
            (Stay.ended_on.is_(None) | (Stay.ended_on > end_date)))),
    }
    severity_rows = session.execute(
        select(Incident.severity, func.count()).where(
            Incident.recorded_at >= start_dt, Incident.recorded_at <= end_dt
        ).group_by(Incident.severity)
    ).all()
    result["incidents_by_severity"] = {str(key): int(value) for key, value in severity_rows}
    category_rows = session.execute(
        select(DiaryEntry.category, func.count()).where(
            DiaryEntry.recorded_at >= start_dt, DiaryEntry.recorded_at <= end_dt
        ).group_by(DiaryEntry.category)
    ).all()
    result["diary_entries_by_category"] = {str(key): int(value) for key, value in category_rows}
    session.add(AccessAudit(account_id=actor.id, username_snapshot=actor.username,
        event="aggregate_report_generated", details=f"{start_date.isoformat()}:{end_date.isoformat()}"))
    return result


def export_statistics_csv(report: dict, destination: Path) -> Path:
    """Exporta únicamente métricas agregadas; nunca nombres ni identificadores."""
    rows = []
    for key, value in report.items():
        if isinstance(value, dict):
            rows.extend((f"{key}.{subkey}", subvalue) for subkey, subvalue in sorted(value.items()))
        else:
            rows.append((key, value))
    with destination.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(["Indicador", "Valor"])
        writer.writerows(rows)
    return destination
