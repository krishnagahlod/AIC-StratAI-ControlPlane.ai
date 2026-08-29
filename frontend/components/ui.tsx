import { flagLabel, severityColor, trustScoreColor } from "@/lib/format";
import type { Flag } from "@/lib/types";

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-surface border border-border rounded-xl p-5 ${className}`}>{children}</div>
  );
}

export function StatCard({
  label,
  value,
  sub,
  accentClass,
}: {
  label: string;
  value: string;
  sub?: string;
  accentClass?: string;
}) {
  return (
    <Card>
      <div className="text-xs uppercase tracking-wide text-muted mb-2">{label}</div>
      <div className={`text-2xl font-semibold ${accentClass ?? ""}`}>{value}</div>
      {sub && <div className="text-xs text-muted mt-1">{sub}</div>}
    </Card>
  );
}

export function PageHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-xl font-semibold">{title}</h1>
      {description && <p className="text-sm text-muted mt-1">{description}</p>}
    </div>
  );
}

export function TrustRing({ score, size = 64 }: { score: number; size?: number }) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);
  const colorClass = trustScoreColor(score);
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="var(--border)" strokeWidth={6} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={6}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={colorClass}
        />
      </svg>
      <div className={`absolute inset-0 flex items-center justify-center text-sm font-semibold ${colorClass}`}>
        {Math.round(score)}
      </div>
    </div>
  );
}

export function FlagChip({ flag }: { flag: Flag }) {
  return (
    <span
      title={flag.detail}
      className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md border ${severityColor(flag.severity)}`}
    >
      {flagLabel(flag.type)}
      <span className="opacity-60">· {flag.method === "llm_judge" ? "LLM judge" : flag.method === "deterministic" ? "rule" : "rule"}</span>
    </span>
  );
}

export function FlagList({ flags }: { flags: Flag[] }) {
  if (!flags || flags.length === 0) {
    return <span className="text-xs text-muted">No issues detected</span>;
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {flags.map((f, i) => (
        <FlagChip key={i} flag={f} />
      ))}
    </div>
  );
}

export function Badge({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center text-xs px-2 py-0.5 rounded-md border ${className}`}>
      {children}
    </span>
  );
}

export function Button({
  children,
  onClick,
  variant = "primary",
  disabled,
  type = "button",
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "danger" | "ghost";
  disabled?: boolean;
  type?: "button" | "submit";
}) {
  const base = "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed";
  const styles: Record<string, string> = {
    primary: "bg-accent text-white hover:bg-accent/90",
    secondary: "bg-surface-2 text-foreground border border-border hover:bg-border/40",
    danger: "bg-rose-500/15 text-rose-300 border border-rose-500/30 hover:bg-rose-500/25",
    ghost: "text-muted hover:text-foreground",
  };
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={`${base} ${styles[variant]}`}>
      {children}
    </button>
  );
}
