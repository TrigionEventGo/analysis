import React, { useState } from "react";
import { apiGet, apiPost } from "../lib/api";
import { useQuery } from "@tanstack/react-query";

type Log = { id: number; company_guid: string; total_sales: number; total_refunds: number; created_at: string };

export default function Reports() {
  const [companyGuid, setCompanyGuid] = useState("");
  const { data, refetch, isFetching } = useQuery({ queryKey: ["reportLogs"], queryFn: () => apiGet<Log[]>("/reports/logs") });

  const run = async () => {
    await apiPost(`/reports/generate?company_guid=${encodeURIComponent(companyGuid)}`);
    setTimeout(() => refetch(), 1500);
  };

  return (
    <div className="grid gap-4">
      <h1 className="text-xl font-semibold">Reports</h1>
      <div className="flex gap-2">
        <input value={companyGuid} onChange={(e) => setCompanyGuid(e.target.value)} placeholder="Company GUID" className="border px-3 py-2 rounded w-80" />
        <button onClick={run} className="px-4 py-2 rounded bg-blue-600 text-white">Run report</button>
        <button onClick={() => refetch()} className="px-4 py-2 rounded border">Refresh</button>
      </div>
      {isFetching ? (
        <div>Loading...</div>
      ) : (
        <div className="space-y-2">
          {(data || []).map((l) => (
            <div key={l.id} className="border rounded p-3 bg-white dark:bg-gray-800">
              <div className="text-sm">{l.company_guid}</div>
              <div className="text-xs text-gray-500">{new Date(l.created_at).toLocaleString()}</div>
              <div className="text-sm">Sales: {l.total_sales} | Refunds: {l.total_refunds}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
