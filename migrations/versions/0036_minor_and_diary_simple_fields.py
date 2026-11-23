"""Añade campos simplificados de ficha del menor y parte diario por turnos."""
from alembic import op
import sqlalchemy as sa

revision = "0036_minor_and_diary_simple_fields"
down_revision = "0035_medication_administration_versions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("minors", sa.Column("sex", sa.String(24), nullable=True))
    op.add_column("minors", sa.Column("postal_code", sa.String(12), nullable=True))
    op.add_column("minors", sa.Column("mobile_phone", sa.String(30), nullable=True))
    op.add_column("minors", sa.Column("health_card_issued_on", sa.Date(), nullable=True))
    for name in (
        "morning_staff", "afternoon_staff", "night_staff",
        "morning_activities", "afternoon_activities", "night_activities",
    ):
        op.add_column("diary_days", sa.Column(name, sa.Text(), nullable=True))


def downgrade():
    for name in (
        "night_activities", "afternoon_activities", "morning_activities",
        "night_staff", "afternoon_staff", "morning_staff",
    ):
        op.drop_column("diary_days", name)
    op.drop_column("minors", "health_card_issued_on")
    op.drop_column("minors", "mobile_phone")
    op.drop_column("minors", "postal_code")
    op.drop_column("minors", "sex")
