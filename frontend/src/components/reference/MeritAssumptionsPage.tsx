import { RefTablePage } from '../shared/RefTablePage';
import type { MeritAssumption } from '../../types/reference';

const columnDefs = [
  {
    field: 'merit_rate', headerName: 'Merit Rate', type: 'numericColumn',
    valueFormatter: (p: any) => p.value != null ? `${(p.value * 100).toFixed(1)}%` : '',
  },
  { field: 'effective_date', headerName: 'Effective Date' },
  { field: 'joiner_cutoff_date', headerName: 'Joiner Cut-off Date' },
];

export function MeritAssumptionsPage() {
  return (
    <RefTablePage<MeritAssumption>
      title="Merit Assumptions"
      apiPath="merit-assumptions"
      columnDefs={columnDefs}
      defaultRow={() => ({
        merit_rate: 0.03, effective_date: '2026-04-01', joiner_cutoff_date: '2025-09-29',
      })}
    />
  );
}
