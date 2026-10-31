"""Comunicaciones internas: borradores compartidos y aportaciones append-only."""
from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from gestion_centro.persistence.base import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Communication(Base):
    __tablename__ = "communications"
    __table_args__ = (Index("ix_communications_status_updated", "status", "updated_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    created_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    created_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_by_account_id: Mapped[str | None] = mapped_column(ForeignKey("user_accounts.id"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_by_account_id: Mapped[str | None] = mapped_column(ForeignKey("user_accounts.id"))
    contributions: Mapped[list[CommunicationContribution]] = relationship(
        back_populates="communication", cascade="all, delete-orphan",
        order_by="CommunicationContribution.created_at"
    )

class CommunicationContribution(Base):
    __tablename__ = "communication_contributions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    communication_id: Mapped[str] = mapped_column(ForeignKey("communications.id"), nullable=False)
    author_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    author_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    communication: Mapped[Communication] = relationship(back_populates="contributions")
