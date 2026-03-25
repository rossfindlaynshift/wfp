import { RefTablePage } from '../shared/RefTablePage';
import type { DepartmentHierarchy } from '../../types/reference';

const columnDefs = [
  { field: 'department', headerName: 'Department (HiBob)', flex: 3 },
  { field: 'l1', headerName: 'L1' },
  { field: 'l2', headerName: 'L2' },
  { field: 'l3', headerName: 'L3', flex: 2 },
];

export function DepartmentHierarchyPage() {
  return (
    <RefTablePage<DepartmentHierarchy>
      title="Department Hierarchy"
      apiPath="department-hierarchy"
      columnDefs={columnDefs}
      defaultRow={() => ({ department: '', l1: '', l2: '', l3: '' })}
      uploadTableName="department-hierarchy"
    />
  );
}
