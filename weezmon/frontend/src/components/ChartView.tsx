import React from "react";

type Props = {
  title: string;
};

export default function ChartView({ title }: Props) {
  return (
    <div className="rounded-lg border p-4 bg-white dark:bg-gray-800">
      <div className="text-sm mb-2 font-medium">{title}</div>
      <div className="text-xs text-gray-500">Chart placeholder</div>
    </div>
  );
}
