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
      className={`relative bg-surface border border-border rounded-2xl p-5 shadow-[0_1px_2px_rgba(10,0,17,0.04),0_1px_0_rgba(10,0,17,0.02)] transition-all duration-200 ${
        interactive ? "hover:border-border-strong hover:shadow-[0_4px_16px_-4px_rgba(10,0,17,0.10)] hover:-translate-y-0.5 cursor-pointer" : ""
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

/** Shimmering placeholder. Distinguishes "we don't know yet" from "the answer is zero". */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-surface-3/70 ${className}`} aria-hidden="true" />;
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
  loading = false,
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
  loading?: boolean;
}) {
  return (
    <Card className="overflow-hidden">
      <div className="flex items-start justify-between mb-2">
        <div className="text-xs uppercase tracking-wide text-muted-2 font-medium">{label}</div>
        {icon && <div className="text-accent">{icon}</div>}
      </div>
      {/* A headline metric must never render a confident, fully-styled 0 before its
          first real value arrives — that reads as "no risk" rather than "loading". */}
      {loading ? (
        <Skeleton className="h-[34px] w-24 mt-0.5" />
      ) : (
        <div className={`text-[28px] font-bold tracking-tight ${accentClass ?? "text-foreground"}`}>
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
      )}
      {sub && (
        <div className="text-xs text-muted-2 mt-1.5">
          {loading ? <Skeleton className="h-3 w-32" /> : sub}
        </div>
      )}
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
        <h1 className="text-[26px] font-bold tracking-tight text-foreground">{title}</h1>
      </div>
      {description && <p className="text-[15px] text-muted mt-1.5 max-w-2xl leading-relaxed">{description}</p>}
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
      <div className={`absolute inset-0 flex items-center justify-center text-sm font-bold ${colorClass}`}>
        {Math.round(score)}
      </div>
    </div>
  );
}

export function FlagChip({ flag }: { flag: Flag }) {
  return (
    <span
      title={flag.detail}
      className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border ${severityColor(flag.severity)}`}
    >
      {flagLabel(flag.type)}
      <span className="opacity-40">·</span>
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
    "inline-flex items-center justify-center gap-1.5 px-4 h-10 rounded-xl text-sm font-semibold transition-all duration-150 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100";
  const styles: Record<string, string> = {
    primary: "bg-accent text-white shadow-[0_1px_2px_rgba(161,0,255,0.15),0_4px_14px_-4px_rgba(161,0,255,0.45)] hover:bg-accent-deep",
    secondary: "bg-white text-foreground border border-border hover:bg-surface-2 hover:border-border-strong",
    danger: "bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100",
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
    <div className={`flex items-center gap-2 text-[15px] font-semibold text-foreground ${className}`}>
      {icon && <span className="text-accent">{icon}</span>}
      {children}
    </div>
  );
}
