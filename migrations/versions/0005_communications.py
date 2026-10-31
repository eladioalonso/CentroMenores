"""Comunicaciones compartidas con aportaciones inmutables."""
from alembic import op
import sqlalchemy as sa
revision = "0005_communications"
down_revision = "0004_agenda_tasks"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("communications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("created_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("closed_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id")))
    op.create_index("ix_communications_status_updated", "communications", ["status", "updated_at"])
    op.create_table("communication_contributions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("communication_id", sa.String(36), sa.ForeignKey("communications.id"), nullable=False),
        sa.Column("author_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("author_name_snapshot", sa.String(160), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))

def downgrade() -> None:
    op.drop_table("communication_contributions")
    op.drop_index("ix_communications_status_updated", table_name="communications")
    op.drop_table("communications")
