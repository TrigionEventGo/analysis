import React from "react";

type Column<T> = {
  key: keyof T;
  header: string;
};

type Props<T> = {
  columns: Column<T>[];
  rows: T[];
};

export default function DataTable<T>({ columns, rows }: Props<T>) {
  return (
    <div className="overflow-auto border rounded-lg">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-100 dark:bg-gray-700">
          <tr>
            {columns.map((c) => (
              <th key={String(c.key)} className="text-left px-3 py-2 font-medium">
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="odd:bg-white even:bg-gray-50 dark:odd:bg-gray-800 dark:even:bg-gray-900">
              {columns.map((c) => (
                <td key={String(c.key)} className="px-3 py-2 border-t">
                  {String(r[c.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
