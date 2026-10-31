"""Registro sanitario, pautas prescritas y administración."""
from alembic import op
import sqlalchemy as sa
revision="0007_health"
down_revision="0006_education_schooling"
branch_labels=None
depends_on=None

def upgrade():
 op.create_table("health_profiles",
  sa.Column("id",sa.String(36),primary_key=True),sa.Column("stay_id",sa.String(36),sa.ForeignKey("stays.id"),nullable=False,unique=True),
  sa.Column("allergies",sa.Text()),sa.Column("relevant_conditions",sa.Text()),sa.Column("emergency_instructions",sa.Text()),
  sa.Column("updated_by_account_id",sa.String(36),sa.ForeignKey("user_accounts.id"),nullable=False),
  sa.Column("updated_by_name_snapshot",sa.String(160),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
 op.create_table("medication_plans",
  sa.Column("id",sa.String(36),primary_key=True),sa.Column("stay_id",sa.String(36),sa.ForeignKey("stays.id"),nullable=False),
  sa.Column("medication_name",sa.String(180),nullable=False),sa.Column("prescribed_dose",sa.String(120),nullable=False),
  sa.Column("schedule_text",sa.String(240),nullable=False),sa.Column("instructions",sa.Text()),
  sa.Column("prescriber_reference",sa.String(180),nullable=False),sa.Column("starts_on",sa.Date(),nullable=False),
  sa.Column("ends_on",sa.Date()),sa.Column("active",sa.Boolean(),nullable=False),
  sa.Column("recorded_by_account_id",sa.String(36),sa.ForeignKey("user_accounts.id"),nullable=False),
  sa.Column("recorded_by_name_snapshot",sa.String(160),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
 op.create_index("ix_medication_plans_stay_active","medication_plans",["stay_id","active"])
 op.create_table("medication_administrations",
  sa.Column("id",sa.String(36),primary_key=True),sa.Column("plan_id",sa.String(36),sa.ForeignKey("medication_plans.id"),nullable=False),
  sa.Column("scheduled_at",sa.DateTime(timezone=True),nullable=False),sa.Column("status",sa.String(20),nullable=False),
  sa.Column("note",sa.Text()),sa.Column("recorded_by_account_id",sa.String(36),sa.ForeignKey("user_accounts.id"),nullable=False),
  sa.Column("recorded_by_name_snapshot",sa.String(160),nullable=False),sa.Column("recorded_at",sa.DateTime(timezone=True),nullable=False))
 op.create_table("vaccine_records",
  sa.Column("id",sa.String(36),primary_key=True),sa.Column("stay_id",sa.String(36),sa.ForeignKey("stays.id"),nullable=False),
  sa.Column("vaccine_name",sa.String(180),nullable=False),sa.Column("administered_on",sa.Date(),nullable=False),
  sa.Column("dose_reference",sa.String(80)),sa.Column("source_document_id",sa.String(36)),
  sa.Column("recorded_by_account_id",sa.String(36),sa.ForeignKey("user_accounts.id"),nullable=False),
  sa.Column("recorded_by_name_snapshot",sa.String(160),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))

def downgrade():
 op.drop_table("vaccine_records"); op.drop_table("medication_administrations")
 op.drop_index("ix_medication_plans_stay_active",table_name="medication_plans")
 op.drop_table("medication_plans"); op.drop_table("health_profiles")
