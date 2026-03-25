import { RefTablePage } from '../shared/RefTablePage';
import type { LeaveCostRate } from '../../types/reference';

const columnDefs = [
  { field: 'country', headerName: 'Country', flex: 2 },
  {
    field: 'cost_pct', headerName: 'Leave Cost %', type: 'numericColumn',
    valueFormatter: (p: any) => p.value != null ? `${(p.value * 100).toFixed(0)}%` : '',
  },
];

export function LeaveCostRatesPage() {
  return (
    <RefTablePage<LeaveCostRate>
      title="Leave Cost Rates (by Country)"
      apiPath="leave-cost-rates"
      columnDefs={columnDefs}
      defaultRow={() => ({ country: '', cost_pct: 0 })}
      uploadTableName="leave-cost-rates"
    />
  );
}
