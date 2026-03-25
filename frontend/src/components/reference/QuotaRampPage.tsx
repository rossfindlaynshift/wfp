import { RefTablePage } from '../shared/RefTablePage';
import type { QuotaRampSchedule } from '../../types/reference';

const columnDefs = [
  { field: 'day_from', headerName: 'Day From', type: 'numericColumn' },
  { field: 'day_to', headerName: 'Day To', type: 'numericColumn' },
  {
    field: 'ramp_pct', headerName: 'Ramp %', type: 'numericColumn',
    valueFormatter: (p: any) => p.value != null ? `${(p.value * 100).toFixed(0)}%` : '',
  },
];

export function QuotaRampPage() {
  return (
    <RefTablePage<QuotaRampSchedule>
      title="Quota Ramp Schedule"
      apiPath="quota-ramp-schedule"
      columnDefs={columnDefs}
      defaultRow={() => ({ day_from: 0, day_to: null, ramp_pct: 0 })}
    />
  );
}
