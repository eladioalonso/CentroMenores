"""Preparación y entrega controlada de informes a terceros."""
from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from gestion_centro.persistence.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExternalReport(Base):
    __tablename__ = "external_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    stay_id: Mapped[str] = mapped_column(ForeignKey("stays.id"), nullable=False)
    authorization_id: Mapped[str] = mapped_column(ForeignKey("authorizations.id"), nullable=False)
    recipient: Mapped[str] = mapped_column(String(180), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    included_fields: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    created_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    reviewed_by_account_id: Mapped[str | None] = mapped_column(ForeignKey("user_accounts.id"))
    reviewed_by_name_snapshot: Mapped[str | None] = mapped_column(String(160))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_reference: Mapped[str | None] = mapped_column(String(180))
    delivered_by_account_id: Mapped[str | None] = mapped_column(ForeignKey("user_accounts.id"))
    delivered_by_name_snapshot: Mapped[str | None] = mapped_column(String(160))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
