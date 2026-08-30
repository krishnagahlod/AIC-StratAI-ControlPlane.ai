export function formatUsd(value: number): string {
  if (Math.abs(value) < 1) return `$${value.toFixed(4)}`;
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

export function formatRelativeTime(iso: string): string {
  const then = new Date(iso.endsWith("Z") ? iso : `${iso}Z`).getTime();
  const diffMs = Date.now() - then;
  const diffSec = Math.round(diffMs / 1000);
  if (diffSec < 5) return "just now";
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.round(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.round(diffHr / 24);
  return `${diffDay}d ago`;
}

// Status palette — fixed, distinct from the chart categorical series, per the
// dataviz skill's rule that a status color must never impersonate a series.
export function riskLevelColor(level: string): string {
  switch (level) {
    case "minimal":
      return "text-emerald-700 bg-emerald-50 border-emerald-200";
    case "low":
      return "text-sky-700 bg-sky-50 border-sky-200";
    case "moderate":
      return "text-amber-800 bg-amber-50 border-amber-200";
    case "critical":
      return "text-rose-700 bg-rose-50 border-rose-200";
    default:
      return "text-muted bg-surface-2 border-border";
  }
}

export function severityColor(severity: string): string {
  switch (severity) {
    case "critical":
      return "text-rose-700 bg-rose-50 border-rose-200";
    case "high":
      return "text-orange-800 bg-orange-50 border-orange-200";
    case "medium":
      return "text-amber-800 bg-amber-50 border-amber-200";
    case "low":
      return "text-slate-600 bg-slate-50 border-slate-200";
    default:
      return "text-slate-600 bg-slate-50 border-slate-200";
  }
}

export function trustScoreColor(score: number): string {
  if (score >= 90) return "text-emerald-600";
  if (score >= 70) return "text-sky-600";
  if (score >= 30) return "text-amber-600";
  return "text-rose-600";
}

export function decisionLabel(decision: string): string {
  return decision
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

export function flagLabel(type: string): string {
  return type
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}
