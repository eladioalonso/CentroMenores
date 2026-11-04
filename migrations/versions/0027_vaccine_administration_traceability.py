"""Amplía la trazabilidad de las administraciones vacunales."""
from alembic import op
import sqlalchemy as sa

revision = "0027_vaccine_administration_traceability"
down_revision = "0026_mark_risk_schedule_entries"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("vaccine_records", sa.Column("manufacturer", sa.String(160), nullable=True))
    op.add_column("vaccine_records", sa.Column("product_name", sa.String(180), nullable=True))
    op.add_column("vaccine_records", sa.Column("batch_number", sa.String(100), nullable=True))
    op.add_column("vaccine_records", sa.Column("administration_center", sa.String(180), nullable=True))
    op.add_column("vaccine_records", sa.Column("administering_professional", sa.String(160), nullable=True))


def downgrade():
    op.drop_column("vaccine_records", "administering_professional")
    op.drop_column("vaccine_records", "administration_center")
    op.drop_column("vaccine_records", "batch_number")
    op.drop_column("vaccine_records", "product_name")
    op.drop_column("vaccine_records", "manufacturer")
