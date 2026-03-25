# Workforce Planning Application — Implementation Plan

## Overview

A web application replacing the existing nShift workforce planning spreadsheet. Built with a **Python/FastAPI backend** and **React frontend**, running locally on macOS. The app manages census snapshots from HiBob, forecasts people costs over a rolling 24-month horizon, and provides real-time executive dashboards with budget comparison.

---

## Architecture

```
┌─────────────────────────────────────┐
│           React Frontend            │
│  (Vite + TypeScript + TailwindCSS)  │
│  AG Grid (tables) + Recharts (viz)  │
└──────────────┬──────────────────────┘
               │ REST API (JSON)
┌──────────────▼──────────────────────┐
│         FastAPI Backend             │
│  Census / Forecast / Ref / Export   │
│  Cost calculation engine            │
└──────────────┬──────────────────────┘
               │ SQLAlchemy ORM
┌──────────────▼──────────────────────┐
│           SQLite Database           │
│  (PostgreSQL-ready for future)      │
└─────────────────────────────────────┘
```

**Why these choices:**
- **FastAPI** — async, fast, auto-generates API docs, good for data-heavy apps
- **SQLite** — zero-config for local use; the schema will be PostgreSQL-compatible for future migration
- **AG Grid (Community)** — handles 400+ row editable tables with sorting/filtering, closest to the spreadsheet UX a CFO expects
- **Recharts** — lightweight charting for dashboard visualisations
- **Vite + TypeScript** — fast dev server, type safety on the frontend

---

## Data Model (Core Tables)

### Census & People

| Table | Purpose |
|---|---|
| `employees` | Master record per HiBob employee ID. Stores immutable identity fields. |
| `census_snapshots` | One row per employee per snapshot period. Stores all point-in-time data (salary, department, title, etc.) as at month-end. |
| `employee_exclusions` | All HiBob employees with fields: HiBob ID, name, title, department, excluded (yes/no). New employees are flagged for exclusion decision during snapshot. User-editable at any time via ref tables. Excluded employees are omitted from cost calculations (e.g., contractors paid via invoicing). |

### Forecast

| Table | Purpose |
|---|---|
| `forecast_adjustments` | User-entered changes to existing employees: future leave dates, salary changes, effective dates. Linked to employee ID. Carry forward across census refreshes until resolved. |
| `open_roles` | New hires from Teamtailor spreadsheet import or backfill placeholders. Same data model as census. Source field distinguishes: `backfill`, `open_req`. |
| `backfill_decisions` | Tracks user decisions on leaver backfills (accepted/declined) to avoid re-prompting. Links leaver employee ID to open_role ID if accepted. |
| `forecast_versions` | Named snapshots of forecast state. Stores: version name, timestamp, base census period, and a frozen copy of all inputs (adjustments, open roles, backfills, ref table values) as a JSON blob. The calculation engine can run against any saved version instead of live state. |

### Reference

| Table | Purpose |
|---|---|
| `fx_rates` | Currency → EUR budget rate. Single set, updateable. |
| `loading_multipliers` | Legal entity → employer benefits %, employer taxes %, currency. | 
| `department_hierarchy` | HiBob department ID → L1 (R&D/S&M/G&A/COGS), L2 (Sales/Marketing/etc.), L3 (Nordic Sales/etc.). |
| `merit_assumptions` | Global merit increase rate + effective date + joiner cut-off date. |
| `budget_targets` | Monthly budget figures by L2 function: headcount, loaded cost, P&L cost. |
| `quota_ramp_schedule` | Up to 5 ramp points: day threshold → ramp %. Single global schedule. |
| `leave_cost_rates` | Country → leave cost % (e.g., Sweden = 20%, UK = 0%). Applied as a percentage of normal loaded cost while an employee is on leave. |

> **All reference tables are fully user-editable** via the UI — inline editing in grids, bulk Excel/CSV upload, and individual add/edit/delete. Changes take effect immediately and trigger forecast recalculation.

### Key Census Snapshot Fields

From HiBob + calculated:

| Field | Source |
|---|---|
| `source` | Census / Open Req / Backfill |
| `employment_type` | HiBob (Employee / Consultant) |
| `employee_id` | HiBob |
| `display_name` | HiBob |
| `job_title` | HiBob |
| `legal_entity` | HiBob |
| `site` | HiBob |
| `department` | HiBob |
| `start_date` | HiBob |
| `future_leave_date` | HiBob (if resigned) |
| `currency` | HiBob |
| `salary_local` | HiBob (annual, pro-rated for part-time) |
| `commission` | HiBob (annual OTE at 100%) |
| `bonus` | HiBob (annual, fixed amount) |
| `weekly_hours` | HiBob |
| `notice_period` | HiBob |
| `business_unit` | HiBob |
| `team` | HiBob |
| `manager_id` | HiBob |
| `snapshot_period` | End-of-month date |
| `quota_type` | HiBob (Direct QC / Overlay / None) |
| `quota_amount` | HiBob |
| `quota_ramp_start_date` | HiBob |
| `leave_type` | User-entered (e.g., Parental Leave, Study Leave, Sabbatical, etc.) — null if not on leave |
| `leave_start_date` | User-entered — date leave begins |
| `leave_end_date` | User-entered — date leave ends (null if open-ended) |
| **Calculated fields** | |
| `l1`, `l2`, `l3` | Looked up from `department_hierarchy` |
| `country` | Derived from `site` via ref table |
| `fx_rate` | Looked up from `fx_rates` by currency |
| `salary_eur` | `salary_local / fx_rate` |
| `incentive_otv_eur` | `(commission or bonus) / fx_rate` — whichever is non-zero |
| `incentive_attainment` | 0.8 for commission roles, 1.0 for bonus roles |
| `incentive_eur` | `incentive_otv_eur × incentive_attainment` |
| `employer_benefits` | `(salary_eur + incentive_otv_eur) × benefits_rate` from loading table |
| `employer_taxes` | `(salary_eur + incentive_otv_eur) × tax_rate` from loading table |
| `loaded_cost` | `salary_eur + incentive_eur + employer_benefits + employer_taxes` |
| `monthly_cost` | `loaded_cost / 12` |

---

## Cost Calculation Engine

### Point-in-Time (Loaded) Cost
The annualised fully-loaded cost of an employee as at a given date:

```
loaded_cost = salary_eur + incentive_eur + employer_benefits + employer_taxes
```

Where:
- `incentive_eur = incentive_otv_eur × attainment` (0.8 for sales/commission, 1.0 for bonus)
- `employer_benefits = (salary_eur + incentive_otv_eur) × benefits_rate`
- `employer_taxes = (salary_eur + incentive_otv_eur) × tax_rate`
- Benefits/tax rates come from `loading_multipliers` by legal entity

### P&L Monthly Cost
The cost that hits the income statement in a given month:

```
monthly_pnl = loaded_cost / 12                      (if employed and NOT on leave)
monthly_pnl = (loaded_cost / 12) × leave_cost_%     (if employed and ON leave)
monthly_pnl = 0                                      (if not employed that month)
```

An employee is "employed in month M" if:
- `start_date` is on or before the last day of month M, AND
- `future_leave_date` is null OR falls in a month after M

An employee is "on leave in month M" if:
- `leave_start_date` is on or before the last day of month M, AND
- `leave_end_date` is null OR falls in a month equal to or after M

The `leave_cost_%` is looked up from the `leave_cost_rates` ref table by the employee's country.

No mid-month proration — a leaver/joiner in month M counts for the full month. Same for leave start/end.

### Merit Increase
Applied once per year on **1 April** (configurable in merit assumptions ref table):
- All employees with `start_date` on or before the joiner cut-off date receive the merit increase
- `salary_local_new = salary_local × (1 + merit_rate)`
- Recalculates all derived cost fields from the effective date forward
- Default effective date: 1 April. Default joiner cut-off: configurable (e.g., 29 September of the prior year)

### Forecast Period Logic
For each of the 24 rolling months, the engine computes headcount and cost by combining:
1. **Census employees** — from the latest snapshot
2. **Forecast adjustments** — user-entered leave dates or salary changes for existing employees
3. **Open roles & backfills** — with their expected start dates

---

## Implementation Phases

### Phase 1: Foundation & Data Model
**Goal:** Project scaffolding, database schema, reference table management, and CSV/Excel import infrastructure.

**Backend:**
- [ ] Initialise FastAPI project with SQLAlchemy + SQLite
- [ ] Define all database models (see Data Model section)
- [ ] Create Alembic migration setup for schema versioning
- [ ] Build CRUD API endpoints for reference tables:
  - `GET/POST/PUT /api/ref/fx-rates` — currency → EUR rates
  - `GET/POST/PUT /api/ref/loading-multipliers` — legal entity → benefits %, taxes %, currency
  - `GET/POST/PUT /api/ref/department-hierarchy` — department → L1/L2/L3
  - `GET/PUT /api/ref/employee-exclusions` — all HiBob employees with excluded yes/no flag (bulk toggle)
  - `GET/POST/PUT /api/ref/merit-assumptions` — rate, effective date, joiner cut-off
  - `GET/POST/PUT /api/ref/budget-targets` — monthly budget by L2
  - `GET/POST/PUT /api/ref/leave-cost-rates` — country → leave cost % of normal loaded cost
  - `GET/POST/PUT /api/ref/quota-ramp-schedule` — day thresholds → ramp %
- [ ] Build Excel/CSV upload endpoint for bulk ref table loading
- [ ] Seed database with reference data from the existing spreadsheet's `ref` tab

**Frontend:**
- [ ] Initialise React + Vite + TypeScript project
- [ ] Set up TailwindCSS + component library (shadcn/ui)
- [ ] Build reference table management UI — editable grid for each ref table
- [ ] Build Excel upload component for bulk loading

**Deliverable:** Running app where you can view and edit all reference tables.

---

### Phase 2: Census Snapshots
**Goal:** Pull monthly census snapshots from HiBob via API, detect changes, and prompt for backfill decisions.

#### User Journey: Month-End Snapshot

The user clicks **"Take Snapshot"** at the end of each month. The app then:

1. **Pulls data from HiBob API** — fetches all active employees with their current attributes
2. **Checks for new employees** — any HiBob ID not yet in the `employee_exclusions` table is flagged as new
3. **Prompts for exclusion decisions** — for each new employee, shows name, title, department and asks: "Exclude from workforce plan?" (yes/no). Adds them to the `employee_exclusions` table with the user's decision.
4. **Filters** — removes employees marked as excluded in the `employee_exclusions` table
5. **Enriches** — looks up L1/L2/L3, FX rates, loading multipliers; calculates all cost fields
6. **Compares to previous snapshot** — identifies:
   - **Leavers:** present last month, absent now (or newly have a future leave date)
   - **Joiners:** absent last month, present now (and not excluded)
   - **Changes:** department moves, salary changes, title changes, etc.
7. **Presents a summary screen** showing all changes with counts
8. **Prompts for backfill decisions** — for each leaver, asks: "Create backfill placeholder?" with duplicate detection against existing open roles
9. **Saves the snapshot** once the user confirms

After the snapshot, the user typically reviews forecast adjustments (update future leavers, salary changes, etc.) before exec review sessions.

#### User Journey: Exec Review Sessions

The user walks each exec through their function's dashboard, making live updates:
- Add/edit forecast leavers or salary changes advised by the exec
- Adjust open role timing or details
- All changes reflect immediately in the dashboard and forecast

**Backend:**
- [ ] HiBob API client (`services/hibob.py`):
  - Authenticate with API key (stored in app config)
  - `GET` all active employees with required fields
  - Map HiBob field names to census schema
  - Handle pagination if >400 employees
- [ ] Snapshot endpoint: `POST /api/census/take-snapshot`
  - Calls HiBob API to pull current employee data
  - Identifies new HiBob IDs not yet in `employee_exclusions` table
  - Returns new employees requiring exclusion decisions (if any) — pauses here until resolved
- [ ] Exclusion decisions endpoint: `POST /api/census/exclusion-decisions`
  - Accepts user's yes/no exclusion decisions for new employees
  - Saves to `employee_exclusions` table
  - Proceeds with snapshot: filters excluded employees, enriches with calculated fields
  - Compares against previous snapshot to produce a change report
  - Returns change summary (leavers, joiners, department changes, salary changes) — does NOT save yet
- [ ] Snapshot confirm endpoint: `POST /api/census/confirm-snapshot`
  - Saves the snapshot after user reviews changes and makes backfill decisions
  - Creates backfill placeholders for accepted leavers
  - Records declined backfills to avoid re-prompting
- [ ] Census query endpoints:
  - `GET /api/census/snapshots` — list all snapshot periods
  - `GET /api/census/{period}` — full employee list for a snapshot
  - `GET /api/census/diff/{period_a}/{period_b}` — changes between any two snapshots
- [ ] Historical census import: `POST /api/census/import` — one-time Excel upload to seed historical snapshots from the existing spreadsheet (for initial data load only)

**Frontend:**
- [ ] **Take Snapshot page:**
  - "Take Snapshot" button with period selector (defaults to current month-end)
  - Progress indicator while HiBob API call runs
  - **New employee exclusion screen** (if new HiBob IDs detected):
    - Table showing each new employee: HiBob ID, name, title, department
    - Excluded toggle (yes/no) for each — defaults to "No" (included)
    - "Confirm & Continue" button to save decisions and proceed
  - **Change summary screen** after exclusion decisions are saved:
    - Headline stats: X leavers, Y joiners, Z changes
    - Leavers tab: list of departed employees with last-known details
    - Joiners tab: list of new employees
    - Changes tab: employees with changed department, salary, title, etc. (showing old → new)
  - **Backfill prompt** for each leaver:
    - Pre-filled backfill details (inherited from leaver)
    - Accept / Decline / Edit-then-accept
    - Duplicate warning if similar open role already exists
  - "Confirm & Save Snapshot" button
- [ ] **Census browser** — select any historical snapshot period, view full employee grid
- [ ] **Snapshot comparison view** — pick two periods, see side-by-side diff

**Deliverable:** One-click monthly census from HiBob with automated change detection and backfill workflow.

---

### Phase 3: People Forecast
**Goal:** Manage open roles, backfills, and forecast adjustments to project headcount and costs 24 months forward.

**Backend:**
- [ ] Open roles endpoints:
  - `POST /api/forecast/open-roles/import` — bulk import from Teamtailor spreadsheet
  - `GET/POST/PUT/DELETE /api/forecast/open-roles` — CRUD for individual roles
  - Open roles share the same data model as census records (source = `open_req`)
- [ ] Backfill endpoints:
  - `POST /api/forecast/backfills` — create backfill from a leaver (inherits all attributes, start date = leaver's leave date, editable)
  - `PUT /api/forecast/backfills/{id}` — edit backfill details
  - `GET /api/forecast/backfill-decisions` — track which leavers have been addressed
  - Duplicate detection: when creating a backfill, check against existing open roles by department + job title + approximate start date
- [ ] Forecast adjustment endpoints:
  - `POST /api/forecast/adjustments` — add a leave date, salary change, or leave period for an existing employee
  - `GET /api/forecast/adjustments` — list all active adjustments
  - `PUT/DELETE /api/forecast/adjustments/{id}` — edit or remove
  - Adjustment types: `future_leave_date`, `salary_change`, `leave_of_absence`
  - Leave of absence fields: leave type (free text, e.g., Parental Leave, Study Leave, Sabbatical), start date, end date (optional — null = open-ended)
  - On new census import: flag adjustments that may be outdated (e.g., employee already left, salary already changed, leave ended) and prompt user to review
- [ ] **Forecast calculation engine** — the core of the app:
  - `GET /api/forecast/calculate` — returns a 24-month projection
  - For each month in the rolling window:
    1. Start with latest census employees
    2. Apply forecast adjustments (leave dates, salary changes, leaves of absence)
    3. Apply merit increases (if effective date falls in or before the month, and employee joined before cut-off)
    4. Add open roles and backfills (if start date is on or before month-end)
    5. Determine leave status for each employee — apply country-specific leave cost % for those on leave
    6. Calculate: headcount, loaded cost, monthly P&L cost (reduced for employees on leave)
    7. Group by L1, L2, L3
  - Returns per-month: headcount, loaded cost, P&L cost — broken down by function hierarchy
  - Also returns per-employee monthly presence (1/0) and monthly cost — for the detailed grid
  - **The forecast is calculated on-the-fly, not stored.** Every view pulls fresh numbers from the current state of census + adjustments + open roles + ref tables. ~400 people × 24 months computes in milliseconds — no batch recalculation needed.
  - Accepts optional `version_id` parameter — if provided, runs against frozen inputs from that saved version instead of live state
- [ ] **Forecast versioning:**
  - `POST /api/forecast/versions` — save current state as a named version (e.g., "Board Pack March 2026"). Freezes a JSON snapshot of all adjustments, open roles, backfills, and ref table values, plus a pointer to the base census period.
  - `GET /api/forecast/versions` — list all saved versions
  - `GET /api/forecast/versions/{id}` — retrieve a saved version's frozen inputs
  - `DELETE /api/forecast/versions/{id}` — delete a saved version
  - `GET /api/forecast/compare?live=true&version_id=X` — returns side-by-side calculation of live forecast vs. a saved version, with deltas per month per function

**Frontend:**
- [ ] Open roles management page:
  - Spreadsheet upload for bulk import
  - Editable grid showing all open roles with same columns as census
  - Add/edit/delete individual roles
- [ ] Backfill management:
  - List of leavers pending backfill decision
  - One-click "create backfill" that pre-fills from leaver data
  - Edit backfill details before confirming
  - Duplicate warning if similar open role exists
- [ ] Forecast adjustments page:
  - Select an employee from census → add:
    - Future leave date (resignation)
    - Salary change with effective date
    - Leave of absence: type (free text), start date, end date (optional)
  - List of all active adjustments with ability to edit/remove, grouped by type
  - Visual indicator on employees currently on leave or with upcoming leave
  - Stale adjustment warnings after new census import
- [ ] **Forecast grid view** — the main planning view:
  - Rows = all people (census + open roles + backfills)
  - Columns = person details + 24 monthly columns showing presence (headcount) and cost
  - Filterable by L1/L2/L3, source (census/open req/backfill), employment type
  - Real-time recalculation as adjustments are made
  - Summary row at top showing totals

- [ ] **Forecast versioning UI:**
  - "Save Forecast Version" button — prompts for a name, saves current state
  - Version selector dropdown: "Live" (default) + all saved versions
  - When a saved version is selected, the forecast grid shows that version's numbers (read-only)
  - "Compare to Version" mode — split view showing live vs. saved, with delta columns (green = saving, red = increase)

**Deliverable:** Full people forecast — import open roles, create backfills, make adjustments, see 24-month cost projection. Save and compare forecast versions.

---

### Phase 4: Executive Dashboard
**Goal:** Real-time dashboard showing each function's headcount and cost — actuals, forecast, and budget comparison.

**Backend:**
- [ ] Dashboard data endpoint: `GET /api/dashboard`
  - Parameters: L1 filter (optional), L2 filter (optional), L3 filter (optional), as-of date
  - Returns:
    - **Headcount roll-forward** by month: opening, leavers, joiners, closing — split by employee/consultant
    - **Loaded cost roll-forward** by month: opening, leaver cost removed, joiner cost added, merit/rate changes, closing
    - **Monthly P&L cost** by month
    - **Budget comparison**: forecast vs. budget for headcount, loaded cost, monthly cost — with variance
    - **Prior month actuals** (from census): headcount, loaded cost, P&L cost
    - **YTD actuals**: sum of monthly P&L costs for months with census data in the current fiscal year
    - **Full year forecast**: YTD actuals + remaining months forecast
  - Breakdowns by L2 function and L3 sub-function
- [ ] Summary metrics endpoint: `GET /api/dashboard/summary`
  - Total headcount, total loaded cost, total monthly run-rate
  - Variance to budget (headcount and cost)
  - Leavers YTD (actual) + forecast leavers remaining
  - Joiners YTD (actual) + forecast joiners remaining

**Frontend:**
- [ ] Dashboard layout with function selector (dropdown: All / Sales / Marketing / Customer Service / Professional Services / Hosting / R&D / G&A)
- [ ] **Headcount section:**
  - Headcount roll-forward table (opening → leavers → joiners → closing) by month
  - Employee vs. consultant split
  - Line chart: forecast headcount vs. budget headcount
- [ ] **Loaded cost section:**
  - Cost roll-forward table by month
  - Bar chart: forecast loaded cost vs. budget
  - Variance highlight (green = under budget, red = over)
- [ ] **P&L cost section:**
  - Monthly cost table
  - Stacked bar chart by L2 function
  - Variance to budget
- [ ] **Summary cards** at top:
  - Current headcount | Loaded cost (annualised) | Monthly run-rate
  - Prior month actual | YTD actual | Full year forecast
  - Forecast leavers | Forecast joiners | Net change
- [ ] **L3 drill-down:** click an L2 function to see L3 breakdown
- [ ] **Version comparison on dashboard:** same version selector as forecast grid — view any saved version's dashboard, or compare live vs. saved with delta highlights
- [ ] All figures update in real-time as forecast adjustments are made

**Deliverable:** Live executive dashboard with budget comparison, version comparison, filterable by function.

---

### Phase 5: Model Export & Polish
**Goal:** Export view matching the "model update" sheet format, plus UX refinements.

**Backend:**
- [ ] Export endpoint: `GET /api/export/model-update`
  - Returns monthly time-series (up to 36 months: 12 historical + 24 forecast) of:
    - Headcount by L2 function
    - Salary cost by L2 function
    - Loaded cost (excl. incentive) by L2 function
    - Incentive cost by L2 function
    - Total loaded cost by L2 function
  - Format: JSON (for UI display) + Excel download option
- [ ] Excel export endpoint: `GET /api/export/model-update/excel`
  - Generates an Excel file matching the "model update" sheet structure
  - Historical months populated from census snapshots
  - Forecast months from the calculation engine

**Frontend:**
- [ ] Model export page — table view matching the model update sheet layout
- [ ] Download as Excel button
- [ ] Date range selector (fiscal year)

**Deliverable:** Exportable model update view for downstream financial modelling.

---

## Version 2 Backlog (Out of Scope for V1)

- [ ] Quota ramp calculation (ramped quota = full quota × ramp% based on days since ramp start)
- [ ] Scenario modelling ("what if we delay these 3 hires by 2 months")
- [ ] Teamtailor API integration (replace spreadsheet import)
- [ ] Multi-user access with role-based permissions (exec sees only their function)
- [ ] PostgreSQL migration for server deployment
- [ ] Audit trail / change history
- [ ] NetSuite or FP&A system export integration
- [ ] Merit increase dimensions beyond a single global rate (by region, level, etc.)

---

## Project Structure

```
wfp/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings, DB connection
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── census.py
│   │   │   ├── forecast.py
│   │   │   └── reference.py
│   │   ├── routers/             # API route handlers
│   │   │   ├── census.py
│   │   │   ├── forecast.py
│   │   │   ├── dashboard.py
│   │   │   ├── reference.py
│   │   │   └── export.py
│   │   ├── services/            # Business logic
│   │   │   ├── census_import.py
│   │   │   ├── cost_engine.py   # Core cost calculation
│   │   │   ├── forecast.py
│   │   │   └── hibob.py         # HiBob API client
│   │   ├── schemas/             # Pydantic request/response models
│   │   └── utils/
│   ├── alembic/                 # DB migrations
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── census/          # Census views
│   │   │   ├── forecast/        # Forecast grid, adjustments
│   │   │   ├── dashboard/       # Executive dashboard
│   │   │   ├── reference/       # Ref table editors
│   │   │   └── shared/          # Common components
│   │   ├── hooks/               # React hooks for API calls
│   │   ├── services/            # API client
│   │   ├── types/               # TypeScript interfaces
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── data/                        # SQLite DB + seed files
├── plan.md
└── README.md
```

---

## Running Locally

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev   # → http://localhost:5173
```

---

## Phase Sequence & Dependencies

```
Phase 1 (Foundation) ──→ Phase 2 (Census) ──→ Phase 3 (Forecast) ──→ Phase 4 (Dashboard)
                                                                           │
                                                                           ▼
                                                                    Phase 5 (Export)
```

Each phase builds on the previous and produces a usable deliverable. Phase 1 can be started immediately.
