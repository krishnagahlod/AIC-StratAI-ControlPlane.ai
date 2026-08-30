"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Filter } from "lucide-react";
import { api } from "@/lib/api";
import { usePolling } from "@/lib/hooks";
import { formatRelativeTime, formatUsd, riskLevelColor } from "@/lib/format";
import { Badge, Card, FlagList, InterventionBanner, PageHeader, TrustRing } from "@/components/ui";
import AppFilter from "@/components/AppFilter";
import type { AppSummary, InteractionSummary } from "@/lib/types";

function SyncActionBadge({ action }: { action: string }) {
  const styles: Record<string, string> = {
    allowed: "text-emerald-600 bg-emerald-50 border-emerald-200",
    redacted: "text-amber-700 bg-amber-50 border-amber-200",
    blocked: "text-rose-600 bg-rose-50 border-rose-200",
  };
  return <Badge className={styles[action] ?? styles.allowed}>{action}</Badge>;
}

export default function LiveFeedPage() {
  const [apps, setApps] = useState<AppSummary[]>([]);
  const [appId, setAppId] = useState<number | null>(null);
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [interactions, setInteractions] = useState<InteractionSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<InteractionSummary | null>(null);

  // Changing the app filter must clear the selection: otherwise the detail panel keeps
  // showing a trace from an app the filter has since excluded, so the evidence on screen
  // contradicts the dropdown above it.
  function changeApp(next: number | null) {
    setAppId(next);
    setSelectedId(null);
    setDetail(null);
  }

  const visible = flaggedOnly
    ? interactions.filter((i) => (i.evaluation?.flags.length ?? 0) > 0 || i.sync_action !== "allowed")
    : interactions;

  usePolling(() => {
    api.listApps().then(setApps).catch(console.error);
  }, 15000);

  usePolling(() => {
    api
      .listInteractions({ appId, limit: 60 })
      .then((rows) => setInteractions(rows.slice().reverse()))
      .catch(console.error);
  }, 3000, [appId]);

  usePolling(() => {
    if (selectedId == null) {
      setDetail(null);
      return;
    }
    api.getInteraction(selectedId).then(setDetail).catch(console.error);
  }, 3000, [selectedId]);

  return (
    <div>
      <PageHeader title="Live Feed & Trace Explorer" description="Every request-response pair flowing through the proxy, with full evaluation traces." />

      <div className="mb-4 flex items-center gap-3 overflow-x-auto no-scrollbar pb-1">
        <AppFilter apps={apps} value={appId} onChange={changeApp} />
        <button
          onClick={() => setFlaggedOnly((v) => !v)}
          aria-pressed={flaggedOnly}
          className={`shrink-0 inline-flex items-center gap-2 h-10 px-3.5 rounded-xl border text-sm font-medium transition-colors duration-150 ${
            flaggedOnly
              ? "bg-accent-tint border-accent/30 text-accent-deep"
              : "bg-white border-border text-muted hover:text-foreground hover:border-border-strong"
          }`}
        >
          <Filter size={15} />
          Flagged only
          {flaggedOnly && <span className="text-xs opacity-70">({visible.length})</span>}
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        <Card className="xl:col-span-2 p-0 overflow-hidden">
          <div className="max-h-[75vh] overflow-y-auto divide-y divide-border">
            {visible.length === 0 && (
              <div className="p-4 text-sm text-muted-2">
                {flaggedOnly
                  ? "No flagged interactions in this window — every request passed all three analyzers."
                  : "No interactions yet. Send one from Try It Live to see the pipeline run."}
              </div>
            )}
            {visible.map((i) => (
              <motion.button
                key={i.id}
                layout
                onClick={() => setSelectedId(i.id)}
                className={`w-full text-left p-4 hover:bg-surface-2 transition-colors duration-150 ${
                  selectedId === i.id ? "bg-surface-2" : ""
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-xs text-muted-2">{i.app_name} · {i.source}</div>
                    <div className="text-sm truncate font-medium">{i.prompt}</div>
                  </div>
                  {i.evaluation && (
                    <span className={`shrink-0 text-sm font-semibold ${riskLevelColor(i.evaluation.risk_level).split(" ")[0]}`}>
                      {Math.round(i.evaluation.trust_score)}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <SyncActionBadge action={i.sync_action} />
                  {i.evaluation && i.evaluation.flags.length > 0 && (
                    <Badge className="text-muted bg-surface-2 border-border">{i.evaluation.flags.length} flag(s)</Badge>
                  )}
                  <span className="text-xs text-muted-2 ml-auto">{formatRelativeTime(i.created_at)}</span>
                </div>
              </motion.button>
            ))}
          </div>
        </Card>

        <Card className="xl:col-span-3">
          {!detail && <div className="text-sm text-muted-2">Select an interaction to see its full evaluation trace.</div>}
          {detail && (
            <motion.div
              key={detail.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className="space-y-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-xs text-muted-2">{detail.app_name} · {detail.task_type} · {detail.model}</div>
                  <div className="text-sm text-muted mt-1">{formatRelativeTime(detail.created_at)} · {detail.latency_ms.toFixed(0)}ms</div>
                </div>
                {detail.evaluation &&
                  (detail.sync_action === "allowed" ? (
                    <TrustRing score={detail.evaluation.trust_score} />
                  ) : (
                    <div className="text-right shrink-0">
                      <div className="text-xs uppercase tracking-wide text-muted-2">TrustScore</div>
                      <div className="text-lg font-semibold text-muted">
                        {Math.round(detail.evaluation.trust_score)}
                      </div>
                    </div>
                  ))}
              </div>

              <InterventionBanner action={detail.sync_action} />

              <div>
                <div className="text-xs uppercase text-muted-2 mb-1.5">Prompt</div>
                <div className="text-sm bg-surface-2 rounded-xl p-3 whitespace-pre-wrap">{detail.prompt}</div>
              </div>

              {detail.rag_context && (
                <div>
                  <div className="text-xs uppercase text-muted-2 mb-1.5">Source / RAG Context</div>
                  <div className="text-sm bg-surface-2 rounded-xl p-3 whitespace-pre-wrap">{detail.rag_context}</div>
                </div>
              )}

              <div>
                <div className="flex items-center gap-2 text-xs uppercase text-muted-2 mb-1.5">
                  Delivered Response <SyncActionBadge action={detail.sync_action} />
                </div>
                <div className="text-sm bg-surface-2 rounded-xl p-3 whitespace-pre-wrap">{detail.response}</div>
              </div>

              {detail.raw_response && detail.raw_response !== detail.response && (
                <div>
                  <div className="text-xs uppercase text-muted-2 mb-1.5">Raw Model Output (pre-redaction, internal only)</div>
                  <div className="text-sm bg-rose-500/5 border border-rose-500/20 rounded-xl p-3 whitespace-pre-wrap">
                    {detail.raw_response}
                  </div>
                </div>
              )}

              {detail.evaluation && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-surface-2 rounded-xl p-3">
                    <div className="text-xs text-muted-2">Performance</div>
                    <div className="text-lg font-semibold">{detail.evaluation.performance_score}</div>
                  </div>
                  <div className="bg-surface-2 rounded-xl p-3">
                    <div className="text-xs text-muted-2">Cost</div>
                    <div className="text-lg font-semibold">{detail.evaluation.cost_score}</div>
                  </div>
                  <div className="bg-surface-2 rounded-xl p-3">
                    <div className="text-xs text-muted-2">Responsibility</div>
                    <div className="text-lg font-semibold">{detail.evaluation.responsibility_score}</div>
                  </div>
                </div>
              )}

              {detail.evaluation && (
                <div>
                  <div className="text-xs uppercase text-muted-2 mb-2">Flags</div>
                  <FlagList flags={detail.evaluation.flags} />
                </div>
              )}

              {detail.business_impact && detail.business_impact.risk_category !== "none" && (
                <div>
                  <div className="text-xs uppercase text-muted-2 mb-1.5">Business Impact</div>
                  <div className="text-sm bg-surface-2 rounded-xl p-3">
                    <div className="font-medium text-rose-600 mb-1">
                      {formatUsd(detail.business_impact.estimated_impact_usd)} · {detail.business_impact.risk_category}
                    </div>
                    {detail.business_impact.narrative}
                  </div>
                </div>
              )}

              {detail.escalation && (
                <div>
                  <div className="text-xs uppercase text-muted-2 mb-1.5">Escalation</div>
                  <Badge className={riskLevelColor(detail.evaluation?.risk_level ?? "minimal")}>
                    {detail.escalation.decision.replace(/_/g, " ")} · {detail.escalation.status}
                  </Badge>
                </div>
              )}
            </motion.div>
          )}
        </Card>
      </div>
    </div>
  );
}
