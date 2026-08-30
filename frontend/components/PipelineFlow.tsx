"use client";

import { motion } from "framer-motion";
import {
  ArrowDownToLine,
  ShieldCheck,
  Sparkles,
  Scale,
  Gauge,
  GitBranch,
  Check,
  X,
  Minus,
  Loader2,
} from "lucide-react";
import type { InteractionSummary } from "@/lib/types";

/**
 * Makes the four-layer architecture watchable instead of asserted.
 *
 * Every stage transition here is driven by a real backend signal — the proxy's sync
 * response resolves stages 1-3 (including whether the model was called at all), and
 * the evaluation row arriving from the existing poll resolves 4-6. Nothing advances on
 * a timer. The only illustrative element is the shimmer while genuinely waiting, and
 * the three analyzers really do run concurrently, so drawing them as a parallel fan-out
 * is accurate rather than decorative.
 *
 * Building a fake progress bar into a governance product would be the same category of
 * error as the narrator fabricating service names.
 */

export type StageStatus = "idle" | "active" | "done" | "blocked" | "skipped";

export interface SyncOutcome {
  syncAction: string;
  latencyMs: number;
  modelCalled: boolean;
  flagCount: number;
}

const LAYERS: Record<string, string> = {
  ingress: "Data Plane",
  guardrails: "Data Plane",
  model: "Data Plane",
  analyzers: "Control Plane",
  trust: "Intelligence Layer",
  escalation: "Intelligence Layer",
};

function StatusMark({ status }: { status: StageStatus }) {
  if (status === "active") return <Loader2 size={11} className="animate-spin" />;
  if (status === "done") return <Check size={11} strokeWidth={3} />;
  if (status === "blocked") return <X size={11} strokeWidth={3} />;
  if (status === "skipped") return <Minus size={11} strokeWidth={3} />;
  return <span className="w-[11px] h-[11px] rounded-full border border-current opacity-40" />;
}

const STATUS_STYLES: Record<StageStatus, { ring: string; chip: string; label: string }> = {
  idle: { ring: "border-border bg-surface-2", chip: "text-muted-2", label: "text-muted-2" },
  active: { ring: "border-accent/40 bg-accent-tint", chip: "text-accent-deep", label: "text-accent-deep" },
  done: { ring: "border-emerald-200 bg-emerald-50", chip: "text-emerald-700", label: "text-foreground" },
  blocked: { ring: "border-rose-200 bg-rose-50", chip: "text-rose-700", label: "text-rose-800" },
  skipped: { ring: "border-border bg-surface-2", chip: "text-muted-2", label: "text-muted-2" },
};

function Stage({
  icon,
  name,
  detail,
  status,
  index,
}: {
  icon: React.ReactNode;
  name: string;
  detail: string;
  status: StageStatus;
  index: number;
}) {
  const s = STATUS_STYLES[status];
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.25 }}
      className="flex-1 min-w-0"
    >
      <div className={`rounded-xl border p-3 h-full transition-colors duration-300 ${s.ring}`}>
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <span className={`shrink-0 ${s.chip}`}>{icon}</span>
          <span className={s.chip}>
            <StatusMark status={status} />
          </span>
        </div>
        <div className={`text-[12px] font-semibold leading-tight ${s.label}`}>{name}</div>
        <div className="text-[11px] text-muted-2 leading-tight mt-0.5 break-words">{detail}</div>
      </div>
    </motion.div>
  );
}

export default function PipelineFlow({
  sending,
  sync,
  detail,
  evalState,
}: {
  sending: boolean;
  sync: SyncOutcome | null;
  detail: InteractionSummary | null;
  evalState: "idle" | "running" | "done" | "failed" | "timeout";
}) {
  const started = sending || sync !== null;
  const blocked = sync?.syncAction === "blocked";
  const evaluation = detail?.evaluation ?? null;

  const idleOr = (s: StageStatus): StageStatus => (started ? s : "idle");

  const ingress: StageStatus = sync ? "done" : sending ? "active" : "idle";
  const guardrails: StageStatus = sync ? (blocked ? "blocked" : "done") : sending ? "active" : "idle";
  const model: StageStatus = sync ? (sync.modelCalled ? "done" : "skipped") : sending ? "idle" : "idle";
  const analyzers: StageStatus = evaluation
    ? "done"
    : evalState === "failed" || evalState === "timeout"
      ? "idle"
      : sync
        ? "active"
        : "idle";
  const trust: StageStatus = evaluation ? "done" : idleOr("idle");
  const escalationStatus: StageStatus = detail?.escalation ? "done" : idleOr("idle");

  const stages = [
    {
      key: "ingress",
      icon: <ArrowDownToLine size={15} />,
      name: "Ingress",
      detail: sync ? "Request accepted" : sending ? "Receiving…" : "Awaiting request",
      status: ingress,
    },
    {
      key: "guardrails",
      icon: <ShieldCheck size={15} />,
      name: "Sync Guardrails",
      detail: sync
        ? blocked
          ? "Blocked — pattern matched"
          : sync.syncAction === "redacted"
            ? "PII redacted inline"
            : `Passed · ${sync.flagCount} sync flag${sync.flagCount === 1 ? "" : "s"}`
        : "PII · blocklist · budget",
      status: guardrails,
    },
    {
      key: "model",
      icon: <Sparkles size={15} />,
      name: "Model Call",
      detail: sync
        ? sync.modelCalled
          ? `Gemini · ${Math.round(sync.latencyMs)}ms`
          : "Never called — stopped upstream"
        : "Gemini",
      status: model,
    },
    {
      key: "analyzers",
      icon: <Scale size={15} />,
      name: "Async Evaluation",
      detail: evaluation
        ? `${evaluation.flags.length} flag${evaluation.flags.length === 1 ? "" : "s"} from 3 analyzers`
        : analyzers === "active"
          ? "Performance · Cost · Responsibility"
          : "3 analyzers, in parallel",
      status: analyzers,
    },
    {
      key: "trust",
      icon: <Gauge size={15} />,
      name: "TrustScore",
      detail: evaluation
        ? `${Math.round(evaluation.trust_score)} · ${evaluation.risk_level} risk`
        : "Weighted per app policy",
      status: trust,
    },
    {
      key: "escalation",
      icon: <GitBranch size={15} />,
      name: "Escalation",
      detail: detail?.escalation ? detail.escalation.decision.replace(/_/g, " ") : "Tiered decision",
      status: escalationStatus,
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-2.5">
        <div className="text-xs uppercase tracking-wide text-muted-2 font-medium">Pipeline</div>
        <div className="flex items-center gap-3 text-[10px] uppercase tracking-wide text-muted-2">
          <span>Data Plane</span>
          <span className="text-border-strong">›</span>
          <span>Control Plane</span>
          <span className="text-border-strong">›</span>
          <span>Intelligence Layer</span>
        </div>
      </div>

      <div className="flex items-stretch gap-1.5">
        {stages.map((s, i) => (
          <Stage key={s.key} icon={s.icon} name={s.name} detail={s.detail} status={s.status} index={i} />
        ))}
      </div>

      {blocked && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-xs text-rose-700 mt-2.5"
        >
          The request was stopped in the synchronous path, before any tokens were sent to the model —
          so it cost nothing and could not produce a harmful response.
        </motion.p>
      )}

      <p className="text-[11px] text-muted-2 mt-2.5">
        Each stage advances on a real signal from the backend — the proxy&apos;s response resolves the
        first three, the evaluation record resolves the rest. Nothing here runs on a timer.
      </p>
    </div>
  );
}
