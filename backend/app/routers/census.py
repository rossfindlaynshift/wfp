"""
Census snapshot API endpoints.

Implements the multi-step snapshot workflow:
1. POST /take-snapshot  — pull from HiBob, check for new employees
2. POST /exclusion-decisions — save exclusion decisions, enrich, diff
3. POST /confirm-snapshot — save to DB with backfill decisions
"""
from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.census import (
    TakeSnapshotRequest,
    ExclusionDecisionsRequest,
    ConfirmSnapshotRequest,
    SnapshotPullResult,
    NewEmployeeOut,
    PreparedSnapshotResult,
    DiffSummary,
    SnapshotPeriodOut,
)
from app.services.census import (
    get_snapshot_periods,
    get_snapshot,
    find_new_employees,
    save_exclusion_decisions,
    prepare_snapshot,
    save_snapshot,
    create_backfill_from_leaver,
    record_backfill_declined,
    check_duplicate_open_role,
    compute_diff,
)
from app.services.hibob import fetch_employees_from_hibob

router = APIRouter()

# In-memory store for the pending snapshot between steps.
# In a multi-user setup this would be session/cache-based.
_pending_raw: dict[str, list[dict]] = {}
_pending_prepared: dict[str, dict] = {}


@router.post("/take-snapshot", response_model=SnapshotPullResult)
async def take_snapshot(req: TakeSnapshotRequest, db: Session = Depends(get_db)):
    """
    Step 1: Pull employees from HiBob, check for new employees needing exclusion decisions.
    """
    period_str = str(req.period)

    # Pull employee data from HiBob
    raw_employees = await fetch_employees_from_hibob()

    # Store in memory for subsequent steps
    _pending_raw[period_str] = raw_employees

    # Check for new employees not in exclusion table
    new_emps = find_new_employees(db, raw_employees)

    if new_emps:
        return SnapshotPullResult(
            status="needs_exclusion_decisions",
            new_employees=[
                NewEmployeeOut(
                    employee_id=e["employee_id"],
                    display_name=e["display_name"],
                    job_title=e.get("job_title"),
                    department=e.get("department"),
                    employment_type=e.get("employment_type"),
                )
                for e in new_emps
            ],
            total_pulled=len(raw_employees),
        )

    # No new employees — proceed directly to prepare
    prepared = prepare_snapshot(db, raw_employees, req.period)
    _pending_prepared[period_str] = prepared

    # Identify leavers that need backfill decisions
    leavers = prepared["diff"]["leavers"]
    duplicate_warnings = {}
    for leaver in leavers:
        dup = check_duplicate_open_role(db, leaver)
        if dup:
            duplicate_warnings[leaver["employee_id"]] = dup

    return SnapshotPullResult(
        status="ready",
        new_employees=[],
        total_pulled=len(raw_employees),
    )


@router.post("/exclusion-decisions", response_model=PreparedSnapshotResult)
def submit_exclusion_decisions(req: ExclusionDecisionsRequest, db: Session = Depends(get_db)):
    """
    Step 2: Save exclusion decisions, then filter, enrich, and compute diff.
    Returns the change summary for user review.
    """
    period_str = str(req.period)

    # Save decisions
    save_exclusion_decisions(db, [d.model_dump() for d in req.decisions])

    # Get raw employees from step 1
    raw_employees = _pending_raw.get(period_str)
    if not raw_employees:
        raise HTTPException(status_code=400, detail="No pending snapshot. Run take-snapshot first.")

    # Prepare snapshot (filter, enrich, diff)
    prepared = prepare_snapshot(db, raw_employees, req.period)
    _pending_prepared[period_str] = prepared

    # Identify leavers for backfill prompts
    leavers = prepared["diff"]["leavers"]
    duplicate_warnings = {}
    for leaver in leavers:
        dup = check_duplicate_open_role(db, leaver)
        if dup:
            duplicate_warnings[leaver["employee_id"]] = dup

    return PreparedSnapshotResult(
        status="review",
        period=period_str,
        employee_count=len(prepared["employees"]),
        diff=DiffSummary(**prepared["diff"]),
        leavers_for_backfill=leavers,
        duplicate_warnings=duplicate_warnings,
    )


@router.post("/confirm-snapshot")
def confirm_snapshot(req: ConfirmSnapshotRequest, db: Session = Depends(get_db)):
    """
    Step 3: Save the snapshot and process backfill decisions.
    """
    period_str = str(req.period)
    prepared = _pending_prepared.get(period_str)
    if not prepared:
        raise HTTPException(status_code=400, detail="No prepared snapshot. Complete the previous steps first.")

    # Save census snapshot
    count = save_snapshot(db, prepared)

    # Process backfill decisions
    leavers_by_id = {l["employee_id"]: l for l in prepared["diff"]["leavers"]}
    backfills_created = 0
    for decision in req.backfill_decisions:
        leaver = leavers_by_id.get(decision.employee_id)
        if not leaver:
            continue
        if decision.accepted:
            create_backfill_from_leaver(db, leaver, req.period)
            backfills_created += 1
        else:
            record_backfill_declined(db, decision.employee_id, req.period)

    # Cleanup pending state
    _pending_raw.pop(period_str, None)
    _pending_prepared.pop(period_str, None)

    return {
        "status": "saved",
        "period": period_str,
        "employees_saved": count,
        "backfills_created": backfills_created,
    }


@router.get("/snapshots", response_model=list[SnapshotPeriodOut])
def list_snapshots(db: Session = Depends(get_db)):
    """List all snapshot periods with employee counts."""
    from sqlalchemy import func
    rows = (
        db.query(
            CensusSnapshot.snapshot_period,
            func.count(CensusSnapshot.id),
        )
        .group_by(CensusSnapshot.snapshot_period)
        .order_by(CensusSnapshot.snapshot_period.desc())
        .all()
    )
    return [
        SnapshotPeriodOut(period=str(r[0]), employee_count=r[1])
        for r in rows
    ]


@router.get("/snapshot/{period}")
def get_snapshot_data(period: str, db: Session = Depends(get_db)):
    """Get full employee data for a snapshot period."""
    try:
        period_date = date.fromisoformat(period)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    data = get_snapshot(db, period_date)
    if not data:
        raise HTTPException(status_code=404, detail=f"No snapshot found for {period}")
    return data


@router.get("/diff/{period_a}/{period_b}")
def get_diff(period_a: str, period_b: str, db: Session = Depends(get_db)):
    """Compute diff between two snapshot periods."""
    try:
        date_a = date.fromisoformat(period_a)
        date_b = date.fromisoformat(period_b)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    return compute_diff(db, date_a, date_b)


# Need to import the model for the list_snapshots query
from app.models.census import CensusSnapshot
