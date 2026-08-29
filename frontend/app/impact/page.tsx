"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatUsd } from "@/lib/format";
import { Badge, Card, PageHeader } from "@/components/ui";
import AppFilter from "@/components/AppFilter";
import type { AppSummary, ImpactBreakdownItem, Recommendation } from "@/lib/types";

const AUDIENCES = [
  { key: "engineer", label: "Engineer" },
  { key: "ciso", label: "CISO / Compliance" },
  { key: "ceo", label: "CEO / CTO" },
];

const CATEGORY_LABEL: Record<string, string> = {
  revenue: "Revenue Risk",
  compliance: "Compliance Risk",
  reputation: "Reputation Risk",
  customer_trust: "Customer Trust",
  security: "Security",
  operational_cost: "Operational Cost",
};

export default function ImpactPage() {
  const [apps, setApps] = useState<AppSummary[]>([]);
  const [appId, setAppId] = useState<number | null>(null);
  const [audience, setAudience] = useState("ceo");
  const [narrative, setNarrative] = useState<string>("");
  const [loadingNarrative, setLoadingNarrative] = useState(false);
  const [breakdown, setBreakdown] = useState<ImpactBreakdownItem[]>([]);
  const [recs, setRecs] = useState<Recommendation[]>([]);

  useEffect(() => {
    api.listApps().then(setApps).catch(console.error);
  }, []);

  useEffect(() => {
    api.getImpactBreakdown(appId, 14).then(setBreakdown).catch(console.error);
    api.listRecommendations(appId).then(setRecs).catch(console.error);
  }, [appId]);

  useEffect(() => {
    setLoadingNarrative(true);
    api
      .getNarrative(audience, appId, 14)
      .then((r) => setNarrative(r.narrative))
      .catch((e) => setNarrative(`Could not load narrative: ${e.message}`))
      .finally(() => setLoadingNarrative(false));
  }, [audience, appId]);

  const maxImpact = Math.max(...breakdown.map((b) => b.total_usd), 1);

  return (
    <div>
      <PageHeader
        title="Business Impact & Executive Brief"
        description="Technical flags translated into dollars, affected users, and plain-English narratives per audience."
      />

      <div className="flex flex-wrap items-center gap-3 mb-6">
        <AppFilter apps={apps} value={appId} onChange={setAppId} />
        <div className="flex bg-surface-2 border border-border rounded-lg p-1">
          {AUDIENCES.map((a) => (
            <button
              key={a.key}
              onClick={() => setAudience(a.key)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                audience === a.key ? "bg-accent text-white" : "text-muted hover:text-foreground"
              }`}
            >
              {a.label}
            </button>
          ))}
        </div>
      </div>

      <Card className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="text-sm font-medium">🎤 Executive Narrator — {AUDIENCES.find((a) => a.key === audience)?.label} Report</div>
          {loadingNarrative && <span className="text-xs text-muted">generating…</span>}
        </div>
        <p className="text-sm leading-relaxed text-foreground/90">{narrative || "Loading narrative…"}</p>
      </Card>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card>
          <div className="text-sm font-medium mb-4">Estimated Impact by Risk Category (14d)</div>
          <div className="space-y-3">
            {breakdown.length === 0 && <div className="text-xs text-muted">No material business impact detected.</div>}
            {breakdown.map((b) => (
              <div key={b.risk_category}>
                <div className="flex justify-between text-sm mb-1">
                  <span>{CATEGORY_LABEL[b.risk_category] ?? b.risk_category}</span>
                  <span className="font-medium">{formatUsd(b.total_usd)}</span>
                </div>
                <div className="h-2 bg-surface-2 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-accent to-rose-400"
                    style={{ width: `${(b.total_usd / maxImpact) * 100}%` }}
                  />
                </div>
                <div className="text-xs text-muted mt-0.5">{b.count} flagged interaction(s)</div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <div className="text-sm font-medium mb-4">💡 Prescriptive Actions</div>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {recs.length === 0 && <div className="text-xs text-muted">No recommendations yet.</div>}
            {recs.map((r) => (
              <div key={r.id} className="border-b border-border/60 last:border-0 pb-3 last:pb-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="text-sm font-medium">{r.issue}</div>
                  <Badge className={r.priority === 1 ? "text-rose-400 bg-rose-400/10 border-rose-400/30" : "text-muted bg-surface-2 border-border"}>
                    P{r.priority}
                  </Badge>
                </div>
                <div className="text-xs text-muted mt-1">
                  <span className="text-foreground/80">Root cause:</span> {r.root_cause}
                </div>
                <div className="text-xs text-muted mt-1">
                  <span className="text-foreground/80">Action:</span> {r.action}
                </div>
                <div className="flex items-center gap-3 mt-1.5 text-xs">
                  <span className="text-emerald-400">{formatUsd(r.estimated_value_usd)} value</span>
                  <span className="text-muted">{Math.round(r.confidence * 100)}% confidence</span>
                  <span className="text-muted">{r.method === "llm_generated" ? "LLM-proposed" : "rule-based"}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
