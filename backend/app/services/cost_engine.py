"""
Cost enrichment engine.

Takes raw employee data and lookups from reference tables to calculate
all derived cost fields (FX conversion, loading, incentive, etc.).
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.reference import FxRate, LoadingMultiplier, DepartmentHierarchy


def build_lookup_tables(db: Session) -> dict[str, Any]:
    """Load all reference data needed for cost enrichment into memory."""
    fx_rates = {r.currency: r.rate_to_eur for r in db.query(FxRate).all()}
    loading = {
        r.legal_entity: {
            "benefits_pct": r.employer_benefits_pct,
            "taxes_pct": r.employer_taxes_pct,
            "currency": r.currency,
            "default_location": r.default_location,
        }
        for r in db.query(LoadingMultiplier).all()
    }
    dept_hierarchy = {
        r.department: {"l1": r.l1, "l2": r.l2, "l3": r.l3}
        for r in db.query(DepartmentHierarchy).all()
    }

    # Build site -> country mapping from loading multiplier locations
    site_country: dict[str, str] = {}
    for lm in loading.values():
        loc = lm.get("default_location")
        if loc:
            # Extract country from "City, Country" format
            parts = loc.split(",")
            if len(parts) >= 2:
                site_country[loc.strip()] = parts[-1].strip()

    return {
        "fx_rates": fx_rates,
        "loading": loading,
        "dept_hierarchy": dept_hierarchy,
        "site_country": site_country,
    }


def enrich_employee(emp: dict, lookups: dict[str, Any]) -> dict:
    """
    Enrich a single employee dict with calculated cost fields.
    Mutates and returns the dict.
    """
    fx_rates = lookups["fx_rates"]
    loading = lookups["loading"]
    dept_hierarchy = lookups["dept_hierarchy"]
    site_country = lookups["site_country"]

    # Department hierarchy lookup
    dept = emp.get("department") or ""
    hier = dept_hierarchy.get(dept, {})
    emp["l1"] = hier.get("l1")
    emp["l2"] = hier.get("l2")
    emp["l3"] = hier.get("l3")

    # Country from site
    site = emp.get("site") or ""
    emp["country"] = site_country.get(site)

    # FX rate
    currency = emp.get("currency") or "EUR"
    fx_rate = fx_rates.get(currency, 1.0)
    emp["fx_rate"] = fx_rate

    # EUR conversion
    salary_local = float(emp.get("salary_local") or 0)
    commission = float(emp.get("commission") or 0)
    bonus = float(emp.get("bonus") or 0)

    salary_eur = salary_local / fx_rate if fx_rate else 0
    emp["salary_eur"] = salary_eur

    # Incentive: commission for sales, bonus for non-sales (whichever is non-zero)
    incentive_local = commission if commission > 0 else bonus
    incentive_otv_eur = incentive_local / fx_rate if fx_rate else 0
    emp["incentive_otv_eur"] = incentive_otv_eur

    # Attainment: 0.8 for commission roles, 1.0 for bonus roles
    if commission > 0:
        emp["incentive_attainment"] = 0.8
    else:
        emp["incentive_attainment"] = 1.0

    incentive_eur = incentive_otv_eur * emp["incentive_attainment"]
    emp["incentive_eur"] = incentive_eur

    # Loading multipliers by legal entity
    entity = emp.get("legal_entity") or ""
    lm = loading.get(entity, {})
    benefits_pct = lm.get("benefits_pct", 0)
    taxes_pct = lm.get("taxes_pct", 0)

    base_for_loading = salary_eur + incentive_otv_eur
    employer_benefits = base_for_loading * benefits_pct
    employer_taxes = base_for_loading * taxes_pct
    emp["employer_benefits"] = employer_benefits
    emp["employer_taxes"] = employer_taxes

    # Loaded cost
    loaded_cost = salary_eur + incentive_eur + employer_benefits + employer_taxes
    emp["loaded_cost"] = loaded_cost
    emp["monthly_cost"] = loaded_cost / 12

    return emp
