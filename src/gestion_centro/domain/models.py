"""Modelo inicial de menores, estancias y acontecimientos compartidos.

No almacena aquí datos sanitarios ni documentos adjuntos: esos módulos tendrán
sus propios controles de acceso, historial y migraciones.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Date, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gestion_centro.persistence.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Minor(Base):
    __tablename__ = "minors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    internal_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    given_names: Mapped[str] = mapped_column(String(160), nullable=False)
    family_names: Mapped[str] = mapped_column(String(200), nullable=False)
    active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    stays: Mapped[list[Stay]] = relationship(back_populates="minor")


class Stay(Base):
    __tablename__ = "stays"
    __table_args__ = (
        Index(
            "uq_stays_one_active_per_minor", "minor_id", unique=True,
            sqlite_where=text("status = 'active'"),
        ),
        UniqueConstraint("minor_id", "sequence_number", name="uq_stay_minor_sequence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    minor_id: Mapped[str] = mapped_column(ForeignKey("minors.id"), nullable=False)
    sequence_number: Mapped[int] = mapped_column(nullable=False)
    started_on: Mapped[date] = mapped_column(Date, nullable=False)
    ended_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    closure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    minor: Mapped[Minor] = relationship(back_populates="stays")


class Event(Base):
    """Acontecimiento único; puede aparecer en varios historiales individuales."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    happened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    author_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    author_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="recorded")
    correction_of_id: Mapped[str | None] = mapped_column(ForeignKey("events.id"), nullable=True)

    participants: Mapped[list[EventStayLink]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class EventStayLink(Base):
    """Vincula un mismo acontecimiento a cada menor y estancia implicados."""

    __tablename__ = "event_stay_links"
    __table_args__ = (
        UniqueConstraint("event_id", "stay_id", name="uq_event_stay_link"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    stay_id: Mapped[str] = mapped_column(ForeignKey("stays.id"), nullable=False)
    participation_role: Mapped[str] = mapped_column(String(32), nullable=False, default="participant")
    minor_code_snapshot: Mapped[str] = mapped_column(String(32), nullable=False)
    minor_name_snapshot: Mapped[str] = mapped_column(String(360), nullable=False)

    event: Mapped[Event] = relationship(back_populates="participants")


class DiaryDay(Base):
    __tablename__ = "diary_days"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    diary_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by_account_id: Mapped[str | None] = mapped_column(ForeignKey("user_accounts.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    entries: Mapped[list[DiaryEntry]] = relationship(back_populates="diary_day")


class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    diary_day_id: Mapped[str] = mapped_column(ForeignKey("diary_days.id"), nullable=False)
    shift: Mapped[str] = mapped_column(String(12), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    happened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    author_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    author_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    correction_of_id: Mapped[str | None] = mapped_column(ForeignKey("diary_entries.id"), nullable=True)

    diary_day: Mapped[DiaryDay] = relationship(back_populates="entries")
    participants: Mapped[list[DiaryEntryStayLink]] = relationship(back_populates="entry", cascade="all, delete-orphan")


class DiaryEntryStayLink(Base):
    __tablename__ = "diary_entry_stay_links"
    __table_args__ = (UniqueConstraint("entry_id", "stay_id", name="uq_diary_entry_stay"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    entry_id: Mapped[str] = mapped_column(ForeignKey("diary_entries.id"), nullable=False)
    stay_id: Mapped[str] = mapped_column(ForeignKey("stays.id"), nullable=False)
    minor_code_snapshot: Mapped[str] = mapped_column(String(32), nullable=False)
    minor_name_snapshot: Mapped[str] = mapped_column(String(360), nullable=False)

    entry: Mapped[DiaryEntry] = relationship(back_populates="participants")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    diary_day_id: Mapped[str] = mapped_column(ForeignKey("diary_days.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    incident_type: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    happened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    author_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    author_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by_account_id: Mapped[str | None] = mapped_column(ForeignKey("user_accounts.id"), nullable=True)
    closure_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    participants: Mapped[list[IncidentParticipant]] = relationship(back_populates="incident", cascade="all, delete-orphan")


class IncidentParticipant(Base):
    __tablename__ = "incident_participants"
    __table_args__ = (UniqueConstraint("incident_id", "stay_id", name="uq_incident_stay"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), nullable=False)
    stay_id: Mapped[str] = mapped_column(ForeignKey("stays.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    factual_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    minor_code_snapshot: Mapped[str] = mapped_column(String(32), nullable=False)
    minor_name_snapshot: Mapped[str] = mapped_column(String(360), nullable=False)

    incident: Mapped[Incident] = relationship(back_populates="participants")
