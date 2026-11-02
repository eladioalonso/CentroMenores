from datetime import date, datetime, timezone
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from gestion_centro.persistence.base import Base
from gestion_centro.auth.models import Professional, UserAccount, AccessAudit
from gestion_centro.domain.models import Minor, Stay
from gestion_centro.domain import health as health_models
from gestion_centro.domain.health_service import save_health_profile, read_health_profile, add_medication_plan, record_medication_administration

@pytest.fixture
def health_case():
 engine=create_engine("sqlite://"); Base.metadata.create_all(engine); factory=sessionmaker(engine,expire_on_commit=False)
 with factory() as s:
  p=Professional(display_name="Educador"); s.add(p); s.flush()
  a=UserAccount(professional_id=p.id,username="health-edu",password_hash="x",role="educator"); s.add(a)
  m=Minor(internal_code="MC-HEALTH-TEST",given_names="Caso",family_names="Ficticio"); s.add(m); s.flush()
  stay=Stay(minor_id=m.id,sequence_number=1,started_on=date(2026,1,1),status="active"); s.add(stay); s.flush()
  yield s,a.id,stay.id
 engine.dispose()

def test_health_access_is_audited_and_medication_results_are_explicit(health_case):
 s,actor,stay=health_case
 save_health_profile(s,actor_account_id=actor,stay_id=stay,allergies="Dato ficticio",relevant_conditions=None,emergency_instructions="Avisar al responsable sanitario")
 assert read_health_profile(s,actor_account_id=actor,stay_id=stay).allergies=="Dato ficticio"
 plan=add_medication_plan(s,actor_account_id=actor,stay_id=stay,medication_name="Producto ficticio",
  prescribed_dose="Según documento",schedule_text="08:00",prescriber_reference="Documento clínico ficticio",starts_on=date(2026,1,1))
 with pytest.raises(ValueError):
  record_medication_administration(s,actor_account_id=actor,plan_id=plan.id,scheduled_at=datetime(2026,1,2,8,tzinfo=timezone.utc),status="refused")
 record_medication_administration(s,actor_account_id=actor,plan_id=plan.id,scheduled_at=datetime(2026,1,2,8,tzinfo=timezone.utc),status="refused",note="Rechazo comunicado")
 assert len(s.scalars(select(AccessAudit)).all())>=4

def test_daily_medication_schedule_shows_pending_and_recorded_doses(health_case):
 s,actor,stay=health_case
 plan=add_medication_plan(s,actor_account_id=actor,stay_id=stay,medication_name="Producto ficticio",
  prescribed_dose="1 unidad",schedule_text="Pauta indicada",prescriber_reference="Prescripción ficticia",starts_on=date(2026,1,1))
 set_medication_schedules(s,actor_account_id=actor,plan_id=plan.id,schedules=[("08:00","morning"),("20:00","night")])
 rows=list_daily_medication_schedule(s,actor_account_id=actor,stay_id=stay,day=date(2026,1,2))
 assert len(rows)==2
 assert all(record is None for _,_,_,record in rows)
 record_medication_administration(s,actor_account_id=actor,plan_id=plan.id,
  scheduled_at=datetime(2026,1,2,8,tzinfo=timezone.utc),status="administered",shift="morning")
 rows=list_daily_medication_schedule(s,actor_account_id=actor,stay_id=stay,day=date(2026,1,2))
 assert sum(record is not None for _,_,_,record in rows)==1

def test_medication_schedule_rejects_invalid_or_duplicate_times(health_case):
 s,actor,stay=health_case
 plan=add_medication_plan(s,actor_account_id=actor,stay_id=stay,medication_name="Producto ficticio",
  prescribed_dose="1 unidad",schedule_text="Pauta indicada",prescriber_reference="Prescripción ficticia",starts_on=date(2026,1,1))
 with pytest.raises(ValueError):
  set_medication_schedules(s,actor_account_id=actor,plan_id=plan.id,schedules=[("25:00","morning")])
 with pytest.raises(ValueError):
  set_medication_schedules(s,actor_account_id=actor,plan_id=plan.id,schedules=[("08:00","morning"),("08:00","night")])