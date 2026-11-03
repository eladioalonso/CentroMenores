"""Carga documental inicial del calendario infantil Melilla 2026."""
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from alembic import op
import sqlalchemy as sa

revision = "0018_melilla_vaccine_catalog_2026"
down_revision = "0017_vaccine_calendar_reviews"
branch_labels = None
depends_on = None

EDITION_KEY = "melilla-calendar-2026-infantil"
EDITION_ID = str(uuid5(NAMESPACE_URL, EDITION_KEY))
SOURCE_URL = "https://bomemelilla.es/bome/descargar/BOME-A-2025-1322.pdf"

# Datos transcritos del Anexo I, BOME 6335, pp. 4167-4168.
# Son referencias documentales: no expresan indicación individual ni producto comercial.
ITEMS = [
    ("dTpa", "Difteria, tétanos y tosferina (dTpa)", "Gestación semanas 28-36", "Prenatal", "systematic", "Vacunación durante el embarazo; confirmar indicación y antecedentes.", "4167"),
    ("GRIPE-GEST", "Gripe (vacuna antigripal)", "Campaña estacional", "Embarazo", "campaign", "Vacuna intramuscular durante la gestación, según campaña.", "4167"),
    ("HB-NEO", "Hepatitis B (HB) neonatal", "Dosis neonatal condicionada", "0 meses", "systematic", "Supuesto específico de la nota (a), incluida madre portadora; validar pauta sanitaria.", "4167"),
    ("VPI-1", "Poliomielitis inactivada (VPI)", "Dosis 1", "2 meses", "systematic", None, "4167"),
    ("DTPA-1", "Difteria, tétanos y tosferina acelular (DTPa)", "Dosis 1", "2 meses", "systematic", None, "4167"),
    ("HIB-1", "Haemophilus influenzae tipo b (Hib)", "Dosis 1", "2 meses", "systematic", None, "4167"),
    ("HB-1", "Hepatitis B (HB)", "Dosis 1", "2 meses", "systematic", None, "4167"),
    ("MENB-1", "Meningococo B (MenB)", "Dosis 1", "2 meses", "systematic", None, "4167"),
    ("NEUMO-1", "Neumococo", "Dosis 1", "2 meses", "systematic", None, "4167"),
    ("ROTA-1", "Rotavirus", "Dosis 1", "2 meses", "systematic", "El número total de dosis depende del preparado.", "4167"),
    ("VPI-2", "Poliomielitis inactivada (VPI)", "Dosis 2", "4 meses", "systematic", None, "4167"),
    ("DTPA-2", "Difteria, tétanos y tosferina acelular (DTPa)", "Dosis 2", "4 meses", "systematic", None, "4167"),
    ("HIB-2", "Haemophilus influenzae tipo b (Hib)", "Dosis 2", "4 meses", "systematic", None, "4167"),
    ("HB-2", "Hepatitis B (HB)", "Dosis 2", "4 meses", "systematic", None, "4167"),
    ("MENACWY-1", "Meningococo ACWY (MenACWY)", "Dosis indicada a los 4 meses", "4 meses", "systematic", None, "4167"),
    ("MENB-2", "Meningococo B (MenB)", "Dosis 2", "4 meses", "systematic", None, "4167"),
    ("NEUMO-2", "Neumococo", "Dosis 2", "4 meses", "systematic", None, "4167"),
    ("ROTA-2", "Rotavirus", "Dosis 2", "4 meses", "systematic", "El número total de dosis depende del preparado.", "4167"),
    ("NEUMO-3", "Neumococo", "Dosis 3", "6 meses", "systematic", None, "4167"),
    ("ROTA-3", "Rotavirus", "Dosis 3 condicionada", "6 meses", "systematic", "Solo si el preparado utilizado requiere pauta de tres dosis (nota b).", "4167"),
    ("VPI-3", "Poliomielitis inactivada (VPI)", "Dosis 3", "11 meses", "systematic", None, "4167"),
    ("DTPA-3", "Difteria, tétanos y tosferina acelular (DTPa)", "Dosis 3", "11 meses", "systematic", None, "4167"),
    ("HIB-3", "Haemophilus influenzae tipo b (Hib)", "Dosis 3", "11 meses", "systematic", None, "4167"),
    ("HB-3", "Hepatitis B (HB)", "Dosis 3", "11 meses", "systematic", None, "4167"),
    ("NEUMO-4", "Neumococo", "Dosis 4", "11 meses", "systematic", None, "4167"),
    ("TV-1", "Triple vírica (sarampión, rubéola y parotiditis)", "Dosis 1", "12 meses", "systematic", None, "4167"),
    ("MENACWY-2", "Meningococo ACWY (MenACWY)", "Dosis indicada a los 12 meses", "12 meses", "systematic", None, "4167"),
    ("MENB-3", "Meningococo B (MenB)", "Dosis 3", "12 meses", "systematic", None, "4167"),
    ("HA-1", "Hepatitis A", "Dosis 1", "15 meses", "systematic", None, "4167"),
    ("VAR-1", "Varicela", "Dosis 1", "15 meses", "systematic", None, "4167"),
    ("HA-2", "Hepatitis A", "Dosis 2", "24 meses", "systematic", None, "4167"),
    ("TVV-2", "Tetravírica (sarampión, rubéola, parotiditis y varicela)", "Dosis 2 combinada", "3 años", "systematic", "En 2026 agrupa la segunda dosis de triple vírica y varicela (nota c).", "4167"),
    ("VPI-4", "Poliomielitis inactivada (VPI)", "Dosis 4", "6 años", "systematic", None, "4168"),
    ("DTPA-4", "Difteria, tétanos y tosferina acelular (DTPa)", "Dosis 4", "6 años", "systematic", None, "4168"),
    ("MENACWY-12", "Meningococo ACWY (MenACWY)", "Dosis indicada a los 12 años", "12 años", "systematic", None, "4168"),
    ("VPH", "Virus del papiloma humano (VPH)", "Pauta según calendario", "12 años", "systematic", "El número de dosis no se codifica aquí; validar pauta individual.", "4168"),
    ("VAR-12", "Varicela", "Dos dosis si susceptible", "12 años", "systematic", "Solo si no ha pasado la enfermedad ni ha sido vacunado (nota d); confirmar antecedentes.", "4168"),
    ("TD-5", "Tétanos y difteria (Td)", "Dosis 5", "14 años", "systematic", None, "4168"),
    ("GRIPE-6-24", "Gripe (vacuna intramuscular)", "Campaña estacional", "6-24 meses", "campaign", "El anexo 2026 indica vía intramuscular para este grupo (nota f).", "4168"),
    ("GRIPE-24-17", "Gripe (intranasal o intramuscular)", "Campaña estacional", "24 meses-17 años", "campaign", "Vía según edad, preparado y campaña (nota f); no inferir producto.", "4168"),
    ("VRS-MAB", "Inmunización pasiva frente al VRS (anticuerpo monoclonal)", "Campaña 1 octubre-31 marzo", "Menores de 12 meses", "passive_immunization", "No es una vacuna convencional. Aplican las condiciones de la nota (e) y validación sanitaria.", "4168"),
]


def upgrade():
    now = datetime.now(timezone.utc)
    editions = sa.table(
        "vaccine_calendar_editions",
        sa.column("id", sa.String), sa.column("jurisdiction", sa.String),
        sa.column("edition_code", sa.String), sa.column("title", sa.String),
        sa.column("effective_from", sa.Date), sa.column("effective_until", sa.Date),
        sa.column("source_title", sa.String), sa.column("source_reference", sa.String),
        sa.column("source_url", sa.String), sa.column("verified_at", sa.DateTime),
        sa.column("status", sa.String), sa.column("created_at", sa.DateTime),
    )
    items_table = sa.table(
        "vaccine_calendar_items",
        sa.column("id", sa.String), sa.column("edition_id", sa.String),
        sa.column("vaccine_code", sa.String), sa.column("display_name", sa.String),
        sa.column("dose_label", sa.String), sa.column("target_age_text", sa.String),
        sa.column("category", sa.String), sa.column("documentary_note", sa.Text),
        sa.column("source_page", sa.String),
    )
    op.bulk_insert(editions, [{
        "id": EDITION_ID, "jurisdiction": "Melilla", "edition_code": "2026-infantil",
        "title": "Calendario infantil de vacunación e inmunización de Melilla 2026",
        "effective_from": __import__("datetime").date(2026, 1, 1), "effective_until": None,
        "source_title": "Orden n.º 3567, de 9 de diciembre de 2025, BOME n.º 6335",
        "source_reference": "Artículo 1322, Anexo I, pp. 4167-4168",
        "source_url": SOURCE_URL, "verified_at": None, "status": "documentary",
        "created_at": now,
    }])
    op.bulk_insert(items_table, [{
        "id": str(uuid5(NAMESPACE_URL, f"{EDITION_KEY}:{code}:{dose}:{age}")),
        "edition_id": EDITION_ID, "vaccine_code": code, "display_name": name,
        "dose_label": dose, "target_age_text": age, "category": category,
        "documentary_note": note, "source_page": page,
    } for code, name, dose, age, category, note, page in ITEMS])


def downgrade():
    op.execute(sa.text("DELETE FROM vaccine_calendar_items WHERE edition_id = :edition_id").bindparams(edition_id=EDITION_ID))
    op.execute(sa.text("DELETE FROM vaccine_calendar_editions WHERE id = :edition_id").bindparams(edition_id=EDITION_ID))
