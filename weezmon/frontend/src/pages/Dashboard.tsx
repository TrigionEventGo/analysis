import React from "react";
import StatCard from "../components/StatCard";
import ChartView from "../components/ChartView";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";

type Health = { status: string };

export default function Dashboard() {
  const { data } = useQuery({ queryKey: ["health"], queryFn: () => apiGet<Health>("/health") });

  return (
    <div className="grid gap-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Total Sales" value={"-"} />
        <StatCard title="Total Refunds" value={"-"} />
        <StatCard title="Active Events" value={"-"} />
        <StatCard title="Backend" value={data?.status ?? "unknown"} />
      </div>
      <ChartView title="Revenue (last 30 days)" />
    </div>
  );
}
