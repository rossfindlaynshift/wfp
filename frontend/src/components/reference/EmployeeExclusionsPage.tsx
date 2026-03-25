import { RefTablePage } from '../shared/RefTablePage';
import type { EmployeeExclusion } from '../../types/reference';

const columnDefs = [
  { field: 'hibob_id', headerName: 'HiBob ID', type: 'numericColumn' },
  { field: 'display_name', headerName: 'Name', flex: 2 },
  { field: 'job_title', headerName: 'Title', flex: 2 },
  { field: 'department', headerName: 'Department', flex: 2 },
  {
    field: 'excluded', headerName: 'Excluded',
    cellDataType: 'boolean',
    cellRenderer: 'agCheckboxCellRenderer',
    cellEditor: 'agCheckboxCellEditor',
  },
];

export function EmployeeExclusionsPage() {
  return (
    <RefTablePage<EmployeeExclusion>
      title="Employee Exclusions"
      apiPath="employee-exclusions"
      columnDefs={columnDefs}
      defaultRow={() => ({
        hibob_id: 0, display_name: '', job_title: null, department: null, excluded: false,
      })}
      uploadTableName="employee-exclusions"
    />
  );
}
