from __future__ import annotations

from datetime import date
from typing import Optional, Any

from pydantic import BaseModel


class TakeSnapshotRequest(BaseModel):
    period: date  # e.g. 2026-03-31


class ExclusionDecision(BaseModel):
    hibob_id: str
    display_name: str
    job_title: Optional[str] = None
    department: Optional[str] = None
    excluded: bool


class ExclusionDecisionsRequest(BaseModel):
    decisions: list[ExclusionDecision]
    period: date


class BackfillRequest(BaseModel):
    employee_id: str
    accepted: bool


class ConfirmSnapshotRequest(BaseModel):
    period: date
    backfill_decisions: list[BackfillRequest] = []


class NewEmployeeOut(BaseModel):
    employee_id: str
    display_name: str
    job_title: Optional[str] = None
    department: Optional[str] = None
    employment_type: Optional[str] = None


class SnapshotPullResult(BaseModel):
    status: str  # "needs_exclusion_decisions" or "ready"
    new_employees: list[NewEmployeeOut] = []
    total_pulled: int = 0


class DiffSummary(BaseModel):
    leavers: list[dict[str, Any]]
    joiners: list[dict[str, Any]]
    changes: list[dict[str, Any]]


class PreparedSnapshotResult(BaseModel):
    status: str  # "review"
    period: str
    employee_count: int
    diff: DiffSummary
    leavers_for_backfill: list[dict[str, Any]] = []
    duplicate_warnings: dict[str, dict[str, Any]] = {}


class SnapshotPeriodOut(BaseModel):
    period: str
    employee_count: int


