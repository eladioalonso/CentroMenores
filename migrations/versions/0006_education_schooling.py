"""Seguimiento educativo y escolaridad."""
from alembic import op
import sqlalchemy as sa
revision = "0006_education_schooling"
down_revision = "0005_communications"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("education_goals",
        sa.Column("id",sa.String(36),primary_key=True),sa.Column("stay_id",sa.String(36),sa.ForeignKey("stays.id"),nullable=False),
        sa.Column("title",sa.String(180),nullable=False),sa.Column("description",sa.Text(),nullable=False),
        sa.Column("target_date",sa.Date()),sa.Column("status",sa.String(16),nullable=False),
        sa.Column("created_by_account_id",sa.String(36),sa.ForeignKey("user_accounts.id"),nullable=False),
        sa.Column("created_by_name_snapshot",sa.String(160),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_education_goals_stay_status","education_goals",["stay_id","status"])
    op.create_table("education_updates",
        sa.Column("id",sa.String(36),primary_key=True),sa.Column("goal_id",sa.String(36),sa.ForeignKey("education_goals.id"),nullable=False),
        sa.Column("category",sa.String(32),nullable=False),sa.Column("objective_description",sa.Text(),nullable=False),
        sa.Column("actions_taken",sa.Text(),nullable=False),sa.Column("response_observed",sa.Text(),nullable=False),
        sa.Column("follow_up",sa.Text()),sa.Column("author_account_id",sa.String(36),sa.ForeignKey("user_accounts.id"),nullable=False),
        sa.Column("author_name_snapshot",sa.String(160),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_table("school_placements",
        sa.Column("id",sa.String(36),primary_key=True),sa.Column("stay_id",sa.String(36),sa.ForeignKey("stays.id"),nullable=False),
        sa.Column("school_name",sa.String(180),nullable=False),sa.Column("course",sa.String(80),nullable=False),
        sa.Column("started_on",sa.Date(),nullable=False),sa.Column("ended_on",sa.Date()),sa.Column("notes",sa.Text()),
        sa.Column("created_by_account_id",sa.String(36),sa.ForeignKey("user_accounts.id"),nullable=False),
        sa.Column("created_by_name_snapshot",sa.String(160),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_table("school_records",
        sa.Column("id",sa.String(36),primary_key=True),sa.Column("placement_id",sa.String(36),sa.ForeignKey("school_placements.id"),nullable=False),
        sa.Column("record_type",sa.String(24),nullable=False),sa.Column("occurred_on",sa.Date(),nullable=False),
        sa.Column("description",sa.Text(),nullable=False),sa.Column("author_account_id",sa.String(36),sa.ForeignKey("user_accounts.id"),nullable=False),
        sa.Column("author_name_snapshot",sa.String(160),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))

def downgrade():
    op.drop_table("school_records"); op.drop_table("school_placements")
    op.drop_table("education_updates"); op.drop_index("ix_education_goals_stay_status",table_name="education_goals")
    op.drop_table("education_goals")
