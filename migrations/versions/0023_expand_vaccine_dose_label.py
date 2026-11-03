"""Amplía la longitud de la descripción de dosis para secuencias documentales."""
from alembic import op
import sqlalchemy as sa

revision = "0023_expand_vaccine_dose_label"
down_revision = "0022_sns_risk_calendars_2026"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("vaccine_calendar_items") as batch_op:
        batch_op.alter_column(
            "dose_label",
            existing_type=sa.String(length=80),
            type_=sa.String(length=240),
            existing_nullable=False,
        )


def downgrade():
    # El downgrade puede truncar datos si ya se han añadido secuencias largas.
    with op.batch_alter_table("vaccine_calendar_items") as batch_op:
        batch_op.alter_column(
            "dose_label",
            existing_type=sa.String(length=240),
            type_=sa.String(length=80),
            existing_nullable=False,
        )
