"""Turno asociado a cada administración de medicación."""
from alembic import op
import sqlalchemy as sa

revision = "0009_medication_shift"
down_revision = "0008_documents_authorizations_outings"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("medication_administrations", sa.Column("shift", sa.String(16), nullable=False, server_default="unspecified"))
    op.create_index("ix_medication_admin_shift_time", "medication_administrations", ["shift", "scheduled_at"])


def downgrade():
    op.drop_index("ix_medication_admin_shift_time", table_name="medication_administrations")
    op.drop_column("medication_administrations", "shift")
