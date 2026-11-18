"""Añade historial de rectificaciones de administraciones de medicación."""
from alembic import op
import sqlalchemy as sa

revision = "0035_medication_administration_versions"
down_revision = "0034_move_sanitary_identity_fields_to_health_profile"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "medication_administration_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("administration_id", sa.String(36), sa.ForeignKey("medication_administrations.id"), nullable=False),
        sa.Column("changed_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("changed_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("old_values", sa.JSON(), nullable=False),
        sa.Column("new_values", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_medication_administration_versions_record_changed",
        "medication_administration_versions", ["administration_id", "changed_at"]
    )


def downgrade():
    op.drop_index(
        "ix_medication_administration_versions_record_changed",
        table_name="medication_administration_versions",
    )
    op.drop_table("medication_administration_versions")
