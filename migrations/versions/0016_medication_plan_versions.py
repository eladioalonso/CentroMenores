"""Añade historial inmutable de pautas de medicación."""
from alembic import op
import sqlalchemy as sa

revision = "0016_medication_plan_versions"
down_revision = "0015_health_profile_versions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "medication_plan_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("medication_plans.id"), nullable=False),
        sa.Column("minor_id", sa.String(36), sa.ForeignKey("minors.id"), nullable=False),
        sa.Column("changed_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("changed_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("old_values", sa.JSON(), nullable=False),
        sa.Column("new_values", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_medication_plan_versions_plan_changed",
        "medication_plan_versions", ["plan_id", "changed_at"],
    )


def downgrade():
    op.drop_index("ix_medication_plan_versions_plan_changed", table_name="medication_plan_versions")
    op.drop_table("medication_plan_versions")
