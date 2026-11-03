"""Vincula una administración vacunal con la dosis documental que la identifica."""
from alembic import op
import sqlalchemy as sa

revision = "0025_vaccine_record_calendar_link"
down_revision = "0024_vaccine_calendar_entry_kind"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("vaccine_records") as batch_op:
        batch_op.add_column(sa.Column("calendar_item_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_vaccine_records_calendar_item",
            "vaccine_calendar_items",
            ["calendar_item_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("vaccine_records") as batch_op:
        batch_op.drop_constraint("fk_vaccine_records_calendar_item", type_="foreignkey")
        batch_op.drop_column("calendar_item_id")
