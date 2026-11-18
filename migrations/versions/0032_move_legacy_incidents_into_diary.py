"""Integra incidencias históricas en la cronología del parte diario."""
from uuid import uuid4
from alembic import op
import sqlalchemy as sa

revision = "0032_move_legacy_incidents_into_diary"
down_revision = "0031_incident_report_version_metadata"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    incidents = connection.execute(sa.text("""
        SELECT id, diary_day_id, title, description, incident_type, severity,
               happened_at, recorded_at, author_account_id, author_name_snapshot,
               status, closure_note, closed_at
        FROM incidents
        ORDER BY happened_at, recorded_at, id
    """)).mappings().all()
    for incident in incidents:
        existing_entries = connection.execute(sa.text("""
            SELECT content FROM diary_entries WHERE diary_day_id = :diary_day_id
        """), {"diary_day_id": incident["diary_day_id"]}).scalars().all()
        title_key = (incident["title"] or "").strip().casefold()
        description_key = (incident["description"] or "").strip().casefold()
        already_documented = any(
            (title_key and title_key in (content or "").casefold())
            or (description_key and description_key in (content or "").casefold())
            for content in existing_entries
        )
        if already_documented:
            # El parte ya contiene este hecho; se conserva la incidencia formal
            # antigua como histórico, sin duplicar el acontecimiento.
            continue
        entry_id = str(uuid4())
        category = (
            "health" if incident["incident_type"] == "health"
            else "negative" if incident["incident_type"] in {"behavior", "conflict"}
            else "observation"
        )
        participants = connection.execute(sa.text("""
            SELECT stay_id, role, factual_note, minor_code_snapshot, minor_name_snapshot
            FROM incident_participants WHERE incident_id = :incident_id
        """), {"incident_id": incident["id"]}).mappings().all()
        participant_text = "\\n".join(
            f"Participante ({item['role']}): {item['minor_name_snapshot']} "
            f"{'· ' + item['factual_note'] if item['factual_note'] else ''}"
            for item in participants
        )
        closure_text = (
            f"Estado histórico: {incident['status']}. Cierre: {incident['closure_note']}"
            if incident["closure_note"] else f"Estado histórico: {incident['status']}"
        )
        content = (
            f"Incidencia histórica: {incident['title']}\\n"
            f"Tipo: {incident['incident_type']} · Gravedad: {incident['severity']}\\n"
            f"{incident['description']}\\n{closure_text}"
            f"{'\\n' + participant_text if participant_text else ''}"
        )
        connection.execute(sa.text("""
            INSERT INTO diary_entries (
                id, diary_day_id, shift, category, content, happened_at, recorded_at,
                author_account_id, author_name_snapshot, correction_of_id
            ) VALUES (
                :id, :diary_day_id, 'unspecified', :category, :content, :happened_at,
                :recorded_at, :author_account_id, :author_name_snapshot, NULL
            )
        """), {
            "id": entry_id, "diary_day_id": incident["diary_day_id"],
            "category": category, "content": content,
            "happened_at": incident["happened_at"], "recorded_at": incident["recorded_at"],
            "author_account_id": incident["author_account_id"],
            "author_name_snapshot": incident["author_name_snapshot"],
        })
        for participant in participants:
            connection.execute(sa.text("""
                INSERT INTO diary_entry_stay_links (
                    id, entry_id, stay_id, minor_code_snapshot, minor_name_snapshot
                ) VALUES (:id, :entry_id, :stay_id, :minor_code, :minor_name)
            """), {
                "id": str(uuid4()), "entry_id": entry_id,
                "stay_id": participant["stay_id"],
                "minor_code": participant["minor_code_snapshot"],
                "minor_name": participant["minor_name_snapshot"],
            })


def downgrade():
    # No se eliminan las anotaciones migradas: hacerlo podría borrar cambios
    # posteriores realizados por los educadores sobre esos hechos históricos.
    pass
