"""Seguimiento educativo y escolaridad por estancia."""
from __future__ import annotations
from datetime import date, datetime, timezone
from uuid import uuid4
from sqlalchemy import Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from gestion_centro.persistence.base import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class EducationGoal(Base):
    __tablename__ = "education_goals"
    __table_args__ = (Index("ix_education_goals_stay_status", "stay_id", "status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    stay_id: Mapped[str] = mapped_column(ForeignKey("stays.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    created_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    created_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updates: Mapped[list[EducationUpdate]] = relationship(back_populates="goal", cascade="all, delete-orphan", order_by="EducationUpdate.created_at")

class EducationUpdate(Base):
    __tablename__ = "education_updates"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    goal_id: Mapped[str] = mapped_column(ForeignKey("education_goals.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    objective_description: Mapped[str] = mapped_column(Text, nullable=False)
    actions_taken: Mapped[str] = mapped_column(Text, nullable=False)
    response_observed: Mapped[str] = mapped_column(Text, nullable=False)
    follow_up: Mapped[str | None] = mapped_column(Text)
    author_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    author_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    goal: Mapped[EducationGoal] = relationship(back_populates="updates")

class SchoolPlacement(Base):
    __tablename__ = "school_placements"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    stay_id: Mapped[str] = mapped_column(ForeignKey("stays.id"), nullable=False)
    school_name: Mapped[str] = mapped_column(String(180), nullable=False)
    course: Mapped[str] = mapped_column(String(80), nullable=False)
    started_on: Mapped[date] = mapped_column(Date, nullable=False)
    ended_on: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    created_by_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    records: Mapped[list[SchoolRecord]] = relationship(back_populates="placement", cascade="all, delete-orphan", order_by="SchoolRecord.occurred_on")

class SchoolRecord(Base):
    __tablename__ = "school_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    placement_id: Mapped[str] = mapped_column(ForeignKey("school_placements.id"), nullable=False)
    record_type: Mapped[str] = mapped_column(String(24), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    author_account_id: Mapped[str] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    author_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    placement: Mapped[SchoolPlacement] = relationship(back_populates="records")
