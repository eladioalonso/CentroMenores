"""Horarios diarios estructurados para pautas de medicación."""
from alembic import op
import sqlalchemy as sa

revision = "0011_medication_schedules"
down_revision = "0010_external_reports"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "medication_schedules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("medication_plans.id"), nullable=False),
        sa.Column("time_of_day", sa.String(5), nullable=False),
        sa.Column("shift", sa.String(16), nullable=False),
        sa.UniqueConstraint("plan_id", "time_of_day", name="uq_medication_schedule_plan_time"),
    )
    op.create_index("ix_medication_schedules_plan_shift", "medication_schedules", ["plan_id", "shift"])


def downgrade():
    op.drop_index("ix_medication_schedules_plan_shift", table_name="medication_schedules")
    op.drop_table("medication_schedules")
