import { RefTablePage } from '../shared/RefTablePage';
import type { LoadingMultiplier } from '../../types/reference';

const columnDefs = [
  { field: 'legal_entity', headerName: 'Legal Entity', flex: 2 },
  { field: 'default_location', headerName: 'Default Location', flex: 2 },
  { field: 'employer_benefits_pct', headerName: 'Benefits %', type: 'numericColumn',
    valueFormatter: (p: any) => p.value != null ? `${(p.value * 100).toFixed(1)}%` : '' },
  { field: 'employer_taxes_pct', headerName: 'Taxes %', type: 'numericColumn',
    valueFormatter: (p: any) => p.value != null ? `${(p.value * 100).toFixed(1)}%` : '' },
  { field: 'currency', headerName: 'Currency' },
];

export function LoadingMultipliersPage() {
  return (
    <RefTablePage<LoadingMultiplier>
      title="Loading Multipliers (by Legal Entity)"
      apiPath="loading-multipliers"
      columnDefs={columnDefs}
      defaultRow={() => ({
        legal_entity: '', default_location: null,
        employer_benefits_pct: 0, employer_taxes_pct: 0, currency: 'EUR',
      })}
      uploadTableName="loading-multipliers"
    />
  );
}
