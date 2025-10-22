import React from "react";
import { clsx } from "clsx";

type Props = {
  title: string;
  value: string | number;
  className?: string;
};

export default function StatCard({ title, value, className }: Props) {
  return (
    <div className={clsx("rounded-lg border p-4 bg-white dark:bg-gray-800", className)}>
      <div className="text-xs text-gray-500">{title}</div>
      <div className="text-2xl font-semibold">{value}</div>
    </div>
  );
}
