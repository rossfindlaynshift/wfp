"""
Census snapshot service.

Orchestrates the snapshot workflow: pull data, detect changes, save snapshots.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.census import CensusSnapshot
from app.models.reference import EmployeeExclusion
from app.models.forecast import OpenRole, BackfillDecision
from app.services.cost_engine import build_lookup_tables, enrich_employee


def get_snapshot_periods(db: Session) -> list[date]:
    """Return all distinct snapshot periods, most recent first."""
    rows = (
        db.query(CensusSnapshot.snapshot_period)
        .distinct()
        .order_by(CensusSnapshot.snapshot_period.desc())
        .all()
    )
    return [r[0] for r in rows]


def get_snapshot(db: Session, period: date) -> list[dict]:
    """Return all employees for a given snapshot period as dicts."""
    rows = db.query(CensusSnapshot).filter(CensusSnapshot.snapshot_period == period).all()
    return [_snapshot_to_dict(r) for r in rows]


def find_new_employees(db: Session, raw_employees: list[dict]) -> list[dict]:
    """
    Find employees whose HiBob ID is not yet in the employee_exclusions table.
    Returns the list of new employee dicts.
    """
    known_ids = {
        r.hibob_id for r in db.query(EmployeeExclusion.hibob_id).all()
    }
    return [e for e in raw_employees if e.get("employee_id") not in known_ids]


def save_exclusion_decisions(db: Session, decisions: list[dict]) -> None:
    """
    Save exclusion decisions for new employees.
    Each dict: {hibob_id, display_name, job_title, department, excluded}
    """
    for d in decisions:
        existing = db.query(EmployeeExclusion).filter(
            EmployeeExclusion.hibob_id == d["hibob_id"]
        ).first()
        if existing:
            existing.excluded = d["excluded"]
        else:
            db.add(EmployeeExclusion(
                hibob_id=d["hibob_id"],
                display_name=d["display_name"],
                job_title=d.get("job_title"),
                department=d.get("department"),
                excluded=d["excluded"],
            ))
    db.commit()


def prepare_snapshot(
    db: Session,
    raw_employees: list[dict],
    snapshot_period: date,
) -> dict:
    """
    Filter excluded employees, enrich with cost data, and compute diff
    against the previous snapshot.

    Returns a dict with:
      - employees: enriched employee list (ready to save)
      - diff: {leavers, joiners, changes}
      - period: the snapshot date
    """
    # Filter out excluded employees
    excluded_ids = {
        r.hibob_id
        for r in db.query(EmployeeExclusion).filter(EmployeeExclusion.excluded == True).all()
    }
    filtered = [e for e in raw_employees if e.get("employee_id") not in excluded_ids]

    # Enrich with cost calculations
    lookups = build_lookup_tables(db)
    enriched = [enrich_employee(dict(e), lookups) for e in filtered]

    # Set source and period
    for emp in enriched:
        emp["source"] = "Census"
        emp["snapshot_period"] = snapshot_period

    # Compute diff against previous snapshot
    prev_periods = get_snapshot_periods(db)
    diff = {"leavers": [], "joiners": [], "changes": []}

    if prev_periods:
        prev = get_snapshot(db, prev_periods[0])
        prev_by_id = {e["employee_id"]: e for e in prev}
        curr_by_id = {e["employee_id"]: e for e in enriched}

        # Leavers: in previous but not in current
        for eid, prev_emp in prev_by_id.items():
            if eid not in curr_by_id:
                diff["leavers"].append(prev_emp)

        # Also detect employees who newly have a future_leave_date
        for eid, curr_emp in curr_by_id.items():
            if eid in prev_by_id:
                prev_emp = prev_by_id[eid]
                if curr_emp.get("future_leave_date") and not prev_emp.get("future_leave_date"):
                    diff["leavers"].append(curr_emp)

        # Joiners: in current but not in previous
        for eid, curr_emp in curr_by_id.items():
            if eid not in prev_by_id:
                diff["joiners"].append(curr_emp)

        # Changes: in both but with differences
        compare_fields = [
            "department", "job_title", "salary_local", "legal_entity",
            "site", "team", "business_unit", "commission", "bonus",
        ]
        for eid in set(prev_by_id) & set(curr_by_id):
            prev_emp = prev_by_id[eid]
            curr_emp = curr_by_id[eid]
            changes = {}
            for field in compare_fields:
                old_val = prev_emp.get(field)
                new_val = curr_emp.get(field)
                if old_val != new_val:
                    changes[field] = {"old": old_val, "new": new_val}
            if changes:
                diff["changes"].append({
                    "employee_id": eid,
                    "display_name": curr_emp.get("display_name"),
                    "changes": changes,
                })

    return {
        "employees": enriched,
        "diff": diff,
        "period": snapshot_period,
    }


def save_snapshot(db: Session, prepared: dict) -> int:
    """
    Save the prepared snapshot to the database.
    Returns number of employee records saved.
    """
    period = prepared["period"]

    # Delete any existing snapshot for this period (re-run safety)
    db.query(CensusSnapshot).filter(CensusSnapshot.snapshot_period == period).delete()

    count = 0
    for emp in prepared["employees"]:
        record = CensusSnapshot(
            snapshot_period=emp["snapshot_period"],
            source=emp.get("source") or "Census",
            employment_type=emp.get("employment_type") or "Employee",
            employee_id=emp["employee_id"],
            display_name=emp["display_name"],
            job_title=emp.get("job_title"),
            legal_entity=emp.get("legal_entity"),
            site=emp.get("site"),
            department=emp.get("department"),
            start_date=emp.get("start_date"),
            future_leave_date=emp.get("future_leave_date"),
            currency=emp.get("currency"),
            salary_local=emp.get("salary_local", 0),
            commission=emp.get("commission", 0),
            bonus=emp.get("bonus", 0),
            weekly_hours=emp.get("weekly_hours"),
            notice_period=emp.get("notice_period"),
            business_unit=emp.get("business_unit"),
            team=emp.get("team"),
            manager_id=emp.get("manager_id"),
            quota_type=emp.get("quota_type"),
            quota_amount=emp.get("quota_amount", 0),
            quota_ramp_start_date=emp.get("quota_ramp_start_date"),
            l1=emp.get("l1"),
            l2=emp.get("l2"),
            l3=emp.get("l3"),
            country=emp.get("country"),
            fx_rate=emp.get("fx_rate"),
            salary_eur=emp.get("salary_eur"),
            incentive_otv_eur=emp.get("incentive_otv_eur"),
            incentive_attainment=emp.get("incentive_attainment"),
            incentive_eur=emp.get("incentive_eur"),
            employer_benefits=emp.get("employer_benefits"),
            employer_taxes=emp.get("employer_taxes"),
            loaded_cost=emp.get("loaded_cost"),
            monthly_cost=emp.get("monthly_cost"),
        )
        db.add(record)
        count += 1

    db.commit()
    return count


def create_backfill_from_leaver(db: Session, leaver: dict, snapshot_period: date) -> int:
    """
    Create a backfill open role from a leaver's details.
    Returns the new open_role id.
    """
    start = leaver.get("future_leave_date") or snapshot_period
    role = OpenRole(
        source="backfill",
        employment_type=leaver.get("employment_type", "Employee"),
        display_name=f"Backfill - {leaver.get('job_title', 'TBD')}",
        job_title=leaver.get("job_title"),
        legal_entity=leaver.get("legal_entity"),
        site=leaver.get("site"),
        department=leaver.get("department"),
        start_date=start,
        currency=leaver.get("currency"),
        salary_local=leaver.get("salary_local", 0),
        commission=leaver.get("commission", 0),
        bonus=leaver.get("bonus", 0),
        weekly_hours=leaver.get("weekly_hours"),
        notice_period=leaver.get("notice_period"),
        business_unit=leaver.get("business_unit"),
        team=leaver.get("team"),
        manager_id=leaver.get("manager_id"),
        quota_type=leaver.get("quota_type"),
        quota_amount=leaver.get("quota_amount", 0),
        quota_ramp_start_date=None,
    )
    db.add(role)
    db.commit()
    db.refresh(role)

    # Record the decision
    db.add(BackfillDecision(
        leaver_employee_id=leaver["employee_id"],
        snapshot_period=snapshot_period,
        decision="accepted",
        open_role_id=role.id,
    ))
    db.commit()

    return role.id


def record_backfill_declined(db: Session, employee_id: int, snapshot_period: date) -> None:
    """Record that the user declined to create a backfill for this leaver."""
    db.add(BackfillDecision(
        leaver_employee_id=employee_id,
        snapshot_period=snapshot_period,
        decision="declined",
        open_role_id=None,
    ))
    db.commit()


def check_duplicate_open_role(db: Session, leaver: dict) -> Optional[dict]:
    """Check if there's already an open role that looks like a duplicate of this leaver's backfill."""
    matches = db.query(OpenRole).filter(
        OpenRole.department == leaver.get("department"),
        OpenRole.job_title == leaver.get("job_title"),
    ).all()
    if matches:
        m = matches[0]
        return {
            "id": m.id,
            "display_name": m.display_name,
            "job_title": m.job_title,
            "department": m.department,
            "start_date": str(m.start_date) if m.start_date else None,
        }
    return None


def compute_diff(db: Session, period_a: date, period_b: date) -> dict:
    """
    Compute the diff between two snapshot periods.
    Returns {leavers, joiners, changes} going from period_a to period_b.
    """
    snap_a = {e["employee_id"]: e for e in get_snapshot(db, period_a)}
    snap_b = {e["employee_id"]: e for e in get_snapshot(db, period_b)}

    leavers = [snap_a[eid] for eid in set(snap_a) - set(snap_b)]
    joiners = [snap_b[eid] for eid in set(snap_b) - set(snap_a)]

    compare_fields = [
        "department", "job_title", "salary_local", "legal_entity",
        "site", "team", "business_unit", "commission", "bonus",
    ]
    changes = []
    for eid in set(snap_a) & set(snap_b):
        diffs = {}
        for f in compare_fields:
            if snap_a[eid].get(f) != snap_b[eid].get(f):
                diffs[f] = {"old": snap_a[eid].get(f), "new": snap_b[eid].get(f)}
        if diffs:
            changes.append({
                "employee_id": eid,
                "display_name": snap_b[eid].get("display_name"),
                "changes": diffs,
            })

    return {"leavers": leavers, "joiners": joiners, "changes": changes}


def _snapshot_to_dict(row: CensusSnapshot) -> dict:
    """Convert a CensusSnapshot ORM object to a plain dict."""
    return {
        "id": row.id,
        "snapshot_period": str(row.snapshot_period) if row.snapshot_period else None,
        "source": row.source,
        "employment_type": row.employment_type,
        "employee_id": row.employee_id,
        "display_name": row.display_name,
        "job_title": row.job_title,
        "legal_entity": row.legal_entity,
        "site": row.site,
        "department": row.department,
        "start_date": str(row.start_date) if row.start_date else None,
        "future_leave_date": str(row.future_leave_date) if row.future_leave_date else None,
        "currency": row.currency,
        "salary_local": row.salary_local,
        "commission": row.commission,
        "bonus": row.bonus,
        "weekly_hours": row.weekly_hours,
        "notice_period": row.notice_period,
        "business_unit": row.business_unit,
        "team": row.team,
        "manager_id": row.manager_id,
        "quota_type": row.quota_type,
        "quota_amount": row.quota_amount,
        "quota_ramp_start_date": str(row.quota_ramp_start_date) if row.quota_ramp_start_date else None,
        "l1": row.l1,
        "l2": row.l2,
        "l3": row.l3,
        "country": row.country,
        "fx_rate": row.fx_rate,
        "salary_eur": row.salary_eur,
        "incentive_otv_eur": row.incentive_otv_eur,
        "incentive_attainment": row.incentive_attainment,
        "incentive_eur": row.incentive_eur,
        "employer_benefits": row.employer_benefits,
        "employer_taxes": row.employer_taxes,
        "loaded_cost": row.loaded_cost,
        "monthly_cost": row.monthly_cost,
    }
