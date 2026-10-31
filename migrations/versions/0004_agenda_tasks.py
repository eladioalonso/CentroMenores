"""Añade agenda común y tareas con asignación individual o de equipo."""

from alembic import op
import sqlalchemy as sa

revision = "0004_agenda_tasks"
down_revision = "0003_diary_incidents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agenda_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("assignment_scope", sa.String(16), nullable=False),
        sa.Column("assigned_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=True),
        sa.Column("created_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("created_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=True),
    )
    op.create_index("ix_agenda_items_starts_at", "agenda_items", ["starts_at"])
    op.create_index("ix_agenda_items_status", "agenda_items", ["status"])
    op.create_table(
        "agenda_item_stay_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("agenda_item_id", sa.String(36), sa.ForeignKey("agenda_items.id"), nullable=False),
        sa.Column("stay_id", sa.String(36), sa.ForeignKey("stays.id"), nullable=False),
        sa.Column("minor_code_snapshot", sa.String(32), nullable=False),
        sa.Column("minor_name_snapshot", sa.String(360), nullable=False),
        sa.UniqueConstraint("agenda_item_id", "stay_id", name="uq_agenda_item_stay"),
    )


def downgrade() -> None:
    op.drop_table("agenda_item_stay_links")
    op.drop_index("ix_agenda_items_status", table_name="agenda_items")
    op.drop_index("ix_agenda_items_starts_at", table_name="agenda_items")
    op.drop_table("agenda_items")
