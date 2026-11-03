"""Carga documental del calendario vacunal del adulto de Melilla 2026."""
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from alembic import op
import sqlalchemy as sa

revision = "0020_melilla_adult_vaccine_catalog_2026"
down_revision = "0019_vaccine_review_history"
branch_labels = None
depends_on = None

EDITION_KEY = "melilla-calendar-2026-adulto"
EDITION_ID = str(uuid5(NAMESPACE_URL, EDITION_KEY))
SOURCE_URL = "https://bomemelilla.es/bome/descargar/BOME-A-2025-1322.pdf"

# Transcripción documental de la tabla "Calendario Vacunal del Adulto 2026",
# BOME 6335, página 4168. No constituye una pauta clínica individual.
ITEMS = [
    ("GRIPE-AD", "Gripe", "1 dosis anual", "Adultos según indicación", "campaign",
     "Personas con indicación médica (grupos de riesgo), ocupacional o epidemiológica. También 1 dosis anual en todas las personas de 60 años o más. En embarazadas, cualquier trimestre; también puerperio hasta 6 meses si no se vacunaron."),
    ("NEUMO-VNC20-65", "Enfermedad neumocócica (VNC20)", "Dosis única", "65 años o más", "systematic",
     "Una dosis de VNC20. Si recibió VNP23 antes de los 65 años, respetar al menos 5 años de intervalo según la tabla oficial."),
    ("NEUMO-VNC20-RIESGO", "Enfermedad neumocócica (VNC20)", "Una dosis según valoración", "Desde 18 años con condiciones de riesgo", "risk",
     "La tabla cita inmunodeprimidos, fístulas de LCR, implantes cocleares, asplenia, enfermedad hepática crónica y antecedentes de enfermedad neumocócica invasora confirmada. Si recibió VNP23, intervalo mínimo de un año."),
    ("NEUMO-VNC20-OTROS", "Enfermedad neumocócica (VNC20)", "Una dosis tras valoración clínica", "Inmunocompetentes con otras patologías de riesgo", "risk",
     "La tabla oficial indica valoración clínica y una dosis de VNC20; no automatizar la clasificación de patologías."),
    ("NEUMO-VNP23-65", "Enfermedad neumocócica (VNP23)", "Una dosis", "65 años o más en instituciones o con indicación médica", "risk",
     "Mantener separada de VNC20: la tabla del BOME incluye esta indicación adicional para residentes en instituciones o personas con indicación médica."),
    ("TD-AD", "Tétanos-difteria (Td)", "Completar hasta 5 dosis; recuerdo a los 65 años", "Adultos", "systematic",
     "Completar vacunación hasta 5 dosis si está ausente o incompleta. Una dosis de recuerdo a los 65 años."),
    ("DTPA-GEST", "Tosferina (dTpa)", "Una dosis", "Embarazo, tercer trimestre", "risk",
     "La tabla del adulto de Melilla 2026 indica una dosis en embarazadas en el tercer trimestre."),
    ("TV-AD", "Triple vírica (TV)", "Completar hasta 2 dosis; intervalo mínimo 4 semanas", "Personas nacidas desde 1970 sin vacunación documentada", "risk",
     "Completar hasta dos dosis en personas sin documentación de vacunación; confirmar susceptibilidad y antecedentes."),
    ("VVZ-AD", "Varicela (VVZ)", "Dos dosis; intervalo mínimo 4 semanas (preferible 8)", "Personas seronegativas con indicación médica o no vacunadas", "risk",
     "La tabla exige valoración de susceptibilidad; no deducirla por ausencia de registro."),
    ("HZ-AD", "Herpes zóster", "Dos dosis; intervalo mínimo 8 semanas", "60 años o más; y desde 18 años en grupos de riesgo/tratamientos inmunosupresores", "risk",
     "La indicación por edad y condiciones de riesgo debe confirmarse con la recomendación clínica vigente."),
    ("MEN-AD", "Meningococo B y ACWY", "Una dosis según indicación", "Personas con indicación médica o epidemiológica", "risk",
     "No inferir indicación ni necesidad de dosis adicionales; consultar recomendaciones específicas."),
    ("HIB-AD", "Haemophilus influenzae b (Hib)", "Una dosis según indicación", "Personas con indicación médica", "risk",
     "La tabla del adulto de Melilla 2026 recoge una dosis en personas con indicación médica."),
    ("HA-AD", "Hepatitis A (HAV)", "Dos dosis; 0 y 6 meses", "Personas con indicación médica, ocupacional o epidemiológica", "risk",
     "La tabla del adulto de Melilla 2026 recoge dos dosis separadas 6 meses."),
    ("HB-AD", "Hepatitis B (HBV)", "Tres dosis 0-1-6; o 3/4 según preparado", "Personas con indicación médica, ocupacional o epidemiológica", "risk",
     "En insuficiencia renal, hepática o inmunosupresión, el número de dosis depende del tipo de vacuna y de la valoración sanitaria."),
    ("VPH-AD", "Virus del papiloma humano (VPH)", "Pautas diferenciadas por indicación", "Rescate hasta 18 años; CIN2+; inmunodepresión hasta 45; HSH/prostitución hasta 25", "risk",
     "La tabla detalla: una dosis de rescate hasta 18 años en no vacunados de ambos sexos; tres dosis en mujeres en tratamiento por lesión cervical intraepitelial de alto grado CIN2 o superior a cualquier edad; tres dosis en inmunodepresión hasta 45 años; dos dosis en hombres que tienen sexo con hombres y/o situación de prostitución hasta 25 años incluidos. Validar pauta individual."),
    ("VRS-AD", "Virus respiratorio sincitial (VRS)", "Una dosis", "60+ institucionalizados; 18+ muy alto riesgo; 50+ alto riesgo; 75+", "risk",
     "Orden 3567/2025: una dosis en ≥60 residentes de centros de mayores y discapacidad; ≥18 con condiciones de muy alto riesgo; ≥50 con patologías de alto riesgo; y ≥75 años. Confirmar solapamientos y elegibilidad con profesional sanitario."),
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
        "id": EDITION_ID, "jurisdiction": "Melilla", "edition_code": "2026-adulto",
        "title": "Calendario vacunal del adulto de Melilla 2026",
        "effective_from": __import__("datetime").date(2026, 1, 1), "effective_until": None,
        "source_title": "Orden n.º 3567, de 9 de diciembre de 2025, BOME n.º 6335",
        "source_reference": "Artículo 1322, Anexo II, p. 4168",
        "source_url": SOURCE_URL, "verified_at": None, "status": "documentary",
        "created_at": now,
    }])
    op.bulk_insert(items_table, [{
        "id": str(uuid5(NAMESPACE_URL, f"{EDITION_KEY}:{code}")),
        "edition_id": EDITION_ID, "vaccine_code": code, "display_name": name,
        "dose_label": dose, "target_age_text": age, "category": category,
        "documentary_note": note, "source_page": "4168",
    } for code, name, dose, age, category, note in ITEMS])


def downgrade():
    op.execute(sa.text("DELETE FROM vaccine_calendar_items WHERE edition_id = :edition_id").bindparams(edition_id=EDITION_ID))
    op.execute(sa.text("DELETE FROM vaccine_calendar_editions WHERE id = :edition_id").bindparams(edition_id=EDITION_ID))
