"""Informes externos con selección, revisión y entrega auditadas."""
from alembic import op
import sqlalchemy as sa

revision = "0010_external_reports"
down_revision = "0009_medication_shift"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "external_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("stay_id", sa.String(36), sa.ForeignKey("stays.id"), nullable=False),
        sa.Column("authorization_id", sa.String(36), sa.ForeignKey("authorizations.id"), nullable=False),
        sa.Column("recipient", sa.String(180), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("included_fields", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("created_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id")),
        sa.Column("reviewed_by_name_snapshot", sa.String(160)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("delivery_reference", sa.String(180)),
        sa.Column("delivered_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id")),
        sa.Column("delivered_by_name_snapshot", sa.String(160)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_external_reports_stay_status", "external_reports", ["stay_id", "status"])


def downgrade():
    op.drop_index("ix_external_reports_stay_status", table_name="external_reports")
    op.drop_table("external_reports")
