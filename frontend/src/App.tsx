import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/shared/Layout';
import { FxRatesPage } from './components/reference/FxRatesPage';
import { LoadingMultipliersPage } from './components/reference/LoadingMultipliersPage';
import { DepartmentHierarchyPage } from './components/reference/DepartmentHierarchyPage';
import { EmployeeExclusionsPage } from './components/reference/EmployeeExclusionsPage';
import { MeritAssumptionsPage } from './components/reference/MeritAssumptionsPage';
import { BudgetTargetsPage } from './components/reference/BudgetTargetsPage';
import { QuotaRampPage } from './components/reference/QuotaRampPage';
import { LeaveCostRatesPage } from './components/reference/LeaveCostRatesPage';

function OverviewPage() {
  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Workforce Planning</h2>
      <p className="text-gray-600 mb-6">
        Manage reference tables, take census snapshots, and forecast people costs.
      </p>
      <div className="grid grid-cols-2 gap-4 max-w-2xl">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="font-medium text-gray-800">Reference Tables</h3>
          <p className="text-sm text-gray-500 mt-1">
            FX rates, loading multipliers, department hierarchy, and more.
            Use the sidebar to manage each table.
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4 opacity-50">
          <h3 className="font-medium text-gray-800">Census Snapshots</h3>
          <p className="text-sm text-gray-500 mt-1">Coming in Phase 2</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4 opacity-50">
          <h3 className="font-medium text-gray-800">People Forecast</h3>
          <p className="text-sm text-gray-500 mt-1">Coming in Phase 3</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4 opacity-50">
          <h3 className="font-medium text-gray-800">Exec Dashboard</h3>
          <p className="text-sm text-gray-500 mt-1">Coming in Phase 4</p>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/ref/fx-rates" element={<FxRatesPage />} />
          <Route path="/ref/loading-multipliers" element={<LoadingMultipliersPage />} />
          <Route path="/ref/department-hierarchy" element={<DepartmentHierarchyPage />} />
          <Route path="/ref/employee-exclusions" element={<EmployeeExclusionsPage />} />
          <Route path="/ref/merit-assumptions" element={<MeritAssumptionsPage />} />
          <Route path="/ref/budget-targets" element={<BudgetTargetsPage />} />
          <Route path="/ref/quota-ramp" element={<QuotaRampPage />} />
          <Route path="/ref/leave-cost-rates" element={<LeaveCostRatesPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
