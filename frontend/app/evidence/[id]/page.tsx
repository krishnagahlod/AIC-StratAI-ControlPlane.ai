"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Printer, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { EvidencePack } from "@/lib/types";

/**
 * Print-optimised compliance evidence pack.
 *
 * A CISO's deliverable is an artifact they can hand to an auditor, not a dashboard.
 * Rendering it as a print-first page means the browser's own print dialog produces the
 * PDF — no PDF library, no server-side rendering stack, and the output is whatever the
 * reviewer can see on screen.
 *
 * Every finding carries its detection method, because "a regex matched" and "a model
 * judged" are different grades of evidence and an auditor has to weigh them differently.
 */
export default function EvidencePage() {
  const params = useParams<{ id: string }>();
  const [pack, setPack] = useState<EvidencePack | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = Number(params?.id);
    if (!Number.isFinite(id)) return;
    api.getEvidence(id).then(setPack).catch((e) => setError(e.message));
  }, [params?.id]);

  if (error) {
    return <div className="p-8 text-sm text-rose-700">Could not load evidence pack: {error}</div>;
  }
  if (!pack) {
    return <div className="p-8 text-sm text-muted-2">Loading evidence pack…</div>;
  }

  const { interaction: i, content, controls_applied: controls, evaluation, business_impact, governance_decision } = pack;

  return (
    <div className="max-w-[820px] mx-auto text-[13px] leading-relaxed">
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body { background: #fff !important; }
          aside { display: none !important; }
          .evidence-sheet { padding: 0 !important; }
          .avoid-break { break-inside: avoid; }
        }
      `}</style>

      <div className="no-print flex items-center justify-between mb-6">
        <Link href="/live" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-foreground">
          <ArrowLeft size={15} /> Back to Live Feed
        </Link>
        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-2 px-4 h-10 rounded-xl bg-accent text-white text-sm font-semibold
                     shadow-[0_1px_2px_rgba(161,0,255,0.15),0_4px_14px_-4px_rgba(161,0,255,0.45)] hover:bg-accent-deep"
        >
          <Printer size={15} /> Print / Save as PDF
        </button>
      </div>

      <div className="evidence-sheet bg-white border border-border rounded-2xl p-8 print:border-0">
        <header className="border-b-2 border-foreground pb-4 mb-6">
          <div className="flex items-start justify-between gap-6">
            <div>
              <h1 className="text-xl font-bold tracking-tight">AI Interaction Evidence Pack</h1>
              <p className="text-muted mt-0.5">
                ControlPlane.ai · Interaction #{i.id} · Pack v{pack.evidence_pack_version}
              </p>
            </div>
            <div className="text-right text-xs text-muted-2 shrink-0">
              <div>Generated {new Date(pack.generated_at).toLocaleString()}</div>
              <div>Event {new Date(i.timestamp).toLocaleString()}</div>
            </div>
          </div>
        </header>

        <Section title="1. Interaction">
          <Grid
            rows={[
              ["Application", `${i.application} (${i.application_type?.replace(/_/g, " ")})`],
              ["Task type", i.task_type],
              ["Model", i.model],
              ["Latency", `${i.latency_ms} ms`],
              ["Tokens", `${i.input_tokens} in / ${i.output_tokens} out`],
              ["Record source", i.source],
            ]}
          />
        </Section>

        <Section title="2. Control applied at request time">
          <Grid
            rows={[
              ["Synchronous action", controls.sync_action],
              ["Output modified before delivery", content.was_modified_before_delivery ? "Yes" : "No"],
              ["Sync-path flags", controls.sync_flags.length ? `${controls.sync_flags.length}` : "None"],
            ]}
          />
        </Section>

        <Section title="3. Content of record">
          <Field label="Prompt" value={content.prompt} />
          {content.source_context && <Field label="Source context provided" value={content.source_context} />}
          <Field label="Delivered to user" value={content.delivered_to_user || "(nothing delivered — request blocked)"} />
          {content.was_modified_before_delivery && (
            <Field
              label="Raw model output (pre-intervention, retained for audit)"
              value={content.raw_model_output || "(model was not called)"}
              danger
            />
          )}
        </Section>

        {evaluation && (
          <Section title="4. Evaluation">
            <Grid
              rows={[
                ["TrustScore", `${evaluation.trust_score} (${evaluation.risk_level} risk)`],
                ["Performance", `${evaluation.performance_score} · weight ${evaluation.policy_weights.performance}`],
                ["Cost", `${evaluation.cost_score} · weight ${evaluation.policy_weights.cost}`],
                ["Responsibility", `${evaluation.responsibility_score} · weight ${evaluation.policy_weights.responsibility}`],
                ["Inference cost", `$${evaluation.estimated_cost_usd}`],
              ]}
            />

            <div className="mt-4 avoid-break">
              <div className="font-semibold mb-2">Findings ({evaluation.findings.length})</div>
              {evaluation.findings.length === 0 && <p className="text-muted-2">No findings recorded.</p>}
              {evaluation.findings.map((f, n) => (
                <div key={n} className="border border-border rounded-xl p-3 mb-2 avoid-break">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="font-semibold">{f.type.replace(/_/g, " ")}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full border border-border bg-surface-2 uppercase tracking-wide">
                      {f.severity}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full border border-border bg-surface-2">
                      {f.dimension}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full border ${
                        f.detection_method === "Deterministic rule"
                          ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                          : "border-amber-200 bg-amber-50 text-amber-800"
                      }`}
                    >
                      {f.detection_method}
                    </span>
                  </div>
                  <p className="text-muted">{f.finding}</p>
                  {f.evidence && (
                    <pre className="mt-1.5 text-[11px] bg-surface-2 rounded-lg p-2 whitespace-pre-wrap break-words font-mono">
                      {JSON.stringify(f.evidence)}
                    </pre>
                  )}
                  {f.action_taken && (
                    <p className="text-[11px] text-muted-2 mt-1">Action taken: {f.action_taken}</p>
                  )}
                </div>
              ))}
              <p className="text-[11px] text-muted-2 mt-1">
                Detection method is recorded per finding: a deterministic rule is reproducible from the
                same inputs; an LLM-as-judge finding is a model judgement and should be weighed accordingly.
              </p>
            </div>
          </Section>
        )}

        {business_impact && (
          <Section title="5. Estimated business impact">
            <Grid
              rows={[
                ["Risk category", business_impact.risk_category],
                ["Estimated exposure", `$${business_impact.estimated_impact_usd.toLocaleString()}`],
                ["Affected users", String(business_impact.affected_users)],
                ["Confidence", `${Math.round(business_impact.confidence * 100)}%`],
              ]}
            />
            <p className="mt-2 text-muted">{business_impact.basis}</p>
            <p className="mt-1 text-[11px] text-muted-2 italic">{business_impact.note}</p>
          </Section>
        )}

        {governance_decision && (
          <Section title="6. Governance decision">
            <Grid
              rows={[
                ["Routing decision", governance_decision.decision.replace(/_/g, " ")],
                ["Status", governance_decision.status.replace(/_/g, " ")],
                ["SLA window", governance_decision.sla_seconds ? `${governance_decision.sla_seconds}s` : "n/a"],
                ["Reviewer decision", governance_decision.reviewer_decision ?? "—"],
                ["Reviewer note", governance_decision.reviewer_note ?? "—"],
                ["Decided at", governance_decision.decided_at ? new Date(governance_decision.decided_at).toLocaleString() : "—"],
              ]}
            />
          </Section>
        )}

        <footer className="border-t border-border pt-3 mt-6 text-[11px] text-muted-2">
          Generated by ControlPlane.ai. Dollar figures are estimates derived from documented
          assumptions, not measured losses. Prompt and response text is reproduced verbatim from the
          interaction record.
        </footer>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-6 avoid-break">
      <h2 className="text-[13px] font-bold uppercase tracking-wide text-muted mb-2.5 border-b border-border pb-1">
        {title}
      </h2>
      {children}
    </section>
  );
}

function Grid({ rows }: { rows: [string, string][] }) {
  return (
    <dl className="grid grid-cols-[minmax(0,190px)_1fr] gap-x-4 gap-y-1.5">
      {rows.map(([k, v]) => (
        <div key={k} className="contents">
          <dt className="text-muted-2">{k}</dt>
          <dd className="font-medium break-words">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

function Field({ label, value, danger = false }: { label: string; value: string; danger?: boolean }) {
  return (
    <div className="mb-3 avoid-break">
      <div className="text-muted-2 mb-1">{label}</div>
      <div
        className={`rounded-xl p-3 whitespace-pre-wrap break-words border ${
          danger ? "bg-rose-50 border-rose-200" : "bg-surface-2 border-border"
        }`}
      >
        {value}
      </div>
    </div>
  );
}
