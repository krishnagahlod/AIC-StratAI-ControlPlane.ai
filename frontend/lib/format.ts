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

export function riskLevelColor(level: string): string {
  switch (level) {
    case "minimal":
      return "text-emerald-400 bg-emerald-400/10 border-emerald-400/30";
    case "low":
      return "text-sky-400 bg-sky-400/10 border-sky-400/30";
    case "moderate":
      return "text-amber-400 bg-amber-400/10 border-amber-400/30";
    case "critical":
      return "text-rose-400 bg-rose-400/10 border-rose-400/30";
    default:
      return "text-slate-400 bg-slate-400/10 border-slate-400/30";
  }
}

export function severityColor(severity: string): string {
  switch (severity) {
    case "critical":
      return "text-rose-400 bg-rose-400/10 border-rose-400/30";
    case "high":
      return "text-orange-400 bg-orange-400/10 border-orange-400/30";
    case "medium":
      return "text-amber-400 bg-amber-400/10 border-amber-400/30";
    case "low":
      return "text-slate-300 bg-slate-400/10 border-slate-400/30";
    default:
      return "text-slate-300 bg-slate-400/10 border-slate-400/30";
  }
}

export function trustScoreColor(score: number): string {
  if (score >= 90) return "text-emerald-400";
  if (score >= 70) return "text-sky-400";
  if (score >= 30) return "text-amber-400";
  return "text-rose-400";
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
