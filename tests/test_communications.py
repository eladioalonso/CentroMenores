from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from gestion_centro.persistence.base import Base
from gestion_centro.auth.models import Professional, UserAccount
from gestion_centro.auth.service import hash_password, Role
from gestion_centro.domain.communications import CommunicationContribution
from gestion_centro.domain.communications_service import (
    create_communication, add_communication_contribution, close_communication,
    reopen_communication, move_communication_to_trash, restore_communication,
    stale_communications,
)

@pytest.fixture
def comm_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as session:
        p1=Professional(display_name="Educador uno"); p2=Professional(display_name="Admin")
        session.add_all([p1,p2]); session.flush()
        a1=UserAccount(professional_id=p1.id,username="edu",password_hash="x",role="educator")
        a2=UserAccount(professional_id=p2.id,username="admin",password_hash="x",role="admin")
        session.add_all([a1,a2]); session.flush()
        yield session, a1.id, a2.id
    engine.dispose()

def test_shared_append_only_close_and_admin_reopen(comm_session):
    s, edu, admin = comm_session
    item=create_communication(s,actor_account_id=edu,title="Entrega",content="Pendiente revisar")
    add_communication_contribution(s,actor_account_id=admin,communication_id=item.id,content="Revisado")
    assert len(item.contributions)==2
    close_communication(s,actor_account_id=edu,communication_id=item.id,reason="Fin de turno")
    with pytest.raises(ValueError):
        add_communication_contribution(s,actor_account_id=edu,communication_id=item.id,content="Tarde")
    reopen_communication(s,actor_account_id=admin,communication_id=item.id,reason="Añadir dato")
    assert item.status=="draft"

def test_trash_owner_and_admin_restore(comm_session):
    s, edu, admin=comm_session
    item=create_communication(s,actor_account_id=edu,title="Aviso",content="Texto")
    move_communication_to_trash(s,actor_account_id=edu,communication_id=item.id)
    with pytest.raises(PermissionError):
        restore_communication(s,actor_account_id=edu,communication_id=item.id)
    restore_communication(s,actor_account_id=admin,communication_id=item.id)
    assert item.deleted_at is None

def test_stale_notice_after_seven_days(comm_session):
    s, edu, _=comm_session
    item=create_communication(s,actor_account_id=edu,title="Aviso",content="Texto")
    old=datetime.now(timezone.utc)+timedelta(days=8)
    assert item in stale_communications(s,now=old)


def test_author_can_rectify_own_contribution_without_overwriting_original(comm_session):
    s, edu, admin = comm_session
    item = create_communication(s, actor_account_id=edu, title="Entrega", content="Texto inicial")
    original = item.contributions[0]
    from gestion_centro.domain.communications_service import revise_communication_contribution
    with pytest.raises(PermissionError):
        revise_communication_contribution(s, actor_account_id=admin,
            contribution_id=original.id, corrected_content="Cambio ajeno")
    correction = revise_communication_contribution(s, actor_account_id=edu,
        contribution_id=original.id, corrected_content="Texto corregido")
    assert original.content == "Texto inicial"
    assert correction.author_account_id == edu
    assert correction.content.startswith(f"RECTIFICACIÓN de la aportación {original.id}:")
    close_communication(s, actor_account_id=edu, communication_id=item.id, reason="Cierre")
    with pytest.raises(ValueError):
        revise_communication_contribution(s, actor_account_id=edu,
            contribution_id=original.id, corrected_content="Demasiado tarde")
