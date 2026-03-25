from sqlalchemy import Column, Integer, String, Float, Date, DateTime, JSON, func
from app.database import Base


class ForecastAdjustment(Base):
    __tablename__ = "forecast_adjustments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, nullable=False)
    adjustment_type = Column(String, nullable=False)  # future_leave_date, salary_change, leave_of_absence
    # For future_leave_date
    future_leave_date = Column(Date, nullable=True)
    # For salary_change
    new_salary_local = Column(Float, nullable=True)
    salary_effective_date = Column(Date, nullable=True)
    # For leave_of_absence
    leave_type = Column(String, nullable=True)
    leave_start_date = Column(Date, nullable=True)
    leave_end_date = Column(Date, nullable=True)
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    notes = Column(String, nullable=True)


class OpenRole(Base):
    __tablename__ = "open_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)  # open_req / backfill
    employment_type = Column(String, nullable=False, default="Employee")
    display_name = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    legal_entity = Column(String, nullable=True)
    site = Column(String, nullable=True)
    department = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    currency = Column(String, nullable=True)
    salary_local = Column(Float, nullable=True, default=0)
    commission = Column(Float, nullable=True, default=0)
    bonus = Column(Float, nullable=True, default=0)
    weekly_hours = Column(Float, nullable=True)
    notice_period = Column(String, nullable=True)
    business_unit = Column(String, nullable=True)
    team = Column(String, nullable=True)
    manager_id = Column(Integer, nullable=True)
    quota_type = Column(String, nullable=True)
    quota_amount = Column(Float, nullable=True, default=0)
    quota_ramp_start_date = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class BackfillDecision(Base):
    __tablename__ = "backfill_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    leaver_employee_id = Column(Integer, nullable=False)
    snapshot_period = Column(Date, nullable=False)
    decision = Column(String, nullable=False)  # accepted / declined
    open_role_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class ForecastVersion(Base):
    __tablename__ = "forecast_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    base_census_period = Column(Date, nullable=False)
    frozen_inputs = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
