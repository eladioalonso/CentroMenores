from sqlalchemy import create_engine, func, select

from gestion_centro.auth.models import UserAccount
from gestion_centro.auth.service import AuthStatus, authenticate
from gestion_centro.demo_seed import DEMO_PASSWORD, seed_demo_data
from gestion_centro.domain.models import DiaryEntry, Incident, Minor, Stay
from gestion_centro.persistence.base import Base
from gestion_centro.persistence.database import build_session_factory, session_scope


def test_demo_seed_creates_educator_and_fictional_records_idempotently():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)
    try:
        seed_demo_data(factory)
        seed_demo_data(factory)

        with session_scope(factory) as session:
            account = session.scalar(
                select(UserAccount).where(UserAccount.username == "educador")
            )
            assert account is not None
            assert account.professional.display_name == "educador"
            assert account.role == "educator"
            assert account.health_access is False
            assert session.scalar(select(func.count()).select_from(Minor)) == 5
            assert session.scalar(select(func.count()).select_from(Stay)) == 5
            assert session.scalar(select(func.count()).select_from(DiaryEntry)) == 3
            assert session.scalar(select(func.count()).select_from(Incident)) == 3
            result = authenticate(
                session, username="EDUCADOR", password=DEMO_PASSWORD
            )
            assert result.status is AuthStatus.SUCCESS
            assert result.role.value == "educator"
    finally:
        engine.dispose()
