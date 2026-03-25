import { RefTablePage } from '../shared/RefTablePage';
import type { BudgetTarget } from '../../types/reference';

const columnDefs = [
  { field: 'l2_function', headerName: 'L2 Function', flex: 2 },
  { field: 'month', headerName: 'Month (YYYY-MM-DD)' },
  { field: 'headcount', headerName: 'Headcount', type: 'numericColumn' },
  {
    field: 'loaded_cost', headerName: 'Loaded Cost (EUR k)', type: 'numericColumn',
    valueFormatter: (p: any) => p.value != null ? p.value.toLocaleString('en', { maximumFractionDigits: 1 }) : '',
  },
  {
    field: 'pnl_cost', headerName: 'P&L Cost (EUR k)', type: 'numericColumn',
    valueFormatter: (p: any) => p.value != null ? p.value.toLocaleString('en', { maximumFractionDigits: 1 }) : '',
  },
];

export function BudgetTargetsPage() {
  return (
    <RefTablePage<BudgetTarget>
      title="Budget Targets (by L2 Function & Month)"
      apiPath="budget-targets"
      columnDefs={columnDefs}
      defaultRow={() => ({
        l2_function: '', month: '2026-01-31', headcount: null, loaded_cost: null, pnl_cost: null,
      })}
      uploadTableName="budget-targets"
    />
  );
}
