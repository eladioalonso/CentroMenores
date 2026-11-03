from datetime import date

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from gestion_centro.auth.models import AccessAudit
from gestion_centro.auth.service import Role, create_professional_account
from gestion_centro.domain.models import Minor
from gestion_centro.domain.service import create_minor, update_minor_personal_data
from gestion_centro.persistence.base import Base


def test_personal_data_update_is_saved_and_audited():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        actor = create_professional_account(session, display_name='Test', username='edit-file',
            password='test password long enough', role=Role.EDUCATOR)
        minor = create_minor(session, actor_account_id=actor.id, internal_code='TEST-EDIT-1',
            given_names='Original', family_names='Name')
        update_minor_personal_data(session, actor_account_id=actor.id, minor_id=minor.id,
            given_names='Corrected', family_names='Name', locality='Lorca',
            nif_nie='x1234567a', email='test@example.test')
        saved = session.get(Minor, minor.id)
        assert saved.given_names == 'Corrected'
        assert saved.nif_nie == 'X1234567A'
        assert saved.locality == 'Lorca'
        assert session.scalar(select(AccessAudit).where(
            AccessAudit.event == 'minor_personal_data_updated')) is not None


def test_personal_data_update_rejects_future_birth_date():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        actor = create_professional_account(session, display_name='Test', username='edit-file-2',
            password='test password long enough', role=Role.EDUCATOR)
        minor = create_minor(session, actor_account_id=actor.id, internal_code='TEST-EDIT-2',
            given_names='Name', family_names='Test')
        with pytest.raises(ValueError, match='nacimiento'):
            update_minor_personal_data(session, actor_account_id=actor.id, minor_id=minor.id,
                given_names='Name', family_names='Test',
                birth_date=date.today().replace(year=date.today().year + 1))
