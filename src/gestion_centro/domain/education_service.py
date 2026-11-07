"""Servicios de seguimiento educativo y escolaridad con trazabilidad."""
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from gestion_centro.auth.models import AccessAudit, UserAccount
from gestion_centro.domain.models import Stay
from gestion_centro.domain.education import EducationGoal, EducationUpdate, SchoolPlacement, SchoolRecord

GOAL_STATUSES = {"active", "achieved", "paused", "closed"}
EDUCATION_CATEGORIES = {"autonomy", "coexistence", "emotional", "social", "learning", "health_habits", "other"}
SCHOOL_RECORD_TYPES = {"attendance", "behavior", "meeting", "task", "achievement", "other"}

def _actor(session: Session, account_id: str) -> UserAccount:
    actor=session.get(UserAccount, account_id)
    if actor is None or not actor.active or not actor.professional.active:
        raise PermissionError("Se requiere una cuenta y un profesional activos")
    return actor

def _audit(session: Session, actor: UserAccount, event: str, details: str):
    session.add(AccessAudit(account_id=actor.id, username_snapshot=actor.username, event=event, details=details))

def _active_stay(session: Session, stay_id: str) -> Stay:
    stay=session.get(Stay, stay_id)
    if stay is None or stay.status != "active":
        raise ValueError("La estancia no existe o está cerrada")
    return stay

def create_education_goal(session: Session, *, actor_account_id: str, stay_id: str,
                          title: str, description: str, target_date: date | None = None):
    actor=_actor(session, actor_account_id); _active_stay(session, stay_id)
    if not title.strip() or not description.strip():
        raise ValueError("El objetivo y su descripción son obligatorios")
    goal=EducationGoal(stay_id=stay_id,title=title.strip(),description=description.strip(),
        target_date=target_date,status="active",created_by_account_id=actor.id,
        created_by_name_snapshot=actor.professional.display_name)
    session.add(goal); session.flush()
    _audit(session,actor,"education_goal_created",goal.id)
    return goal

def add_education_update(session: Session, *, actor_account_id: str, goal_id: str,
                         category: str, objective_description: str, actions_taken: str,
                         response_observed: str, follow_up: str | None = None):
    actor=_actor(session,actor_account_id); goal=session.get(EducationGoal,goal_id)
    if goal is None: raise ValueError("El objetivo no existe")
    if category not in EDUCATION_CATEGORIES: raise ValueError("Categoría educativa no válida")
    if not all(x.strip() for x in (objective_description,actions_taken,response_observed)):
        raise ValueError("Describe objetivamente la observación, actuación y respuesta")
    update=EducationUpdate(goal_id=goal.id,category=category,
        objective_description=objective_description.strip(),actions_taken=actions_taken.strip(),
        response_observed=response_observed.strip(),follow_up=follow_up.strip() if follow_up else None,
        author_account_id=actor.id,author_name_snapshot=actor.professional.display_name)
    session.add(update); session.flush()
    _audit(session,actor,"education_update_added",f"{goal.id}:{update.id}")
    return update

def set_education_goal_status(session: Session, *, actor_account_id: str, goal_id: str, status: str):
    actor=_actor(session,actor_account_id); goal=session.get(EducationGoal,goal_id)
    if goal is None: raise ValueError("El objetivo no existe")
    if status not in GOAL_STATUSES: raise ValueError("Estado de objetivo no válido")
    goal.status=status
    _audit(session,actor,"education_goal_status_changed",f"{goal.id}:{status}")
    return goal

def create_school_placement(session: Session, *, actor_account_id: str, stay_id: str,
                            school_name: str, course: str, started_on: date,
                            notes: str | None = None):
    actor=_actor(session,actor_account_id); _active_stay(session,stay_id)
    if not school_name.strip() or not course.strip(): raise ValueError("Centro y curso son obligatorios")
    placement=SchoolPlacement(stay_id=stay_id,school_name=school_name.strip(),course=course.strip(),
        started_on=started_on,notes=notes.strip() if notes else None,
        created_by_account_id=actor.id,created_by_name_snapshot=actor.professional.display_name)
    session.add(placement); session.flush()
    _audit(session,actor,"school_placement_created",placement.id)
    return placement

def end_school_placement(session: Session, *, actor_account_id: str,
                         placement_id: str, ended_on: date):
    actor = _actor(session, actor_account_id)
    placement = session.get(SchoolPlacement, placement_id)
    if placement is None:
        raise ValueError("La escolarización no existe")
    if placement.ended_on is not None:
        raise ValueError("La escolarización ya tiene fecha de finalización")
    if ended_on < placement.started_on:
        raise ValueError("La fecha de finalización no puede preceder al inicio")
    placement.ended_on = ended_on
    session.flush()
    _audit(session, actor, "school_placement_ended", f"{placement.id}:{ended_on.isoformat()}")
    return placement


def add_school_record(session: Session, *, actor_account_id: str, placement_id: str,
                      record_type: str, occurred_on: date, description: str):
    actor=_actor(session,actor_account_id); placement=session.get(SchoolPlacement,placement_id)
    if placement is None: raise ValueError("La escolarización no existe")
    if record_type not in SCHOOL_RECORD_TYPES: raise ValueError("Tipo de registro escolar no válido")
    if not description.strip(): raise ValueError("La descripción es obligatoria")
    if occurred_on < placement.started_on or (placement.ended_on and occurred_on > placement.ended_on):
        raise ValueError("La fecha queda fuera del periodo de escolarización")
    record=SchoolRecord(placement_id=placement.id,record_type=record_type,occurred_on=occurred_on,
        description=description.strip(),author_account_id=actor.id,
        author_name_snapshot=actor.professional.display_name)
    session.add(record); session.flush()
    _audit(session,actor,"school_record_added",f"{placement.id}:{record.id}")
    return record

def list_education_goals(session: Session, *, actor_account_id: str, stay_id: str):
    actor = _actor(session, actor_account_id)
    if session.get(Stay, stay_id) is None:
        raise ValueError("La estancia no existe")
    _audit(session, actor, "education_goals_accessed", stay_id)
    return session.scalars(select(EducationGoal).where(
        EducationGoal.stay_id == stay_id
    ).order_by(EducationGoal.created_at.desc())).all()


def list_school_placements(session: Session, *, actor_account_id: str, stay_id: str):
    actor = _actor(session, actor_account_id)
    if session.get(Stay, stay_id) is None:
        raise ValueError("La estancia no existe")
    _audit(session, actor, "school_history_accessed", stay_id)
    return session.scalars(select(SchoolPlacement).where(
        SchoolPlacement.stay_id == stay_id
    ).order_by(SchoolPlacement.started_on.desc())).all()


def list_school_records(session: Session, *, actor_account_id: str, placement_id: str):
    actor = _actor(session, actor_account_id)
    placement = session.get(SchoolPlacement, placement_id)
    if placement is None:
        raise ValueError("La escolarización no existe")
    _audit(session, actor, "school_records_accessed", placement_id)
    from gestion_centro.domain.education import SchoolRecord
    return session.scalars(select(SchoolRecord).where(
        SchoolRecord.placement_id == placement_id
    ).order_by(SchoolRecord.occurred_on.desc(), SchoolRecord.created_at.desc())).all()


def revise_education_update(session: Session, *, actor_account_id: str, update_id: str,
                            objective_description: str, actions_taken: str,
                            response_observed: str, follow_up: str | None = None):
    """Registra una rectificación propia como nueva actualización, sin alterar el original."""
    actor = _actor(session, actor_account_id)
    original = session.get(EducationUpdate, update_id)
    if original is None:
        raise ValueError("La actualización educativa original no existe")
    if original.author_account_id != actor.id:
        raise PermissionError("Solo puedes rectificar tus propias actualizaciones")
    goal = session.get(EducationGoal, original.goal_id)
    if goal is None or goal.status == "closed":
        raise ValueError("El seguimiento está cerrado y no admite rectificaciones ordinarias")
    if not all(value.strip() for value in (objective_description, actions_taken, response_observed)):
        raise ValueError("Completa observación, actuación y respuesta")
    correction = EducationUpdate(
        goal_id=original.goal_id, category=original.category,
        objective_description=f"RECTIFICACIÓN de la actualización {original.id}: {objective_description.strip()}",
        actions_taken=actions_taken.strip(), response_observed=response_observed.strip(),
        follow_up=follow_up.strip() if follow_up else None,
        author_account_id=actor.id, author_name_snapshot=actor.professional.display_name,
    )
    session.add(correction)
    session.flush()
    _audit(session, actor, "education_update_revised",
           f"Original:{original.id}; rectificación:{correction.id}")
    return correction
