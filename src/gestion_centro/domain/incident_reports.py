"""Informes de incidencias versionados y vinculados a hechos del parte diario."""
from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from gestion_centro.persistence.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IncidentReport(Base):
    __tablename__ = "incident_reports"
    __table_args__ = (Index("ix_incident_reports_status_updated", "status", "updated_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    recipient: Mapped[str | None] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    created_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    issued_by_account_id: Mapped[str | None] = mapped_column(ForeignKey("user_accounts.id"))
    issued_by_name_snapshot: Mapped[str | None] = mapped_column(String(160))
    versions: Mapped[list[IncidentReportVersion]] = relationship(
        back_populates="report", cascade="all, delete-orphan",
        order_by="IncidentReportVersion.version_number"
    )


class IncidentReportVersion(Base):
    __tablename__ = "incident_report_versions"
    __table_args__ = (
        UniqueConstraint("report_id", "version_number", name="uq_incident_report_version"),
        Index("ix_incident_report_versions_report_created", "report_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    report_id: Mapped[str] = mapped_column(ForeignKey("incident_reports.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    recipient: Mapped[str | None] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    created_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    report: Mapped[IncidentReport] = relationship(back_populates="versions")
    entries: Mapped[list[IncidentReportEntry]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )


class IncidentReportEntry(Base):
    __tablename__ = "incident_report_entries"
    __table_args__ = (UniqueConstraint("version_id", "entry_id", name="uq_incident_report_entry"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    version_id: Mapped[str] = mapped_column(ForeignKey("incident_report_versions.id"), nullable=False)
    entry_id: Mapped[str] = mapped_column(ForeignKey("diary_entries.id"), nullable=False)
    version: Mapped[IncidentReportVersion] = relationship(back_populates="entries")
