"""Vincula una administración vacunal con la dosis documental que la identifica."""
from alembic import op
import sqlalchemy as sa

revision = "0025_vaccine_record_calendar_link"
down_revision = "0024_vaccine_calendar_entry_kind"
branch_labels = None
depends_on = None


def upgrade():
    # ADD COLUMN conserva la tabla que ya es referenciada por revisiones de dosis.
    op.add_column(
        "vaccine_records",
        sa.Column(
            "calendar_item_id",
            sa.String(length=36),
            sa.ForeignKey("vaccine_calendar_items.id", name="fk_vaccine_records_calendar_item"),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("vaccine_records", "calendar_item_id")
