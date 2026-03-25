import { RefTablePage } from '../shared/RefTablePage';
import type { FxRate } from '../../types/reference';

const columnDefs = [
  { field: 'currency', headerName: 'Currency' },
  { field: 'rate_to_eur', headerName: 'Rate to EUR', type: 'numericColumn' },
];

export function FxRatesPage() {
  return (
    <RefTablePage<FxRate>
      title="FX Rates (Budget Rates → EUR)"
      apiPath="fx-rates"
      columnDefs={columnDefs}
      defaultRow={() => ({ currency: '', rate_to_eur: 1.0 })}
      uploadTableName="fx-rates"
    />
  );
}
