from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


# --- FX Rates ---
class FxRateBase(BaseModel):
    currency: str
    rate_to_eur: float

class FxRateCreate(FxRateBase):
    pass

class FxRateOut(FxRateBase):
    id: int
    model_config = {"from_attributes": True}


# --- Loading Multipliers ---
class LoadingMultiplierBase(BaseModel):
    legal_entity: str
    default_location: Optional[str] = None
    employer_benefits_pct: float
    employer_taxes_pct: float
    currency: str

class LoadingMultiplierCreate(LoadingMultiplierBase):
    pass

class LoadingMultiplierOut(LoadingMultiplierBase):
    id: int
    model_config = {"from_attributes": True}


# --- Department Hierarchy ---
class DepartmentHierarchyBase(BaseModel):
    department: str
    l1: str
    l2: str
    l3: str

class DepartmentHierarchyCreate(DepartmentHierarchyBase):
    pass

class DepartmentHierarchyOut(DepartmentHierarchyBase):
    id: int
    model_config = {"from_attributes": True}


# --- Employee Exclusions ---
class EmployeeExclusionBase(BaseModel):
    hibob_id: int
    display_name: str
    job_title: Optional[str] = None
    department: Optional[str] = None
    excluded: bool = False

class EmployeeExclusionCreate(EmployeeExclusionBase):
    pass

class EmployeeExclusionUpdate(BaseModel):
    excluded: bool

class EmployeeExclusionOut(EmployeeExclusionBase):
    id: int
    model_config = {"from_attributes": True}


# --- Merit Assumptions ---
class MeritAssumptionBase(BaseModel):
    merit_rate: float
    effective_date: date
    joiner_cutoff_date: date

class MeritAssumptionCreate(MeritAssumptionBase):
    pass

class MeritAssumptionOut(MeritAssumptionBase):
    id: int
    model_config = {"from_attributes": True}


# --- Budget Targets ---
class BudgetTargetBase(BaseModel):
    l2_function: str
    month: date
    headcount: Optional[float] = None
    loaded_cost: Optional[float] = None
    pnl_cost: Optional[float] = None

class BudgetTargetCreate(BudgetTargetBase):
    pass

class BudgetTargetOut(BudgetTargetBase):
    id: int
    model_config = {"from_attributes": True}


# --- Quota Ramp Schedule ---
class QuotaRampScheduleBase(BaseModel):
    day_from: int
    day_to: Optional[int] = None
    ramp_pct: float

class QuotaRampScheduleCreate(QuotaRampScheduleBase):
    pass

class QuotaRampScheduleOut(QuotaRampScheduleBase):
    id: int
    model_config = {"from_attributes": True}


# --- Leave Cost Rates ---
class LeaveCostRateBase(BaseModel):
    country: str
    cost_pct: float

class LeaveCostRateCreate(LeaveCostRateBase):
    pass

class LeaveCostRateOut(LeaveCostRateBase):
    id: int
    model_config = {"from_attributes": True}
