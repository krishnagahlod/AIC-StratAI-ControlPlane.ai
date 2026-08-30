"use client";

import type { AppSummary } from "@/lib/types";

export default function AppFilter({
  apps,
  value,
  onChange,
}: {
  apps: AppSummary[];
  value: number | null;
  onChange: (appId: number | null) => void;
}) {
  return (
    <select
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
      className="bg-white border border-border rounded-xl px-3.5 h-10 text-sm font-medium text-foreground focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent/50 shrink-0"
    >
      <option value="">All Apps</option>
      {apps.map((app) => (
        <option key={app.id} value={app.id}>
          {app.name}
        </option>
      ))}
    </select>
  );
}
