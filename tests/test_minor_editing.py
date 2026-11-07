from datetime import date

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from gestion_centro.auth.models import AccessAudit
from gestion_centro.auth.service import Role, create_professional_account
from gestion_centro.domain.models import Minor, MinorPersonalDataVersion
from gestion_centro.domain.service import create_minor, update_minor_personal_data
from gestion_centro.persistence.base import Base


def test_personal_data_update_is_saved_and_audited():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        actor = create_professional_account(session, display_name='Test', username='edit-file',
            password='test password long enough', role=Role.EDUCATOR)
        actor.health_access = True
        minor = create_minor(session, actor_account_id=actor.id, internal_code='TEST-EDIT-1',
            given_names='Original', family_names='Name')
        update_minor_personal_data(session, actor_account_id=actor.id, minor_id=minor.id,
            given_names='Corrected', family_names='Name', locality='Lorca',
            nif_nie='x1234567a', email='test@example.test', cip='cip-123',
            health_center='Centro ficticio', physician='Facultativo ficticio',
            nurse='Enfermera ficticia', health_card_expires_on=date(2027, 5, 1),
            clinical_history='Historial ficticio')
        saved = session.get(Minor, minor.id)
        assert saved.given_names == 'Corrected'
        assert saved.nif_nie == 'X1234567A'
        assert saved.locality == 'Lorca'
        assert saved.cip == 'CIP-123'
        assert saved.health_center == 'Centro ficticio'
        assert saved.physician == 'Facultativo ficticio'
        assert saved.nurse == 'Enfermera ficticia'
        assert saved.health_card_expires_on == date(2027, 5, 1)
        assert saved.clinical_history == 'Historial ficticio'
        version = session.scalar(select(MinorPersonalDataVersion).where(
            MinorPersonalDataVersion.minor_id == minor.id))
        assert version is not None
        assert version.old_values['given_names'] == 'Original'
        assert version.new_values['given_names'] == 'Corrected'
        assert version.old_values['nif_nie'] is None
        assert version.new_values['nif_nie'] == 'X1234567A'
        assert version.new_values['clinical_history'] == 'Historial ficticio'
        assert version.old_values['clinical_history'] is None
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

def test_personal_data_update_without_health_access_cannot_read_or_change_health_fields():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        actor = create_professional_account(session, display_name='Test', username='edit-no-health',
            password='test password long enough', role=Role.EDUCATOR)
        authorized = create_professional_account(session, display_name='Health', username='edit-health',
            password='test password long enough', role=Role.EDUCATOR)
        authorized.health_access = True
        minor = create_minor(session, actor_account_id=authorized.id, internal_code='TEST-EDIT-3',
            given_names='Name', family_names='Test', clinical_history='Dato clínico ficticio')
        with pytest.raises(PermissionError, match='autorización sanitaria'):
            update_minor_personal_data(session, actor_account_id=actor.id, minor_id=minor.id,
                given_names='Name', family_names='Test', clinical_history=None)
        # Omitir los campos sanitarios permite corregir los identificativos sin borrarlos.
        update_minor_personal_data(session, actor_account_id=actor.id, minor_id=minor.id,
            given_names='Corrected', family_names='Test')
        assert session.get(Minor, minor.id).clinical_history == 'Dato clínico ficticio'


def test_creating_minor_with_health_data_requires_health_access():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        actor = create_professional_account(session, display_name='Test', username='create-no-health',
            password='test password long enough', role=Role.EDUCATOR)
        with pytest.raises(PermissionError, match='autorización sanitaria'):
            create_minor(session, actor_account_id=actor.id, internal_code='TEST-EDIT-4',
                given_names='Name', family_names='Test', clinical_history='Dato clínico ficticio')

