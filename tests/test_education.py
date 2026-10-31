from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from gestion_centro.persistence.base import Base
from gestion_centro.auth.models import Professional, UserAccount
from gestion_centro.domain.models import Minor, Stay
from gestion_centro.domain import education as education_models
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
  m=Minor(internal_code="MC-TEST-1",given_names="Caso",family_names="Ficticio"); s.add(m); s.flush()
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
