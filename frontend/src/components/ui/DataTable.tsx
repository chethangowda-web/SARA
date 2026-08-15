import React from 'react';
import EmptyState from './EmptyState';
import { Database } from 'lucide-react';

export interface Column<T> {
  key: string;
  header: React.ReactNode;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string | number;
  loading?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  onRowClick?: (row: T) => void;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  loading = false,
  emptyTitle = 'No records found',
  emptyDescription = 'There are no entries available for display.',
  onRowClick,
}: DataTableProps<T>) {
  if (loading) {
    return (
      <div className="w-full bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden p-6 space-y-4">
        <div className="h-8 bg-slate-800/60 rounded animate-pulse w-full" />
        <div className="h-12 bg-slate-800/40 rounded animate-pulse w-full" />
        <div className="h-12 bg-slate-800/40 rounded animate-pulse w-full" />
        <div className="h-12 bg-slate-800/40 rounded animate-pulse w-full" />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="border border-slate-800 rounded-2xl p-8 bg-slate-900/40">
        <EmptyState
          icon={<Database className="w-10 h-10 text-slate-500" />}
          title={emptyTitle}
          description={emptyDescription}
        />
      </div>
    );
  }

  return (
    <div className="w-full bg-slate-900/80 border border-slate-800/80 rounded-2xl shadow-xl overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/40 uppercase text-[11px] tracking-wider font-semibold">
            {columns.map((col) => (
              <th key={col.key} className={`px-6 py-4 ${col.className || ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {data.map((row) => (
            <tr
              key={keyExtractor(row)}
              onClick={() => onRowClick && onRowClick(row)}
              className={`transition-colors ${
                onRowClick ? 'hover:bg-slate-800/40 cursor-pointer' : 'hover:bg-slate-800/20'
              }`}
            >
              {columns.map((col) => (
                <td key={col.key} className={`px-6 py-4 text-slate-200 ${col.className || ''}`}>
                  {col.render ? col.render(row) : (row as any)[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;
