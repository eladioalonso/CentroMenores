"""Añade historial inmutable de versiones de la ficha sanitaria general."""
from alembic import op
import sqlalchemy as sa

revision = "0015_health_profile_versions"
down_revision = "0014_health_records_belong_to_minor"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "health_profile_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("minor_id", sa.String(36), sa.ForeignKey("minors.id"), nullable=False),
        sa.Column("profile_id", sa.String(36), nullable=False),
        sa.Column("changed_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("changed_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("old_values", sa.JSON(), nullable=False),
        sa.Column("new_values", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_health_profile_versions_minor_changed",
        "health_profile_versions", ["minor_id", "changed_at"],
    )


def downgrade():
    op.drop_index("ix_health_profile_versions_minor_changed", table_name="health_profile_versions")
    op.drop_table("health_profile_versions")
