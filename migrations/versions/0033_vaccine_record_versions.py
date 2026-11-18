"""Añade historial de modificaciones a registros vacunales."""
from alembic import op
import sqlalchemy as sa

revision = "0033_vaccine_record_versions"
down_revision = "0032_move_legacy_incidents_into_diary"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vaccine_record_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("vaccine_record_id", sa.String(36), sa.ForeignKey("vaccine_records.id"), nullable=False),
        sa.Column("changed_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("changed_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("old_values", sa.JSON(), nullable=False),
        sa.Column("new_values", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_vaccine_record_versions_record_changed",
        "vaccine_record_versions", ["vaccine_record_id", "changed_at"]
    )


def downgrade():
    op.drop_index("ix_vaccine_record_versions_record_changed", table_name="vaccine_record_versions")
    op.drop_table("vaccine_record_versions")
