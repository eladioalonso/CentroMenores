"""Vincula una administración vacunal con su dosis documental mediante integridad SQLite."""
from alembic import op
import sqlalchemy as sa

revision = "0025_vaccine_record_calendar_link"
down_revision = "0024_vaccine_calendar_entry_kind"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite no permite añadir una FK con ALTER COLUMN. La tabla vaccine_records
    # ya recibe referencias desde vaccine_dose_reviews, por lo que reconstruirla
    # con batch mode sería arriesgado. Los triggers aplican la misma integridad.
    op.add_column(
        "vaccine_records",
        sa.Column("calendar_item_id", sa.String(length=36), nullable=True),
    )
    op.execute("""
        CREATE TRIGGER trg_vaccine_record_calendar_insert
        BEFORE INSERT ON vaccine_records
        WHEN NEW.calendar_item_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM vaccine_calendar_items WHERE id = NEW.calendar_item_id)
        BEGIN
            SELECT RAISE(ABORT, 'vaccine calendar item does not exist');
        END
    """)
    op.execute("""
        CREATE TRIGGER trg_vaccine_record_calendar_update
        BEFORE UPDATE OF calendar_item_id ON vaccine_records
        WHEN NEW.calendar_item_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM vaccine_calendar_items WHERE id = NEW.calendar_item_id)
        BEGIN
            SELECT RAISE(ABORT, 'vaccine calendar item does not exist');
        END
    """)
    op.execute("""
        CREATE TRIGGER trg_vaccine_calendar_item_delete
        BEFORE DELETE ON vaccine_calendar_items
        WHEN EXISTS (SELECT 1 FROM vaccine_records WHERE calendar_item_id = OLD.id)
        BEGIN
            SELECT RAISE(ABORT, 'vaccine calendar item is referenced by an administration');
        END
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_vaccine_calendar_item_delete")
    op.execute("DROP TRIGGER IF EXISTS trg_vaccine_record_calendar_update")
    op.execute("DROP TRIGGER IF EXISTS trg_vaccine_record_calendar_insert")
    op.drop_column("vaccine_records", "calendar_item_id")
