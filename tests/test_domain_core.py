from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from gestion_centro.auth.service import Role, create_professional_account
from gestion_centro.domain.models import Event, EventStayLink, Stay
from gestion_centro.domain.service import close_stay, create_minor, open_stay, record_event
from gestion_centro.persistence.base import Base


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_minor_has_unique_code_and_only_one_active_stay():
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba", username="p1", password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        minor = create_minor(session, actor_account_id=actor.id, internal_code="MC-2026-0001", given_names="Caso", family_names="Ficticio")
        open_stay(session, actor_account_id=actor.id, minor_id=minor.id, started_on=date(2026, 1, 1))
        with pytest.raises(ValueError, match="estancia activa"):
            open_stay(session, actor_account_id=actor.id, minor_id=minor.id, started_on=date(2026, 2, 1))
        with pytest.raises(ValueError, match="ya existe"):
            create_minor(session, actor_account_id=actor.id, internal_code="mc-2026-0001", given_names="Otro", family_names="Caso")


def test_reentry_creates_new_stay_and_history_is_preserved():
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba", username="p2", password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        minor = create_minor(session, actor_account_id=actor.id, internal_code="MC-2026-0002", given_names="Caso", family_names="Ficticio")
        first = open_stay(session, actor_account_id=actor.id, minor_id=minor.id, started_on=date(2026, 1, 1))
        close_stay(session, actor_account_id=actor.id, stay_id=first.id, ended_on=date(2026, 1, 5), reason="Fin de estancia ficticia")
        second = open_stay(session, actor_account_id=actor.id, minor_id=minor.id, started_on=date(2026, 3, 1))
        assert second.sequence_number == 2
        assert session.scalar(select(Stay).where(Stay.minor_id == minor.id).order_by(Stay.sequence_number)).id == first.id


def test_shared_event_is_one_record_with_multiple_minor_links_and_snapshots():
    with make_session() as session:
        account = create_professional_account(session, display_name="Profesional de prueba",
            username="educador", password="contraseña de prueba segura", role=Role.EDUCATOR)
        first = create_minor(session, actor_account_id=account.id, internal_code="MC-2026-0003", given_names="Caso Uno", family_names="Ficticio")
        second = create_minor(session, actor_account_id=account.id, internal_code="MC-2026-0004", given_names="Caso Dos", family_names="Ficticio")
        stay1 = open_stay(session, actor_account_id=account.id, minor_id=first.id, started_on=date(2026, 1, 1))
        stay2 = open_stay(session, actor_account_id=account.id, minor_id=second.id, started_on=date(2026, 1, 1))
        event = record_event(session, author_account_id=account.id, title="Actividad grupal",
            description="Descripción ficticia", happened_at=datetime.now(timezone.utc),
            stay_ids=[stay1.id, stay2.id])
        assert session.scalar(select(Event.id).where(Event.id == event.id)) == event.id
        links = session.scalars(select(EventStayLink).where(EventStayLink.event_id == event.id)).all()
        assert len(links) == 2
        assert {link.minor_code_snapshot for link in links} == {"MC-2026-0003", "MC-2026-0004"}


def test_event_requires_active_author_and_valid_stays():
    with make_session() as session:
        with pytest.raises(PermissionError):
            record_event(session, author_account_id="missing", title="x", description="y",
                happened_at=datetime.now(timezone.utc), stay_ids=[])


def test_diary_closure_blocks_edits_but_allows_append_only_correction():
    from gestion_centro.domain.models import DiaryEntry
    from gestion_centro.domain.service import close_diary_day, correct_diary_entry, record_diary_entry
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba", username="diary", password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        day = date(2026, 4, 1)
        entry = record_diary_entry(session, actor_account_id=actor.id, diary_date=day,
            shift="morning", category="general", content="Nota ficticia",
            happened_at=datetime(2026, 4, 1, 10, tzinfo=timezone.utc))
        close_diary_day(session, actor_account_id=actor.id, diary_date=day,
            now=datetime(2026, 4, 2, 10, tzinfo=timezone.utc))
        with pytest.raises(ValueError, match="cerrado"):
            record_diary_entry(session, actor_account_id=actor.id, diary_date=day,
                shift="morning", category="general", content="No debe entrar",
                happened_at=datetime(2026, 4, 1, 11, tzinfo=timezone.utc))
        correction = correct_diary_entry(session, actor_account_id=actor.id,
            original_entry_id=entry.id, content="Texto corregido", reason="Aclaración",
            happened_at=datetime(2026, 4, 2, 11, tzinfo=timezone.utc))
        assert correction.correction_of_id == entry.id
        assert session.get(DiaryEntry, entry.id).content == "Nota ficticia"


def test_incident_participants_have_roles_and_auditable_closure_reopening():
    from gestion_centro.domain.models import Incident
    from gestion_centro.domain.service import close_incident, record_incident, reopen_incident
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba", username="incident", password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        minor = create_minor(session, actor_account_id=actor.id, internal_code="MC-2026-0099", given_names="Caso", family_names="Ficticio")
        stay = open_stay(session, actor_account_id=actor.id, minor_id=minor.id, started_on=date(2026, 1, 1))
        happened = datetime(2026, 4, 1, 10, tzinfo=timezone.utc)
        incident = record_incident(session, actor_account_id=actor.id, diary_date=date(2026, 4, 1),
            title="Incidencia ficticia", description="Descripción objetiva", incident_type="safety",
            severity="medium", happened_at=happened, participants=[(stay.id, "witness", "Nota factual")])
        close_incident(session, actor_account_id=actor.id, incident_id=incident.id, note="Seguimiento completado")
        assert session.get(Incident, incident.id).status == "closed"
        reopen_incident(session, actor_account_id=actor.id, incident_id=incident.id, reason="Nueva información")
        assert session.get(Incident, incident.id).status == "open"


def test_diary_auto_closes_at_48_hour_deadline_and_rejects_late_entry():
    from gestion_centro.domain.models import DiaryDay
    from gestion_centro.domain.service import record_diary_entry
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba", username="late-diary",
            password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        day_date = date(2026, 4, 1)
        with pytest.raises(ValueError, match="cerrado"):
            record_diary_entry(session, actor_account_id=actor.id, diary_date=day_date,
                shift="night", category="general", content="Anotación tardía",
                happened_at=datetime(2026, 4, 1, 23, tzinfo=timezone.utc),
                now=datetime(2026, 4, 3, 0, 0, tzinfo=timezone.utc))
        day = session.scalar(select(DiaryDay).where(DiaryDay.diary_date == day_date))
        assert day is not None
        assert day.closed_at == datetime(2026, 4, 3, 0, 0, tzinfo=timezone.utc)
        assert day.closed_by_account_id is None


def test_invalid_diary_participant_does_not_leave_partial_entry():
    from gestion_centro.domain.models import DiaryEntry
    from gestion_centro.domain.service import record_diary_entry
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba", username="atomic-diary",
            password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        with pytest.raises(ValueError, match="no existe"):
            record_diary_entry(session, actor_account_id=actor.id, diary_date=date(2026, 4, 1),
                shift="morning", category="general", content="Nota ficticia",
                happened_at=datetime(2026, 4, 1, 10, tzinfo=timezone.utc), stay_ids=["missing"])
        assert session.scalar(select(DiaryEntry.id)) is None
