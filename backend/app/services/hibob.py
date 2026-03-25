"""
HiBob API client.

When no API key is configured, falls back to loading from the spreadsheet
so that the snapshot workflow can be developed and tested without live API access.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

import httpx

from app.config import HIBOB_API_TOKEN, HIBOB_SERVICE_USER, HIBOB_BASE_URL

# Mapping from HiBob API field paths (humanReadable=REPLACE) to our internal field names
HIBOB_FIELD_MAP = {
    "work.employeeIdInCompany": "employee_id",
    "displayName": "display_name",
    "work.title": "job_title",
    "work.department": "department",
    "work.site": "site",
    "payroll.employment.type": "employment_type",
    "financial.annualSalary.value": "salary_local",
    "financial.annualSalary.currency": "currency",
    "work.startDate": "start_date",
    "employment.contract.endDate": "future_leave_date",
}


def _get_nested(obj: dict, path: str) -> Any:
    """Retrieve a nested value from a dict using dot notation."""
    for key in path.split("."):
        if isinstance(obj, dict):
            obj = obj.get(key)
        else:
            return None
    return obj


async def fetch_employees_from_hibob() -> list[dict]:
    """Fetch all active employees from HiBob API (POST /v1/people/search)."""
    if not HIBOB_SERVICE_USER or not HIBOB_API_TOKEN:
        raise RuntimeError("HIBOB_SERVICE_USER and HIBOB_API_TOKEN must be configured")

    auth = httpx.BasicAuth(HIBOB_SERVICE_USER, HIBOB_API_TOKEN)

    async with httpx.AsyncClient(base_url=HIBOB_BASE_URL, auth=auth, timeout=60) as client:
        resp = await client.post("/people/search", json={
            "showInactive": False,
            "humanReadable": "REPLACE",
        })
        resp.raise_for_status()
        data = resp.json()
        employees = data.get("employees", [])

    return [_map_hibob_employee(emp) for emp in employees]


def _parse_date(val: Any) -> Optional[date]:
    """Parse a date string in DD/MM/YYYY or YYYY-MM-DD format."""
    if isinstance(val, date):
        return val
    if not isinstance(val, str) or not val:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


def _map_hibob_employee(raw: dict) -> dict:
    """Map a raw HiBob employee dict to our census schema."""
    result: dict[str, Any] = {}

    for bob_path, our_field in HIBOB_FIELD_MAP.items():
        result[our_field] = _get_nested(raw, bob_path)

    # Fall back to HiBob internal ID if company ID is missing
    if not result.get("employee_id"):
        result["employee_id"] = raw.get("id")

    # Additional fields
    result.setdefault("employment_type", "Employee")
    result["legal_entity"] = _get_nested(raw, "work.company") or _get_nested(raw, "custom.field_1736507339838")
    result["business_unit"] = _get_nested(raw, "work.customColumns.column_1648654188866")
    result["team"] = _get_nested(raw, "work.customColumns.column_1649159392883") or _get_nested(raw, "work.team")
    result["manager_id"] = _get_nested(raw, "work.reportsToIdInCompany")
    result["weekly_hours"] = _get_nested(raw, "payroll.employment.weeklyHours") or _get_nested(raw, "employee.weeklyHours")
    result["commission"] = _get_nested(raw, "financial.commission.value") or 0
    result["bonus"] = _get_nested(raw, "financial.bonus.value") or 0
    result["quota_type"] = None
    result["quota_amount"] = 0
    result["quota_ramp_start_date"] = None

    # Parse dates (humanReadable format is DD/MM/YYYY)
    for date_field in ("start_date", "future_leave_date", "quota_ramp_start_date"):
        result[date_field] = _parse_date(result.get(date_field))

    # Ensure numerics default to 0 where missing
    for num_field in ("salary_local", "commission", "bonus", "weekly_hours", "quota_amount"):
        val = result.get(num_field)
        if val is not None:
            try:
                result[num_field] = float(val)
            except (ValueError, TypeError):
                result[num_field] = 0
        else:
            result[num_field] = 0

    return result


