from sqlalchemy import Column, Integer, String, Float, Date, Boolean
from app.database import Base


class FxRate(Base):
    __tablename__ = "fx_rates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    currency = Column(String, nullable=False, unique=True)
    rate_to_eur = Column(Float, nullable=False)


class LoadingMultiplier(Base):
    __tablename__ = "loading_multipliers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    legal_entity = Column(String, nullable=False, unique=True)
    default_location = Column(String, nullable=True)
    employer_benefits_pct = Column(Float, nullable=False)
    employer_taxes_pct = Column(Float, nullable=False)
    currency = Column(String, nullable=False)


class DepartmentHierarchy(Base):
    __tablename__ = "department_hierarchy"

    id = Column(Integer, primary_key=True, autoincrement=True)
    department = Column(String, nullable=False, unique=True)
    l1 = Column(String, nullable=False)
    l2 = Column(String, nullable=False)
    l3 = Column(String, nullable=False)


class EmployeeExclusion(Base):
    __tablename__ = "employee_exclusions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hibob_id = Column(Integer, nullable=False, unique=True)
    display_name = Column(String, nullable=False)
    job_title = Column(String, nullable=True)
    department = Column(String, nullable=True)
    excluded = Column(Boolean, nullable=False, default=False)


class MeritAssumption(Base):
    __tablename__ = "merit_assumptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merit_rate = Column(Float, nullable=False)
    effective_date = Column(Date, nullable=False)
    joiner_cutoff_date = Column(Date, nullable=False)


class BudgetTarget(Base):
    __tablename__ = "budget_targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    l2_function = Column(String, nullable=False)
    month = Column(Date, nullable=False)
    headcount = Column(Float, nullable=True)
    loaded_cost = Column(Float, nullable=True)
    pnl_cost = Column(Float, nullable=True)


class QuotaRampSchedule(Base):
    __tablename__ = "quota_ramp_schedule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_from = Column(Integer, nullable=False)
    day_to = Column(Integer, nullable=True)
    ramp_pct = Column(Float, nullable=False)


class LeaveCostRate(Base):
    __tablename__ = "leave_cost_rates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    country = Column(String, nullable=False, unique=True)
    cost_pct = Column(Float, nullable=False)
