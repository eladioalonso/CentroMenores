"""Datos sanitarios operativos. No diagnostica ni prescribe."""
from __future__ import annotations
from datetime import date, datetime, timezone
from uuid import uuid4
from sqlalchemy import Date, DateTime, ForeignKey, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from gestion_centro.persistence.base import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class HealthProfile(Base):
    __tablename__ = "health_profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    minor_id: Mapped[str] = mapped_column(ForeignKey("minors.id"), nullable=False, unique=True)
    # Estancia de procedencia del primer registro; no determina la identidad del perfil.
    stay_id: Mapped[str | None] = mapped_column(ForeignKey("stays.id"), nullable=True)
    allergies: Mapped[str | None] = mapped_column(Text)
    relevant_conditions: Mapped[str | None] = mapped_column(Text)
    emergency_instructions: Mapped[str | None] = mapped_column(Text)
    updated_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    updated_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class HealthProfileVersion(Base):
    """Instantánea inmutable de cada versión de la ficha sanitaria general."""
    __tablename__ = "health_profile_versions"
    __table_args__ = (Index("ix_health_profile_versions_minor_changed", "minor_id", "changed_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    minor_id: Mapped[str] = mapped_column(ForeignKey("minors.id"), nullable=False)
    profile_id: Mapped[str] = mapped_column(String(36), nullable=False)
    changed_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    changed_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    old_values: Mapped[dict] = mapped_column(JSON, nullable=False)
    new_values: Mapped[dict] = mapped_column(JSON, nullable=False)


class MedicationPlanVersion(Base):
    """Instantánea inmutable de una pauta y sus horarios prescritos."""
    __tablename__ = "medication_plan_versions"
    __table_args__ = (Index("ix_medication_plan_versions_plan_changed", "plan_id", "changed_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    plan_id: Mapped[str] = mapped_column(ForeignKey("medication_plans.id"), nullable=False)
    minor_id: Mapped[str] = mapped_column(ForeignKey("minors.id"), nullable=False)
    changed_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    changed_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    old_values: Mapped[dict] = mapped_column(JSON, nullable=False)
    new_values: Mapped[dict] = mapped_column(JSON, nullable=False)

class MedicationPlan(Base):
    __tablename__ = "medication_plans"
    __table_args__ = (Index("ix_medication_plans_minor_active", "minor_id", "active"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    minor_id: Mapped[str] = mapped_column(ForeignKey("minors.id"), nullable=False)
    # Estancia en la que se registró la pauta, conservada como dato histórico opcional.
    stay_id: Mapped[str | None] = mapped_column(ForeignKey("stays.id"), nullable=True)
    medication_name: Mapped[str] = mapped_column(String(180), nullable=False)
    prescribed_dose: Mapped[str] = mapped_column(String(120), nullable=False)
    schedule_text: Mapped[str] = mapped_column(String(240), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text)
    prescriber_reference: Mapped[str] = mapped_column(String(180), nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date | None] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(nullable=False, default=True)
    recorded_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    recorded_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    administrations: Mapped[list[MedicationAdministration]] = relationship(back_populates="plan", order_by="MedicationAdministration.scheduled_at")
    schedules: Mapped[list[MedicationSchedule]] = relationship(back_populates="plan", cascade="all, delete-orphan", order_by="MedicationSchedule.time_of_day")

class MedicationSchedule(Base):
    """Hora diaria explícita de una pauta, transcrita desde la prescripción."""
    __tablename__ = "medication_schedules"
    __table_args__ = (Index("ix_medication_schedules_plan_shift", "plan_id", "shift"), UniqueConstraint("plan_id", "time_of_day", name="uq_medication_schedule_plan_time"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    plan_id: Mapped[str] = mapped_column(ForeignKey("medication_plans.id"), nullable=False)
    time_of_day: Mapped[str] = mapped_column(String(5), nullable=False)
    shift: Mapped[str] = mapped_column(String(16), nullable=False)
    plan: Mapped[MedicationPlan] = relationship(back_populates="schedules")

class MedicationAdministration(Base):
    __tablename__ = "medication_administrations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    plan_id: Mapped[str] = mapped_column(ForeignKey("medication_plans.id"), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    shift: Mapped[str] = mapped_column(String(16), nullable=False, default="unspecified")
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    recorded_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    recorded_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    plan: Mapped[MedicationPlan] = relationship(back_populates="administrations")

class VaccineRecord(Base):
    __tablename__ = "vaccine_records"
    __table_args__ = (Index("ix_vaccine_records_minor_date", "minor_id", "administered_on"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    minor_id: Mapped[str] = mapped_column(ForeignKey("minors.id"), nullable=False)
    stay_id: Mapped[str | None] = mapped_column(ForeignKey("stays.id"), nullable=True)
    vaccine_name: Mapped[str] = mapped_column(String(180), nullable=False)
    administered_on: Mapped[date] = mapped_column(Date, nullable=False)
    dose_reference: Mapped[str | None] = mapped_column(String(80))
    source_document_id: Mapped[str | None] = mapped_column(String(36))
    recorded_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    recorded_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class VaccineCalendarEdition(Base):
    """Edición documental de un calendario; no contiene prescripción ejecutable."""
    __tablename__ = "vaccine_calendar_editions"
    __table_args__ = (UniqueConstraint("jurisdiction", "edition_code", name="uq_vaccine_calendar_jurisdiction_edition"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    jurisdiction: Mapped[str] = mapped_column(String(80), nullable=False)
    edition_code: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_until: Mapped[date | None] = mapped_column(Date)
    source_title: Mapped[str] = mapped_column(String(240), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(240), nullable=False)
    source_url: Mapped[str] = mapped_column(String(600), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="documentary")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class VaccineCalendarItem(Base):
    """Fila de calendario transcrita como referencia; no calcula indicaciones."""
    __tablename__ = "vaccine_calendar_items"
    __table_args__ = (Index("ix_vaccine_calendar_items_edition", "edition_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    edition_id: Mapped[str] = mapped_column(ForeignKey("vaccine_calendar_editions.id"), nullable=False)
    vaccine_code: Mapped[str] = mapped_column(String(40), nullable=False)
    display_name: Mapped[str] = mapped_column(String(180), nullable=False)
    dose_label: Mapped[str] = mapped_column(String(240), nullable=False)
    entry_kind: Mapped[str] = mapped_column(String(16), nullable=False, default="dose")
    target_age_text: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(24), nullable=False, default="systematic")
    documentary_note: Mapped[str | None] = mapped_column(Text)
    source_page: Mapped[str | None] = mapped_column(String(40))


class VaccineDoseReview(Base):
    """Revisión individual y validada por profesional de una dosis orientativa."""
    __tablename__ = "vaccine_dose_reviews"
    __table_args__ = (
        Index("ix_vaccine_dose_reviews_minor_status", "minor_id", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    minor_id: Mapped[str] = mapped_column(ForeignKey("minors.id"), nullable=False)
    calendar_item_id: Mapped[str | None] = mapped_column(ForeignKey("vaccine_calendar_items.id"))
    vaccine_record_id: Mapped[str | None] = mapped_column(ForeignKey("vaccine_records.id"))
    category: Mapped[str] = mapped_column(String(24), nullable=False, default="systematic")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unverified")
    target_date: Mapped[date | None] = mapped_column(Date)
    reviewed_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    reviewed_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
