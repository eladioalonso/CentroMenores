"""Documentos personales, autorizaciones y salidas por estancia."""
from __future__ import annotations
from datetime import date, datetime, timezone
from uuid import uuid4
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from gestion_centro.persistence.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PersonalDocument(Base):
    __tablename__ = "personal_documents"
    __table_args__ = (Index("ix_personal_documents_stay_category", "stay_id", "category"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    stay_id: Mapped[str] = mapped_column(ForeignKey("stays.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    document_date: Mapped[date | None] = mapped_column(Date)
    expires_on: Mapped[date | None] = mapped_column(Date)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    supersedes_id: Mapped[str | None] = mapped_column(ForeignKey("personal_documents.id"))
    notes: Mapped[str | None] = mapped_column(Text)
    uploaded_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    uploaded_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class Authorization(Base):
    __tablename__ = "authorizations"
    __table_args__ = (Index("ix_authorizations_stay_status", "stay_id", "status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    stay_id: Mapped[str] = mapped_column(ForeignKey("stays.id"), nullable=False)
    authorization_type: Mapped[str] = mapped_column(String(48), nullable=False)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    issuer: Mapped[str] = mapped_column(String(180), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date)
    conditions: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="valid")
    document_id: Mapped[str | None] = mapped_column(ForeignKey("personal_documents.id"))
    recorded_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    recorded_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class Outing(Base):
    __tablename__ = "outings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    destination: Mapped[str] = mapped_column(String(180), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    planned_departure: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_return: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_return: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    responsible_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="planned")
    restrictions_checked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    created_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class OutingStay(Base):
    __tablename__ = "outing_stays"
    outing_id: Mapped[str] = mapped_column(ForeignKey("outings.id"), primary_key=True)
    stay_id: Mapped[str] = mapped_column(ForeignKey("stays.id"), primary_key=True)


class OutingAuthorization(Base):
    __tablename__ = "outing_authorizations"
    outing_id: Mapped[str] = mapped_column(ForeignKey("outings.id"), primary_key=True)
    authorization_id: Mapped[str] = mapped_column(ForeignKey("authorizations.id"), primary_key=True)
