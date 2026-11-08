from datetime import date
import pytest
from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from gestion_centro.persistence.base import Base
from gestion_centro.auth.models import Professional, UserAccount
from gestion_centro.domain.models import Minor, Stay
from gestion_centro.domain.education_service import (
 create_education_goal, add_education_update, set_education_goal_status,
 create_school_placement, add_school_record
)

@pytest.fixture
def edu():
 engine=create_engine("sqlite://")
 Base.metadata.create_all(engine)
 factory=sessionmaker(engine,expire_on_commit=False)
 with factory() as s:
  p=Professional(display_name="Educador"); s.add(p); s.flush()
  a=UserAccount(professional_id=p.id,username="edu",password_hash="x",role="educator"); s.add(a)
  m=Minor(given_names="Caso",family_names="Ficticio"); s.add(m); s.flush()
  stay=Stay(minor_id=m.id,sequence_number=1,started_on=date(2026,1,1),status="active"); s.add(stay); s.flush()
  yield s,a.id,stay.id
 engine.dispose()

def test_education_goal_and_append_only_updates(edu):
 s,actor,stay=edu
 goal=create_education_goal(s,actor_account_id=actor,stay_id=stay,title="Autonomía",description="Objetivo ficticio")
 add_education_update(s,actor_account_id=actor,goal_id=goal.id,category="autonomy",
  objective_description="Preparó sus materiales",actions_taken="Se ofreció apoyo",response_observed="Completó la tarea")
 set_education_goal_status(s,actor_account_id=actor,goal_id=goal.id,status="achieved")
 assert len(goal.updates)==1 and goal.status=="achieved"

def test_school_history_and_date_validation(edu):
 s,actor,stay=edu
 placement=create_school_placement(s,actor_account_id=actor,stay_id=stay,school_name="Centro ficticio",course="2026/27",started_on=date(2026,9,1))
 add_school_record(s,actor_account_id=actor,placement_id=placement.id,record_type="meeting",occurred_on=date(2026,9,10),description="Reunión ficticia")
 with pytest.raises(ValueError):
  add_school_record(s,actor_account_id=actor,placement_id=placement.id,record_type="attendance",occurred_on=date(2026,8,1),description="Fuera de periodo")


def test_author_can_rectify_own_education_update_without_overwriting_original(edu):
 s,actor,stay=edu
 goal=create_education_goal(s,actor_account_id=actor,stay_id=stay,title="Autonomía",description="Objetivo ficticio")
 original=add_education_update(s,actor_account_id=actor,goal_id=goal.id,category="autonomy",
  objective_description="Observación original",actions_taken="Apoyo inicial",response_observed="Respuesta inicial")
 from gestion_centro.domain.education_service import revise_education_update
 correction=revise_education_update(s,actor_account_id=actor,update_id=original.id,
  objective_description="Observación corregida",actions_taken="Apoyo corregido",response_observed="Respuesta corregida")
 assert original.objective_description=="Observación original"
 assert correction.author_account_id==actor
 assert correction.objective_description.startswith(f"RECTIFICACIÓN de la actualización {original.id}:")



def test_other_professional_cannot_rectify_education_update(edu):
 s,actor,stay=edu
 goal=create_education_goal(s,actor_account_id=actor,stay_id=stay,title="Convivencia",description="Objetivo ficticio")
 original=add_education_update(s,actor_account_id=actor,goal_id=goal.id,category="coexistence",
  objective_description="Observación original",actions_taken="Apoyo",response_observed="Respuesta")
 other_prof=Professional(display_name="Otro educador")
 s.add(other_prof); s.flush()
 other_account=UserAccount(professional_id=other_prof.id,username="otro",password_hash="x",role="educator")
 s.add(other_account); s.flush()
 from gestion_centro.domain.education_service import revise_education_update
 with pytest.raises(PermissionError):
  revise_education_update(s,actor_account_id=other_account.id,update_id=original.id,
   objective_description="Intento ajeno",actions_taken="Cambio",response_observed="Cambio")
 assert original.objective_description=="Observación original"



def test_education_and_school_read_services_require_actor_and_audit(edu):
 s,actor,stay=edu
 from gestion_centro.auth.models import AccessAudit
 from gestion_centro.domain.education_service import (
  list_education_goals, list_school_placements, list_school_records,
 )
 assert list_education_goals(s,actor_account_id=actor,stay_id=stay)==[]
 assert list_school_placements(s,actor_account_id=actor,stay_id=stay)==[]
 placement=create_school_placement(s,actor_account_id=actor,stay_id=stay,
  school_name="Centro ficticio",course="2026/27",started_on=date(2026,9,1))
 add_school_record(s,actor_account_id=actor,placement_id=placement.id,
  record_type="meeting",occurred_on=date(2026,9,2),description="Registro ficticio")
 assert len(list_school_records(s,actor_account_id=actor,placement_id=placement.id))==1
 events={e.event for e in s.scalars(select(AccessAudit)).all()}
 assert "education_goals_accessed" in events
 assert "school_history_accessed" in events
 assert "school_records_accessed" in events
 with pytest.raises(PermissionError):
  list_education_goals(s,actor_account_id="cuenta-inexistente",stay_id=stay)
 with pytest.raises(PermissionError):
  list_school_records(s,actor_account_id="cuenta-inexistente",placement_id=placement.id)
