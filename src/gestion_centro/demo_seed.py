"""Datos y cuenta ficticios precargados exclusivamente en el modo demo."""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from gestion_centro.auth.models import UserAccount
from gestion_centro.auth.service import Role, create_professional_account
from gestion_centro.domain.models import Minor
from gestion_centro.domain.service import (
    create_minor, open_stay, record_diary_entry, record_incident,
)
from gestion_centro.persistence.database import session_scope


DEMO_USERNAME = "educador"
DEMO_PASSWORD = "012345678910"


def seed_demo_data(factory) -> None:
    """Crea una cuenta EDUCADOR y registros de ejemplo de forma idempotente."""
    with session_scope(factory) as session:
        account = session.scalar(
            select(UserAccount).where(UserAccount.username == DEMO_USERNAME)
        )
        if account is None:
            account = create_professional_account(
                session,
                display_name="educador",
                username="EDUCADOR",
                password=DEMO_PASSWORD,
                role=Role.EDUCATOR,
            )
        actor_id = account.id

        examples = [
            ("DEMO-001", "Alex", "Ríos Medina", date(2010, 4, 12), "España", "Melilla"),
            ("DEMO-002", "Samira", "Benali", date(2009, 9, 3), "Marruecos", "Nador"),
            ("DEMO-003", "Daniel", "Santos Vega", date(2012, 1, 27), "España", "Málaga"),
            ("DEMO-004", "Yasmin", "El Amrani", date(2008, 6, 18), "Marruecos", "Tetuán"),
            ("DEMO-005", "Nora", "García León", date(2011, 11, 9), "España", "Granada"),
        ]
        stays = {}
        for code, given, family, born, country, locality in examples:
            minor = session.scalar(select(Minor).where(Minor.internal_code == code))
            if minor is None:
                minor = create_minor(
                    session, actor_account_id=actor_id,
                    internal_code=code, given_names=given, family_names=family,
                    birth_country=country, locality=locality, nationality=country,
                    birth_date=born,
                )
            active_stay = next((s for s in minor.stays if s.status == "active"), None)
            if active_stay is None:
                active_stay = open_stay(
                    session, actor_account_id=actor_id, minor_id=minor.id,
                    started_on=date.today() - timedelta(days=20 + len(stays) * 3),
                )
            stays[code] = active_stay

        now = datetime.now(timezone.utc)
        diary_examples = [
            (0, "morning", "activity", "Actividad de ejemplo: apoyo escolar y organización del espacio común.", "DEMO-001"),
            (1, "afternoon", "positive", "Conducta positiva de ejemplo: colaboración en la actividad grupal.", "DEMO-002"),
            (1, "night", "observation", "Observación ficticia: se realiza el relevo de turno sin incidencias pendientes.", "DEMO-003"),
            (2, "morning", "negative", "Conducta negativa de ejemplo: desacuerdo durante una actividad; se acompaña la resolución dialogada.", "DEMO-004"),
            (2, "afternoon", "general", "Registro general de ejemplo: participación en tareas cotidianas del centro.", "DEMO-005"),
        ]
        for days_ago, shift, category, content, code in diary_examples:
            diary_date = date.today() - timedelta(days=days_ago)
            happened = now - timedelta(days=days_ago, hours=2)
            record_diary_entry(
                session, actor_account_id=actor_id, diary_date=diary_date,
                shift=shift, category=category, content=content,
                happened_at=happened, stay_ids=[stays[code].id], now=now,
            )

        incident_examples = [
            (1, "Desacuerdo durante actividad", "Situación ficticia de convivencia. Se facilita el diálogo y se registra el seguimiento educativo.", "conflict", "low", "DEMO-002"),
            (0, "Daño accidental en material", "Daño ficticio y leve en material de uso común. Se deja constancia para su revisión.", "damage", "low", "DEMO-003"),
            (0, "Incidencia de seguridad de ejemplo", "Situación ficticia revisada por el equipo; queda pendiente completar el seguimiento.", "safety", "medium", "DEMO-004"),
        ]
        for days_ago, title, description, kind, severity, code in incident_examples:
            diary_date = date.today() - timedelta(days=days_ago)
            existing_day = next(
                (d for d in []), None
            )
            # Evita duplicados si se vuelve a iniciar la demo.
            from gestion_centro.domain.models import Incident, DiaryDay, IncidentParticipant
            day = session.scalar(select(DiaryDay).where(DiaryDay.diary_date == diary_date))
            duplicate = session.scalar(
                select(Incident.id).where(
                    Incident.diary_day_id == day.id,
                    Incident.title == title,
                )
            ) if day else None
            if duplicate:
                continue
            record_incident(
                session, actor_account_id=actor_id, diary_date=diary_date,
                title=title, description=description, incident_type=kind,
                severity=severity, happened_at=now - timedelta(days=days_ago, hours=1),
                participants=[(stays[code].id, "involved", "Participación ficticia de ejemplo")],
                now=now,
            )
