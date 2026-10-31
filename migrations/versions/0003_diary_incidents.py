"""Añade diario cronológico e incidencias."""

from alembic import op
import sqlalchemy as sa

revision = "0003_diary_incidents"
down_revision = "0002_minor_stays_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "diary_days",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("diary_date", sa.Date(), nullable=False, unique=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "diary_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("diary_day_id", sa.String(36), sa.ForeignKey("diary_days.id"), nullable=False),
        sa.Column("shift", sa.String(12), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("happened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("author_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("author_name_snapshot", sa.String(160), nullable=False),
        sa.Column("correction_of_id", sa.String(36), sa.ForeignKey("diary_entries.id"), nullable=True),
    )
    op.create_table(
        "diary_entry_stay_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entry_id", sa.String(36), sa.ForeignKey("diary_entries.id"), nullable=False),
        sa.Column("stay_id", sa.String(36), sa.ForeignKey("stays.id"), nullable=False),
        sa.Column("minor_code_snapshot", sa.String(32), nullable=False),
        sa.Column("minor_name_snapshot", sa.String(360), nullable=False),
        sa.UniqueConstraint("entry_id", "stay_id", name="uq_diary_entry_stay"),
    )
    op.create_table(
        "incidents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("diary_day_id", sa.String(36), sa.ForeignKey("diary_days.id"), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("incident_type", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("happened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("author_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("author_name_snapshot", sa.String(160), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=True),
        sa.Column("closure_note", sa.Text(), nullable=True),
    )
    op.create_table(
        "incident_participants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("stay_id", sa.String(36), sa.ForeignKey("stays.id"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("factual_note", sa.Text(), nullable=True),
        sa.Column("minor_code_snapshot", sa.String(32), nullable=False),
        sa.Column("minor_name_snapshot", sa.String(360), nullable=False),
        sa.UniqueConstraint("incident_id", "stay_id", name="uq_incident_stay"),
    )


def downgrade() -> None:
    op.drop_table("incident_participants")
    op.drop_table("incidents")
    op.drop_table("diary_entry_stay_links")
    op.drop_table("diary_entries")
    op.drop_table("diary_days")
