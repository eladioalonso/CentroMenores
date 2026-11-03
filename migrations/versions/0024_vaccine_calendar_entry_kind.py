"""Distingue las filas de dosis de las secuencias documentales de rescate."""
from uuid import NAMESPACE_URL, uuid5

from alembic import op
import sqlalchemy as sa

revision = "0024_vaccine_calendar_entry_kind"
down_revision = "0023_expand_vaccine_dose_label"
branch_labels = None
depends_on = None

ACCELERATED_EDITION_ID = str(uuid5(NAMESPACE_URL, "melilla-accelerated-2025"))


def upgrade():
    with op.batch_alter_table("vaccine_calendar_items") as batch_op:
        batch_op.add_column(
            sa.Column("entry_kind", sa.String(length=16), nullable=False, server_default="dose")
        )
    # El calendario acelerado se almacena como secuencia completa por grupo de edad,
    # no como una fila por dosis individual.
    op.execute(
        sa.text(
            "UPDATE vaccine_calendar_items SET entry_kind = 'schedule' "
            "WHERE edition_id = :edition_id"
        ).bindparams(edition_id=ACCELERATED_EDITION_ID)
    )


def downgrade():
    with op.batch_alter_table("vaccine_calendar_items") as batch_op:
        batch_op.drop_column("entry_kind")
