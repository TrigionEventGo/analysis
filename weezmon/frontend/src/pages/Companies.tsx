import React from "react";
import { useQuery } from "@tanstack/react-query";
import DataTable from "../components/DataTable";
import { apiGet } from "../lib/api";

type Company = { id: string; name?: string; company_guid?: string; is_active?: boolean };

export default function Companies() {
  const { data, isLoading } = useQuery({ queryKey: ["companies"], queryFn: () => apiGet<Company[]>("/companies/") });

  return (
    <div className="grid gap-4">
      <h1 className="text-xl font-semibold">Companies</h1>
      {isLoading ? (
        <div>Loading...</div>
      ) : (
        <DataTable
          columns={[
            { key: "name", header: "Name" },
            { key: "company_guid", header: "Guid" },
            { key: "is_active", header: "Active" },
          ]}
          rows={data || []}
        />
      )}
    </div>
  );
}
