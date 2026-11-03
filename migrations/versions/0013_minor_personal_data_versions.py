"""Conserva versiones de los datos personales modificados en expedientes."""
from alembic import op
import sqlalchemy as sa

revision = "0013_minor_personal_data_versions"
down_revision = "0012_minor_personal_health"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "minor_personal_data_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("minor_id", sa.String(length=36), sa.ForeignKey("minors.id"), nullable=False),
        sa.Column("changed_by_account_id", sa.String(length=36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("changed_by_name_snapshot", sa.String(length=160), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("old_values", sa.JSON(), nullable=False),
        sa.Column("new_values", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_minor_personal_data_versions_minor_id",
        "minor_personal_data_versions", ["minor_id"],
    )


def downgrade():
    op.drop_index("ix_minor_personal_data_versions_minor_id", table_name="minor_personal_data_versions")
    op.drop_table("minor_personal_data_versions")
