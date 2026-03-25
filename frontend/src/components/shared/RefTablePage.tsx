import { useState, useEffect, useCallback, useRef } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community';
import type { ColDef, CellValueChangedEvent } from 'ag-grid-community';
import { Plus, Trash2, Upload, Save } from 'lucide-react';
import { api } from '../../services/api';

ModuleRegistry.registerModules([AllCommunityModule]);

interface RefTablePageProps<T extends { id: number }> {
  title: string;
  apiPath: string;
  columnDefs: ColDef[];
  defaultRow: () => Omit<T, 'id'>;
  uploadTableName?: string;
}

export function RefTablePage<T extends { id: number }>({
  title,
  apiPath,
  columnDefs,
  defaultRow,
  uploadTableName,
}: RefTablePageProps<T>) {
  const [rows, setRows] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dirty, setDirty] = useState<Set<number>>(new Set());
  const [newRows, setNewRows] = useState<Set<number>>(new Set());
  const fileInput = useRef<HTMLInputElement>(null);
  const gridRef = useRef<AgGridReact>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.get<T[]>(`/ref/${apiPath}`);
      setRows(data);
      setDirty(new Set());
      setNewRows(new Set());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [apiPath]);

  useEffect(() => { load(); }, [load]);

  const onCellValueChanged = useCallback((e: CellValueChangedEvent) => {
    setDirty(prev => new Set(prev).add(e.data.id));
  }, []);

  const addRow = useCallback(() => {
    const tempId = -(Date.now());
    const row = { ...defaultRow(), id: tempId } as T;
    setRows(prev => [...prev, row]);
    setNewRows(prev => new Set(prev).add(tempId));
    setDirty(prev => new Set(prev).add(tempId));
  }, [defaultRow]);

  const saveAll = useCallback(async () => {
    setError('');
    try {
      for (const id of dirty) {
        const row = rows.find(r => r.id === id);
        if (!row) continue;
        const { id: _id, ...data } = row as any;
        if (newRows.has(id)) {
          await api.post(`/ref/${apiPath}`, data);
        } else {
          await api.put(`/ref/${apiPath}/${id}`, data);
        }
      }
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  }, [dirty, newRows, rows, apiPath, load]);

  const deleteSelected = useCallback(async () => {
    const selected = gridRef.current?.api.getSelectedRows() || [];
    setError('');
    try {
      for (const row of selected) {
        if (newRows.has(row.id)) {
          setRows(prev => prev.filter(r => r.id !== row.id));
        } else {
          await api.delete(`/ref/${apiPath}/${row.id}`);
        }
      }
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  }, [apiPath, load, newRows]);

  const handleUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !uploadTableName) return;
    setError('');
    try {
      await api.upload(`/ref/upload/${uploadTableName}`, file);
      await load();
    } catch (err: any) {
      setError(err.message);
    }
    e.target.value = '';
  }, [uploadTableName, load]);

  const cols: ColDef[] = [
    { headerCheckboxSelection: true, checkboxSelection: true, width: 50, pinned: 'left' },
    ...columnDefs.map(c => ({ ...c, editable: c.editable !== false, flex: c.flex ?? 1 })),
  ];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-800">{title}</h2>
        <div className="flex gap-2">
          {uploadTableName && (
            <>
              <input ref={fileInput} type="file" accept=".xlsx,.csv" className="hidden" onChange={handleUpload} />
              <button
                onClick={() => fileInput.current?.click()}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                <Upload size={14} /> Upload Excel
              </button>
            </>
          )}
          <button
            onClick={addRow}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <Plus size={14} /> Add Row
          </button>
          <button
            onClick={deleteSelected}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-white border border-red-300 text-red-600 rounded-md hover:bg-red-50"
          >
            <Trash2 size={14} /> Delete
          </button>
          <button
            onClick={saveAll}
            disabled={dirty.size === 0}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Save size={14} /> Save Changes
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 text-red-700 text-sm rounded">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200" style={{ height: 'calc(100vh - 200px)' }}>
        <AgGridReact
          ref={gridRef}
          rowData={rows}
          columnDefs={cols}
          defaultColDef={{
            sortable: true,
            filter: true,
            resizable: true,
          }}
          rowSelection="multiple"
          onCellValueChanged={onCellValueChanged}
          getRowId={params => String(params.data.id)}
          loading={loading}
        />
      </div>
    </div>
  );
}
