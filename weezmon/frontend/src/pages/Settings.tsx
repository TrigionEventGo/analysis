import React from "react";

export default function Settings() {
  return (
    <div className="grid gap-4">
      <h1 className="text-xl font-semibold">Settings</h1>
      <div className="text-sm text-gray-600">Configure tokens, email and report frequency via environment.
        Set VITE_API_BASE, VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY in your env when deploying.</div>
    </div>
  );
}
