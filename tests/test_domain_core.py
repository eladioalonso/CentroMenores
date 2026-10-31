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
        minor = create_minor(session, internal_code="MC-2026-0001", given_names="Caso", family_names="Ficticio")
        open_stay(session, minor_id=minor.id, started_on=date(2026, 1, 1))
        with pytest.raises(ValueError, match="estancia activa"):
            open_stay(session, minor_id=minor.id, started_on=date(2026, 2, 1))
        with pytest.raises(ValueError, match="ya existe"):
            create_minor(session, internal_code="mc-2026-0001", given_names="Otro", family_names="Caso")


def test_reentry_creates_new_stay_and_history_is_preserved():
    with make_session() as session:
        minor = create_minor(session, internal_code="MC-2026-0002", given_names="Caso", family_names="Ficticio")
        first = open_stay(session, minor_id=minor.id, started_on=date(2026, 1, 1))
        close_stay(session, stay_id=first.id, ended_on=date(2026, 1, 5), reason="Fin de estancia ficticia")
        second = open_stay(session, minor_id=minor.id, started_on=date(2026, 3, 1))
        assert second.sequence_number == 2
        assert session.scalar(select(Stay).where(Stay.minor_id == minor.id).order_by(Stay.sequence_number)).id == first.id


def test_shared_event_is_one_record_with_multiple_minor_links_and_snapshots():
    with make_session() as session:
        account = create_professional_account(session, display_name="Profesional de prueba",
            username="educador", password="contraseña de prueba segura", role=Role.EDUCATOR)
        first = create_minor(session, internal_code="MC-2026-0003", given_names="Caso Uno", family_names="Ficticio")
        second = create_minor(session, internal_code="MC-2026-0004", given_names="Caso Dos", family_names="Ficticio")
        stay1 = open_stay(session, minor_id=first.id, started_on=date(2026, 1, 1))
        stay2 = open_stay(session, minor_id=second.id, started_on=date(2026, 1, 1))
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
