"""Servicios sanitarios de registro; nunca sustituyen indicación clínica."""
from datetime import date, datetime, timezone
import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from gestion_centro.auth.models import AccessAudit, UserAccount
from gestion_centro.domain.models import Minor, Stay
from gestion_centro.domain.health import HealthProfile, HealthProfileVersion, MedicationPlan, MedicationPlanVersion, MedicationSchedule, MedicationAdministration, VaccineRecord

MEDICATION_RESULTS={"administered","refused","not_available"}

def _actor(session: Session, account_id: str) -> UserAccount:
    actor=session.get(UserAccount,account_id)
    if actor is None or not actor.active or not actor.professional.active:
        raise PermissionError("Se requiere una cuenta y un profesional activos")
    return actor

def _audit(session: Session, actor: UserAccount, event: str, details: str):
    session.add(AccessAudit(account_id=actor.id,username_snapshot=actor.username,event=event,details=details))

def _resolve_minor(session: Session, *, minor_id: str | None = None, stay_id: str | None = None):
    if minor_id:
        minor=session.get(Minor,minor_id)
    elif stay_id:
        stay=session.get(Stay,stay_id)
        minor=stay.minor if stay else None
    else:
        minor=None
    if minor is None:
        raise ValueError("El residente no existe")
    stay = session.get(Stay, stay_id) if stay_id else session.scalar(
        select(Stay).where(Stay.minor_id == minor.id, Stay.status == "active")
    )
    if stay is not None and stay.minor_id != minor.id:
        raise ValueError("La estancia seleccionada no pertenece al residente")
    return minor, stay

def _active_stay(session: Session, minor: Minor, stay_id: str | None = None):
    if stay_id:
        stay=session.get(Stay,stay_id)
        if stay is None or stay.minor_id != minor.id or stay.status != "active":
            raise ValueError("La estancia no existe, no pertenece al residente o está cerrada")
        return stay
    return session.scalar(select(Stay).where(Stay.minor_id==minor.id, Stay.status=="active"))

def read_health_profile(session: Session, *, actor_account_id: str, minor_id: str | None = None, stay_id: str | None = None):
    actor=_actor(session,actor_account_id); minor, _ = _resolve_minor(session,minor_id=minor_id,stay_id=stay_id)
    _audit(session,actor,"health_profile_accessed",minor.id)
    return session.scalar(select(HealthProfile).where(HealthProfile.minor_id==minor.id))

def save_health_profile(session: Session, *, actor_account_id: str, allergies: str | None,
                         relevant_conditions: str | None, emergency_instructions: str | None,
                         minor_id: str | None = None, stay_id: str | None = None):
    actor=_actor(session,actor_account_id); minor, stay = _resolve_minor(session,minor_id=minor_id,stay_id=stay_id)
    profile=session.scalar(select(HealthProfile).where(HealthProfile.minor_id==minor.id))
    old_values = {
        "allergies": profile.allergies if profile else None,
        "relevant_conditions": profile.relevant_conditions if profile else None,
        "emergency_instructions": profile.emergency_instructions if profile else None,
    }
    new_values = {
        "allergies": allergies.strip() if allergies else None,
        "relevant_conditions": relevant_conditions.strip() if relevant_conditions else None,
        "emergency_instructions": emergency_instructions.strip() if emergency_instructions else None,
    }
    if old_values != new_values:
        changed_at = datetime.now(timezone.utc)
        if profile is None:
            profile = HealthProfile(
                minor_id=minor.id,
                stay_id=stay.id if stay else None,
                allergies=new_values["allergies"],
                relevant_conditions=new_values["relevant_conditions"],
                emergency_instructions=new_values["emergency_instructions"],
                updated_by_account_id=actor.id,
                updated_by_name_snapshot=actor.professional.display_name,
                updated_at=changed_at,
            )
            session.add(profile)
            session.flush()
        else:
            profile.allergies = new_values["allergies"]
            profile.relevant_conditions = new_values["relevant_conditions"]
            profile.emergency_instructions = new_values["emergency_instructions"]
            profile.updated_by_account_id = actor.id
            profile.updated_by_name_snapshot = actor.professional.display_name
            profile.updated_at = changed_at
        session.add(HealthProfileVersion(
            minor_id=minor.id, profile_id=profile.id,
            changed_by_account_id=actor.id,
            changed_by_name_snapshot=actor.professional.display_name,
            changed_at=changed_at, old_values=old_values, new_values=new_values,
        ))
        _audit(session,actor,"health_profile_updated",minor.id)
    return profile


def list_health_profile_versions(session: Session, *, actor_account_id: str, minor_id: str):
    actor = _actor(session, actor_account_id)
    minor, _ = _resolve_minor(session, minor_id=minor_id)
    _audit(session, actor, "health_profile_history_accessed", minor.id)
    return session.scalars(
        select(HealthProfileVersion).where(HealthProfileVersion.minor_id == minor.id)
        .order_by(HealthProfileVersion.changed_at.desc(), HealthProfileVersion.id.desc())
    ).all()


def _medication_plan_values(plan: MedicationPlan) -> dict:
    return {
        "medication_name": plan.medication_name,
        "prescribed_dose": plan.prescribed_dose,
        "schedule_text": plan.schedule_text,
        "prescriber_reference": plan.prescriber_reference,
        "starts_on": plan.starts_on.isoformat(),
        "ends_on": plan.ends_on.isoformat() if plan.ends_on else None,
        "instructions": plan.instructions,
        "active": bool(plan.active),
        "schedules": [
            {"time": item.time_of_day, "shift": item.shift}
            for item in sorted(plan.schedules, key=lambda item: (item.time_of_day, item.shift))
        ],
    }


def _record_medication_plan_version(session: Session, plan: MedicationPlan, actor: UserAccount,
                                    old_values: dict, new_values: dict) -> None:
    if old_values == new_values:
        return
    session.add(MedicationPlanVersion(
        plan_id=plan.id, minor_id=plan.minor_id,
        changed_by_account_id=actor.id,
        changed_by_name_snapshot=actor.professional.display_name,
        changed_at=datetime.now(timezone.utc),
        old_values=old_values, new_values=new_values,
    ))


def list_medication_plan_versions(session: Session, *, actor_account_id: str, plan_id: str):
    actor = _actor(session, actor_account_id)
    plan = session.get(MedicationPlan, plan_id)
    if plan is None:
        raise ValueError("La pauta no existe")
    _audit(session, actor, "medication_plan_history_accessed", f"{plan.minor_id}:{plan.id}")
    return session.scalars(
        select(MedicationPlanVersion).where(MedicationPlanVersion.plan_id == plan.id)
        .order_by(MedicationPlanVersion.changed_at.desc(), MedicationPlanVersion.id.desc())
    ).all()


def add_medication_plan(session: Session, *, actor_account_id: str, medication_name: str,
                        prescribed_dose: str, schedule_text: str, prescriber_reference: str,
                        starts_on: date, minor_id: str | None = None, stay_id: str | None = None,
                        ends_on: date | None = None, instructions: str | None = None,
                        schedules: list[tuple[str, str]] | None = None):
    actor=_actor(session,actor_account_id); minor, _ = _resolve_minor(session,minor_id=minor_id,stay_id=stay_id)
    if not all(x.strip() for x in (medication_name,prescribed_dose,schedule_text,prescriber_reference)):
        raise ValueError("Medicamento, dosis prescrita, pauta y referencia del prescriptor son obligatorios")
    if ends_on and ends_on<starts_on: raise ValueError("La fecha final precede al inicio")
    normalized_schedules = []
    for time_text, shift in schedules or []:
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", time_text):
            raise ValueError(f"Hora no válida: {time_text}. Usa HH:MM")
        if shift not in {"morning", "afternoon", "night"}:
            raise ValueError("Turno no válido")
        if any(existing[0] == time_text for existing in normalized_schedules):
            raise ValueError("No repitas una hora dentro de la misma pauta")
        normalized_schedules.append((time_text, shift))
    if schedules is not None and not normalized_schedules:
        raise ValueError("Indica al menos una hora prescrita")
    plan=MedicationPlan(minor_id=minor.id,stay_id=stay_id,medication_name=medication_name.strip(),
        prescribed_dose=prescribed_dose.strip(),schedule_text=schedule_text.strip(),
        prescriber_reference=prescriber_reference.strip(),starts_on=starts_on,ends_on=ends_on,
        instructions=instructions.strip() if instructions else None,
        recorded_by_account_id=actor.id,recorded_by_name_snapshot=actor.professional.display_name)
    for time_text, shift in normalized_schedules:
        plan.schedules.append(MedicationSchedule(time_of_day=time_text, shift=shift))
    session.add(plan); session.flush()
    _record_medication_plan_version(session, plan, actor, {}, _medication_plan_values(plan))
    _audit(session,actor,"medication_plan_recorded",f"{minor.id}:{plan.id}")
    return plan

def set_medication_schedules(session: Session, *, actor_account_id: str, plan_id: str,
                             schedules: list[tuple[str, str]]):
    actor = _actor(session, actor_account_id)
    plan = session.get(MedicationPlan, plan_id)
    if plan is None or not plan.active:
        raise ValueError("La pauta no existe o está inactiva")
    if not schedules:
        raise ValueError("Indica al menos una hora prescrita")
    normalized = []
    for time_text, shift in schedules:
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", time_text):
            raise ValueError(f"Hora no válida: {time_text}. Usa HH:MM")
        if shift not in {"morning", "afternoon", "night"}:
            raise ValueError("Turno no válido")
        if any(existing[0] == time_text for existing in normalized):
            raise ValueError("No repitas una hora dentro de la misma pauta")
        normalized.append((time_text, shift))
    old_values = _medication_plan_values(plan)
    plan.schedules.clear()
    for time_text, shift in normalized:
        plan.schedules.append(MedicationSchedule(time_of_day=time_text, shift=shift))
    session.flush()
    new_values = _medication_plan_values(plan)
    _record_medication_plan_version(session, plan, actor, old_values, new_values)
    _audit(session, actor, "medication_schedule_set", f"{plan.id}:{normalized}")
    return plan.schedules

def list_daily_medication_schedule(session: Session, *, actor_account_id: str,
                                   day: date, minor_id: str | None = None, stay_id: str | None = None):
    actor = _actor(session, actor_account_id)
    minor, stay = _resolve_minor(session,minor_id=minor_id,stay_id=stay_id)
    # Solo se programa y administra desde la estancia activa actual. Las pautas
    # ligadas a ingresos cerrados siguen visibles en el historial, pero nunca se
    # convierten automáticamente en medicación vigente tras un reingreso.
    active_stay = _active_stay(session, minor)
    if active_stay is None:
        _audit(session, actor, "medication_daily_schedule_accessed", f"{minor.id}:{day.isoformat()}:sin-estancia-activa")
        return []
    plans = session.scalars(select(MedicationPlan).where(
        MedicationPlan.minor_id == minor.id, MedicationPlan.stay_id == active_stay.id,
        MedicationPlan.active.is_(True), MedicationPlan.starts_on <= day
    ).order_by(MedicationPlan.medication_name)).all()
    results = []
    for plan in plans:
        if plan.ends_on and plan.ends_on < day:
            continue
        for schedule in plan.schedules:
            local_dt = datetime.combine(day, datetime.strptime(schedule.time_of_day, "%H:%M").time()).astimezone()
            day_records = session.scalars(select(MedicationAdministration).where(
                MedicationAdministration.plan_id == plan.id
            )).all()
            matched = None
            for record in day_records:
                recorded_local = record.scheduled_at.astimezone()
                if recorded_local.date() == day and recorded_local.strftime("%H:%M") == schedule.time_of_day:
                    matched = record
                    break
            results.append((plan, schedule, local_dt, matched))
    _audit(session, actor, "medication_daily_schedule_accessed", f"{minor.id}:{day.isoformat()}")
    return results

def record_medication_administration(session: Session, *, actor_account_id: str, plan_id: str,
                                     scheduled_at: datetime, status: str, shift: str = "unspecified", note: str | None = None):
    actor=_actor(session,actor_account_id); plan=session.get(MedicationPlan,plan_id)
    if plan is None or not plan.active: raise ValueError("La pauta no existe o está inactiva")
    if not plan.stay_id or _active_stay(session, session.get(Minor, plan.minor_id), plan.stay_id) is None:
        raise ValueError("La pauta no pertenece a una estancia activa; consulta el historial y registra una pauta vigente para el ingreso actual")
    if status not in MEDICATION_RESULTS: raise ValueError("Resultado de administración no válido")
    if shift not in {"morning", "afternoon", "night", "unspecified"}: raise ValueError("Turno no válido")
    if status!="administered" and not (note and note.strip()):
        raise ValueError("Indica el motivo si no se administra")
    target_local = scheduled_at.astimezone()
    scheduled_local_date = target_local.date()
    if scheduled_local_date < plan.starts_on or (plan.ends_on and scheduled_local_date > plan.ends_on):
        raise ValueError("La fecha queda fuera de la vigencia de la pauta")
    local_time = target_local.strftime("%H:%M")
    if plan.schedules and not any(item.time_of_day == local_time and item.shift == shift for item in plan.schedules):
        raise ValueError("La hora y el turno no coinciden con un horario de la pauta")
    existing_records = session.scalars(select(MedicationAdministration).where(
        MedicationAdministration.plan_id == plan.id
    )).all()
    for existing in existing_records:
        existing_local = existing.scheduled_at.astimezone()
        if existing_local.date() == target_local.date() and existing_local.strftime("%H:%M") == local_time:
            raise ValueError("Ya existe un registro para esta dosis prevista")
    record=MedicationAdministration(plan_id=plan.id,scheduled_at=scheduled_at,shift=shift,status=status,
        note=note.strip() if note else None,recorded_by_account_id=actor.id,
        recorded_by_name_snapshot=actor.professional.display_name)
    session.add(record); session.flush()
    _audit(session,actor,"medication_administration_recorded",f"{plan.id}:{record.id}:{status}")
    return record

def add_vaccine_record(session: Session, *, actor_account_id: str, vaccine_name: str,
                       administered_on: date, minor_id: str | None = None, stay_id: str | None = None,
                       dose_reference: str | None = None):
    actor=_actor(session,actor_account_id); minor, stay = _resolve_minor(session,minor_id=minor_id,stay_id=stay_id)
    if not vaccine_name.strip(): raise ValueError("La vacuna es obligatoria")
    if administered_on > date.today():
        raise ValueError("La fecha de administración no puede ser futura")
    # El registro vacunal pertenece al expediente permanente del menor.
    # Solo se vincula a una estancia cuando se indica expresamente.
    record=VaccineRecord(minor_id=minor.id,stay_id=stay_id,
        vaccine_name=vaccine_name.strip(),administered_on=administered_on,dose_reference=dose_reference,
        recorded_by_account_id=actor.id,recorded_by_name_snapshot=actor.professional.display_name)
    session.add(record); session.flush()
    _audit(session,actor,"vaccine_recorded",f"{minor.id}:{record.id}")
    return record

def list_medication_plans(session: Session, *, actor_account_id: str,
                          minor_id: str | None = None, stay_id: str | None = None):
    actor=_actor(session,actor_account_id); minor, _ = _resolve_minor(session,minor_id=minor_id,stay_id=stay_id)
    _audit(session,actor,"medication_plans_accessed",minor.id)
    return session.scalars(select(MedicationPlan).where(MedicationPlan.minor_id==minor.id).order_by(MedicationPlan.starts_on.desc())).all()
