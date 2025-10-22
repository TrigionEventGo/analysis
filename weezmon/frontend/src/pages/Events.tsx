import React, { useState } from "react";
import { apiPost } from "../lib/api";

export default function Events() {
  const [companyGuid, setCompanyGuid] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const sync = async () => {
    const res = await apiPost<{ status: string; count: number }>(`/events/sync?company_guid=${encodeURIComponent(companyGuid)}`);
    setMessage(`Synced ${res.count} events`);
  };
  return (
    <div className="grid gap-4">
      <h1 className="text-xl font-semibold">Events</h1>
      <div className="flex gap-2">
        <input value={companyGuid} onChange={(e) => setCompanyGuid(e.target.value)} placeholder="Company GUID" className="border px-3 py-2 rounded w-80" />
        <button onClick={sync} className="px-4 py-2 rounded bg-blue-600 text-white">Sync</button>
      </div>
      {message && <div className="text-green-600">{message}</div>}
    </div>
  );
}
