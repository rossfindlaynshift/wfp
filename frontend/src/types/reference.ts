export interface FxRate {
  id: number;
  currency: string;
  rate_to_eur: number;
}

export interface LoadingMultiplier {
  id: number;
  legal_entity: string;
  default_location: string | null;
  employer_benefits_pct: number;
  employer_taxes_pct: number;
  currency: string;
}

export interface DepartmentHierarchy {
  id: number;
  department: string;
  l1: string;
  l2: string;
  l3: string;
}

export interface EmployeeExclusion {
  id: number;
  hibob_id: number;
  display_name: string;
  job_title: string | null;
  department: string | null;
  excluded: boolean;
}

export interface MeritAssumption {
  id: number;
  merit_rate: number;
  effective_date: string;
  joiner_cutoff_date: string;
}

export interface BudgetTarget {
  id: number;
  l2_function: string;
  month: string;
  headcount: number | null;
  loaded_cost: number | null;
  pnl_cost: number | null;
}

export interface QuotaRampSchedule {
  id: number;
  day_from: number;
  day_to: number | null;
  ramp_pct: number;
}

export interface LeaveCostRate {
  id: number;
  country: string;
  cost_pct: number;
}
