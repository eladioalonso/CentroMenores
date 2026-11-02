"""Amplía los datos personales y sanitarios del expediente."""
from alembic import op
import sqlalchemy as sa

revision = "0012_minor_personal_health"
down_revision = "0011_medication_schedules"
branch_labels = None
depends_on = None

def upgrade():
    columns = [
        ("birth_country", sa.String(100)),
        ("locality", sa.String(120)),
        ("nationality", sa.String(100)),
        ("birth_date", sa.Date()),
        ("nif_nie", sa.String(20)),
        ("passport_number", sa.String(40)),
        ("cip", sa.String(40)),
        ("address", sa.Text()),
        ("health_center", sa.String(180)),
        ("physician", sa.String(160)),
        ("nurse", sa.String(160)),
        ("health_card_expires_on", sa.Date()),
        ("clinical_history", sa.Text()),
        ("email", sa.String(254)),
    ]
    for name, column_type in columns:
        op.add_column("minors", sa.Column(name, column_type, nullable=True))

def downgrade():
    for name in reversed(["birth_country","locality","nationality","birth_date","nif_nie",
        "passport_number","cip","address","health_center","physician","nurse",
        "health_card_expires_on","clinical_history","email"]):
        op.drop_column("minors", name)
