"use client";

import { motion, animate } from "framer-motion";
import { useEffect, useState } from "react";
import { flagLabel, severityColor, trustScoreColor } from "@/lib/format";
import type { Flag } from "@/lib/types";

export function Card({
  children,
  className = "",
  interactive = false,
}: {
  children: React.ReactNode;
  className?: string;
  interactive?: boolean;
}) {
  return (
    <div
      className={`relative bg-surface/90 backdrop-blur-sm border border-border rounded-2xl p-5 shadow-[0_1px_0_0_rgba(255,255,255,0.03)_inset] transition-all duration-200 ${
        interactive ? "hover:border-border-strong hover:bg-surface-2/90 hover:-translate-y-0.5 cursor-pointer" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}

function formatAnimated(v: number, decimals: number): string {
  return v.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function AnimatedNumber({ value, decimals = 0 }: { value: number; decimals?: number }) {
  const [display, setDisplay] = useState(() => formatAnimated(0, decimals));

  useEffect(() => {
    const controls = animate(0, value, {
      duration: 0.7,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => setDisplay(formatAnimated(v, decimals)),
    });
    return controls.stop;
  }, [value, decimals]);

  return <span>{display}</span>;
}

export function StatCard({
  label,
  value,
  numericValue,
  decimals = 0,
  prefix = "",
  suffix = "",
  sub,
  accentClass,
  icon,
}: {
  label: string;
  value?: string;
  numericValue?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  sub?: string;
  accentClass?: string;
  icon?: React.ReactNode;
}) {
  return (
    <Card className="overflow-hidden">
      <div className="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-accent/5 blur-xl" aria-hidden="true" />
      <div className="flex items-start justify-between mb-2">
        <div className="text-xs uppercase tracking-wide text-muted">{label}</div>
        {icon && <div className="text-muted-2">{icon}</div>}
      </div>
      <div className={`font-display text-3xl font-semibold tracking-tight ${accentClass ?? ""}`}>
        {numericValue !== undefined ? (
          <>
            {prefix}
            <AnimatedNumber value={numericValue} decimals={decimals} />
            {suffix}
          </>
        ) : (
          value
        )}
      </div>
      {sub && <div className="text-xs text-muted-2 mt-1.5">{sub}</div>}
    </Card>
  );
}

export function PageHeader({
  title,
  description,
  icon,
}: {
  title: string;
  description?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="mb-7">
      <div className="flex items-center gap-2.5">
        {icon && <span className="text-accent">{icon}</span>}
        <h1 className="font-display text-2xl font-semibold tracking-tight">{title}</h1>
      </div>
      {description && <p className="text-sm text-muted mt-1.5 max-w-2xl">{description}</p>}
    </div>
  );
}

export function TrustRing({ score, size = 64 }: { score: number; size?: number }) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);
  const colorClass = trustScoreColor(score);
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="var(--border)" strokeWidth={6} fill="none" />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={6}
          fill="none"
          strokeDasharray={circumference}
          strokeLinecap="round"
          className={colorClass}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        />
      </svg>
      <div className={`absolute inset-0 flex items-center justify-center text-sm font-semibold font-display ${colorClass}`}>
        {Math.round(score)}
      </div>
    </div>
  );
}

export function FlagChip({ flag }: { flag: Flag }) {
  return (
    <span
      title={flag.detail}
      className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${severityColor(flag.severity)}`}
    >
      {flagLabel(flag.type)}
      <span className="opacity-50">·</span>
      <span className="opacity-70">{flag.method === "llm_judge" ? "LLM judge" : "rule"}</span>
    </span>
  );
}

export function FlagList({ flags }: { flags: Flag[] }) {
  if (!flags || flags.length === 0) {
    return <span className="text-xs text-muted-2">No issues detected</span>;
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
    <span className={`inline-flex items-center text-xs px-2.5 py-1 rounded-full border font-medium ${className}`}>
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
  const base =
    "inline-flex items-center justify-center gap-1.5 px-4 h-10 rounded-xl text-sm font-medium transition-all duration-150 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100";
  const styles: Record<string, string> = {
    primary: "bg-accent text-white shadow-[0_1px_0_0_rgba(255,255,255,0.15)_inset,0_4px_16px_-4px_var(--accent-soft)] hover:brightness-110",
    secondary: "bg-surface-2 text-foreground border border-border hover:bg-surface-3 hover:border-border-strong",
    danger: "bg-rose-500/10 text-rose-300 border border-rose-500/25 hover:bg-rose-500/20",
    ghost: "text-muted hover:text-foreground hover:bg-surface-2",
  };
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={`${base} ${styles[variant]}`}>
      {children}
    </button>
  );
}

export function SectionLabel({
  children,
  icon,
  className = "mb-4",
}: {
  children: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex items-center gap-2 text-sm font-medium ${className}`}>
      {icon && <span className="text-accent">{icon}</span>}
      {children}
    </div>
  );
}
