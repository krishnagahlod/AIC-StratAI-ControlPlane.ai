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
      className="bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
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
