"""Sustituye el código interno del expediente por NIF/NIE."""
from alembic import op
import sqlalchemy as sa

revision = "0029_nif_nie_identifier"
down_revision = "0028_explicit_health_access"
branch_labels = None
depends_on = None


def upgrade():
    # Los registros históricos conservan una instantánea del identificador visible.
    # Se actualiza a NIF/NIE o pasaporte antes de retirar el código interno.
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

    op.drop_column("minors", "internal_code")
    op.create_index("uq_minors_nif_nie", "minors", ["nif_nie"], unique=True)


def downgrade():
    op.drop_index("uq_minors_nif_nie", table_name="minors")
    op.add_column(
        "minors",
        sa.Column("internal_code", sa.String(length=32), nullable=True),
    )
    op.execute(sa.text(
        "UPDATE minors SET internal_code = 'LEGACY-' || substr(id, 1, 8)"
    ))
    # La columna vuelve a ser obligatoria y única para compatibilidad con versiones anteriores.
    with op.batch_alter_table("minors") as batch_op:
        batch_op.alter_column("internal_code", existing_type=sa.String(length=32), nullable=False)
        batch_op.create_unique_constraint("uq_minors_internal_code", ["internal_code"])
