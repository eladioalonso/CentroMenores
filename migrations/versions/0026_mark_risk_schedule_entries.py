"""Marca como secuencias las referencias de grupos de riesgo con pautas múltiples o variables."""
from alembic import op
import sqlalchemy as sa

revision = "0026_mark_risk_schedule_entries"
down_revision = "0025_vaccine_record_calendar_link"
branch_labels = None
depends_on = None

SCHEDULE_CODES = [
    "TD-AD", "TV-AD", "VVZ-AD", "HZ-AD", "HA-AD", "HB-AD", "VPH-AD",
    "RISK-I-DTP", "RISK-I-TV", "RISK-I-HB", "RISK-I-HA", "RISK-I-MEN",
    "RISK-I-VPH", "RISK-I-VVZ", "RISK-I-VN", "RISK-I-RV", "RISK-I-GRIPE",
    "RISK-I-COVID", "RISK-I-VRS",
    "RISK-A-TD", "RISK-A-HB", "RISK-A-TV", "RISK-A-HA", "RISK-A-VVZ",
    "RISK-A-MEN", "RISK-A-HZ", "RISK-A-VPH", "RISK-A-VN",
    "RISK-A-GRIPE", "RISK-A-COVID", "RISK-A-VRS",
]


def upgrade():
    placeholders = ", ".join(f":code_{index}" for index in range(len(SCHEDULE_CODES)))
    params = {f"code_{index}": code for index, code in enumerate(SCHEDULE_CODES)}
    op.execute(
        sa.text(
            "UPDATE vaccine_calendar_items SET entry_kind = 'schedule' "
            f"WHERE vaccine_code IN ({placeholders})"
        ).bindparams(**params)
    )


def downgrade():
    placeholders = ", ".join(f":code_{index}" for index in range(len(SCHEDULE_CODES)))
    params = {f"code_{index}": code for index, code in enumerate(SCHEDULE_CODES)}
    op.execute(
        sa.text(
            "UPDATE vaccine_calendar_items SET entry_kind = 'dose' "
            f"WHERE vaccine_code IN ({placeholders})"
        ).bindparams(**params)
    )
