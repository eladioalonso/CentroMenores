"""Carga documental del calendario acelerado de Melilla 2025."""
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from alembic import op
import sqlalchemy as sa

revision = "0021_melilla_accelerated_vaccination_2025"
down_revision = "0020_melilla_adult_vaccine_catalog_2026"
branch_labels = None
depends_on = None

EDITION_KEY = "melilla-accelerated-2025"
EDITION_ID = str(uuid5(NAMESPACE_URL, EDITION_KEY))
SOURCE_URL = "https://melilla.es/melillaPortal/RecursosWeb/DOCUMENTOS/1/4_30756_1.pdf"

# Transcripción resumida de las tablas 1-4 del documento MELILLA 2025.
# Se conserva como material documental; no calcula pautas ni sustituye valoración sanitaria.
ITEMS = [
    ("ACC-U7-DTPA", "Difteria, tétanos y tosferina (DTPa)", "Visitas 0, 2 y 8 meses; recuerdo al menos 6 meses después de la última primovacunación", "Menores de 7 años", "catch_up", "Pauta 2+1 indicada en el documento. Según edad de inicio puede corresponder otro recuerdo preescolar. Consultar tabla 1 y nota (1).", "2"),
    ("ACC-U7-VPI", "Poliomielitis inactivada (VPI)", "Visitas 0, 2 y 8 meses", "Menores de 7 años", "catch_up", "Si la tercera dosis se administra después de los 4 años, el documento indica que no es necesaria una cuarta dosis. Consultar nota (2).", "2"),
    ("ACC-U7-HIB", "Haemophilus influenzae tipo b (Hib)", "Visitas 0, 2 y 8 meses, según edad de inicio", "Menores de 7 años", "catch_up", "El número de dosis depende de la edad: durante el primer año, 2 dosis de primovacunación y recuerdo; entre 1 y 5 años, una dosis; desde los 5 años no se recomienda salvo grupos de riesgo. Nota (3).", "2"),
    ("ACC-U7-HB", "Hepatitis B (HB)", "Hexavalente: 0, 2 y 8 meses; monovalente: 0, 1 y 6 meses", "Menores de 7 años", "catch_up", "La secuencia depende del preparado utilizado. Nota (4).", "2"),
    ("ACC-U7-HA", "Hepatitis A (HA)", "Inicio si >15 meses; referencia de segunda dosis a los 8 meses desde primera visita", "Menores de 7 años", "catch_up", "El documento refleja HA en primera visita para mayores de 15 meses y otra dosis desde los 6 meses; revisar la tabla y antecedentes. No automatizar.", "2"),
    ("ACC-U7-TV", "Triple vírica (TV)", "Visitas 0 y 1 mes", "Menores de 7 años", "catch_up", "Dos dosis desde los 12 meses, separadas 4 semanas o ajustadas al calendario oficial según edad. Nota (5).", "2"),
    ("ACC-U7-MENB", "Meningococo B (MenB)", "Visitas 0 y 2 meses; recuerdo según edad", "Menores de 7 años", "catch_up", "El número de dosis y el recuerdo dependen de la edad de inicio; consultar tabla 1 y recomendaciones específicas.", "2"),
    ("ACC-U7-MENACWY", "Meningococo ACWY (MenACWY)", "Primera visita y recuerdo según edad", "Menores de 7 años", "catch_up", "Entre 4 y 12 meses, el documento señala una dosis de primovacunación con condiciones específicas y recuerda valorar dosis posteriores; mayores de 12 meses, una dosis de primovacunación. Nota (6).", "2"),
    ("ACC-U7-VNC", "Neumococo conjugada (VNC)", "Visitas 0 y 2 meses, según edad", "Menores de 7 años", "catch_up", "Pauta dependiente de edad: menores de 12 meses según calendario; 12-23 meses, dos dosis separadas al menos 8 semanas; mayores de 2 años, una dosis según el documento. Nota (7).", "2"),
    ("ACC-U7-VVZ", "Varicela (VVZ)", "Visitas 0 y 1 mes", "Menores de 7 años", "catch_up", "Solo si no hay antecedentes fiables de enfermedad ni vacunación previa; dos dosis separadas al menos 4 semanas (preferiblemente 8) o ajuste al calendario vigente. Nota (8).", "2"),
    ("ACC-7-18-TD", "Tétanos-difteria (Td)", "Visitas 0, 1 y 8 meses; completar hasta 5 dosis", "7-18 años", "catch_up", "La tercera dosis se administra entre 6 y 12 meses después de la segunda. Después de primovacunación, recuerdos cada 10 años según condiciones e intervalos mínimos del documento. Al menos una dosis con dTpa en niños y adolescentes. Nota (1).", "3"),
    ("ACC-7-18-VPI", "Poliomielitis inactivada (VPI)", "Visitas 0, 1 y 8 meses cuando esté indicada", "7-18 años", "catch_up", "La necesidad de 1 o 3 dosis depende de antecedentes y país de procedencia; consultar nota (3) y valoración profesional.", "3"),
    ("ACC-7-18-HB", "Hepatitis B (HB)", "Visitas 0, 1 y 6 meses", "7-18 años", "catch_up", "La tabla refleja tres visitas; confirmar antecedentes y situación individual.", "3"),
    ("ACC-7-18-HA", "Hepatitis A (HA)", "Visitas 0 y 6 meses", "7-18 años", "catch_up", "Confirmar indicación y antecedentes antes de valorar la pauta.", "3"),
    ("ACC-7-18-TV", "Triple vírica (TV)", "Visitas 0 y 1 mes", "7-18 años", "catch_up", "Dos dosis separadas al menos 4 semanas si no hay documentación previa ni antecedente de enfermedad; si existe una dosis previa, el documento indica completar con una. Nota (4).", "3"),
    ("ACC-7-18-MENACWY", "Meningococo ACWY (MenACWY)", "Una dosis; recuerdo según edad", "7-18 años", "catch_up", "Entre 7 y 12 años, una dosis y recuerdo a los 12 años; por encima de 12 años, una dosis. Nota (5).", "3"),
    ("ACC-7-18-VVZ", "Varicela (VVZ)", "Visitas 0 y 1 mes", "7-18 años", "catch_up", "Dos dosis separadas al menos 4 semanas (preferiblemente 8) si no existe evidencia de enfermedad; puede utilizarse tetravírica cuando también corresponda TV. Nota (6).", "3"),
    ("ACC-7-18-VPH", "Virus del papiloma humano (VPH)", "Una dosis de rescate", "12-18 años", "catch_up", "El documento de Melilla 2025 recoge una dosis en adolescentes desde los 12 hasta los 18 años. Verificar versión posterior y situación individual. Nota (7).", "3"),
    ("ACC-AD-TV", "Triple vírica (TV)", "Visitas 0 y 1 mes", "Mayores de 18 años", "catch_up", "Recomendada en personas nacidas en España desde 1970 sin historia documentada y personas no nacidas en España sin documentación previa. Dos dosis con intervalo mínimo de 4 semanas; si ya recibió una, una dosis adicional. Nota (1).", "4"),
    ("ACC-AD-TD", "Tétanos-difteria (Td)", "Visitas 0, 1 y 8 meses; completar hasta 5 dosis", "Mayores de 18 años", "catch_up", "La tercera dosis entre 6 y 12 meses después de la segunda; recuerdos hasta 5 dosis totales. Tras primovacunación, dos recuerdos separados 10 años, con los mínimos descritos. Nota (2).", "4"),
    ("ACC-AD-VPI", "Poliomielitis inactivada (VPI)", "Visitas 0, 1 y 8 meses cuando esté indicada", "Mayores de 18 años", "catch_up", "El número de dosis depende del país de procedencia y del riesgo de circulación o reintroducción del poliovirus. Nota (3).", "4"),
    ("ACC-AD-HB", "Hepatitis B (HB)", "Visitas 0, 1 y 6 meses", "Mayores de 18 años", "catch_up", "En grupos de riesgo y personas procedentes de países de alta endemia, valorar marcadores serológicos; vacunación si procede. Nota (4).", "4"),
    ("ACC-AD-HA", "Hepatitis A (HA)", "Visitas 0 y 6 meses", "Mayores de 18 años", "catch_up", "El documento incluye HA en la tabla; confirmar indicación de riesgo y antecedentes.", "4"),
    ("ACC-AD-VVZ", "Varicela (VVZ)", "Visitas 0 y 1 mes si procede", "Mayores de 18 años", "catch_up", "Valorar serología IgG si no hay antecedentes ni dos dosis documentadas; si serología negativa, dos dosis con intervalo mínimo de 4 semanas (preferiblemente 8); completar si ya recibió una. Nota (5).", "4"),
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
        "id": EDITION_ID, "jurisdiction": "Melilla", "edition_code": "2025-acelerado",
        "title": "Calendario de vacunación acelerada de Melilla 2025",
        "effective_from": __import__("datetime").date(2025, 1, 1),
        "effective_until": __import__("datetime").date(2025, 12, 31),
        "source_title": "Ciudad Autónoma de Melilla · Dirección General de Salud Pública",
        "source_reference": "MELILLA 2025, Tablas 1-4, pp. 1-4",
        "source_url": SOURCE_URL, "verified_at": None, "status": "documentary",
        "created_at": now,
    }])
    op.bulk_insert(items_table, [{
        "id": str(uuid5(NAMESPACE_URL, f"{EDITION_KEY}:{code}")),
        "edition_id": EDITION_ID, "vaccine_code": code, "display_name": name,
        "dose_label": schedule, "target_age_text": age, "category": category,
        "documentary_note": note, "source_page": page,
    } for code, name, schedule, age, category, note, page in ITEMS])


def downgrade():
    op.execute(sa.text("DELETE FROM vaccine_calendar_items WHERE edition_id = :edition_id").bindparams(edition_id=EDITION_ID))
    op.execute(sa.text("DELETE FROM vaccine_calendar_editions WHERE id = :edition_id").bindparams(edition_id=EDITION_ID))
