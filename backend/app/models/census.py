from sqlalchemy import Column, Integer, String, Float, Date
from app.database import Base


class CensusSnapshot(Base):
    __tablename__ = "census_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_period = Column(Date, nullable=False)
    source = Column(String, nullable=False)  # Census / Open Req / Backfill
    employment_type = Column(String, nullable=False)
    employee_id = Column(Integer, nullable=False)
    display_name = Column(String, nullable=False)
    job_title = Column(String, nullable=True)
    legal_entity = Column(String, nullable=True)
    site = Column(String, nullable=True)
    department = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    future_leave_date = Column(Date, nullable=True)
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
    # Calculated fields stored for historical record
    l1 = Column(String, nullable=True)
    l2 = Column(String, nullable=True)
    l3 = Column(String, nullable=True)
    country = Column(String, nullable=True)
    fx_rate = Column(Float, nullable=True)
    salary_eur = Column(Float, nullable=True)
    incentive_otv_eur = Column(Float, nullable=True)
    incentive_attainment = Column(Float, nullable=True)
    incentive_eur = Column(Float, nullable=True)
    employer_benefits = Column(Float, nullable=True)
    employer_taxes = Column(Float, nullable=True)
    loaded_cost = Column(Float, nullable=True)
    monthly_cost = Column(Float, nullable=True)
