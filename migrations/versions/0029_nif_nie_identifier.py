"""Establece NIF/NIE como identificador visible del expediente."""
from alembic import op
import sqlalchemy as sa

revision = "0029_nif_nie_identifier"
down_revision = "0028_explicit_health_access"
branch_labels = None
depends_on = None


def upgrade():
    # Los registros históricos conservan una instantánea del identificador visible.
    # Se actualiza a NIF/NIE o pasaporte; la clave técnica heredada permanece oculta.
    for table in (
        "event_stay_links",
        "diary_entry_stay_links",
        "incident_participants",
        "agenda_item_stay_links",
    ):
        op.execute(sa.text(
            f"""
            UPDATE {table}
            SET minor_code_snapshot = COALESCE((
                SELECT COALESCE(NULLIF(m.nif_nie, ''), NULLIF(m.passport_number, ''), '')
                FROM stays AS s
                JOIN minors AS m ON m.id = s.minor_id
                WHERE s.id = {table}.stay_id
            ), '')
            """
        ))

    op.create_index("uq_minors_nif_nie", "minors", ["nif_nie"], unique=True)


def downgrade():
    op.drop_index("uq_minors_nif_nie", table_name="minors")
