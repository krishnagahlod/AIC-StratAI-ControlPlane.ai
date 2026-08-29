"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic2, Lightbulb } from "lucide-react";
import { api } from "@/lib/api";
import { formatUsd } from "@/lib/format";
import { Badge, Card, PageHeader, SectionLabel } from "@/components/ui";
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

      <div className="flex items-center gap-3 mb-6 overflow-x-auto no-scrollbar pb-1">
        <AppFilter apps={apps} value={appId} onChange={setAppId} />
        <div className="flex bg-surface-2 border border-border rounded-xl p-1 shrink-0 max-w-full overflow-x-auto no-scrollbar">
          {AUDIENCES.map((a) => (
            <button
              key={a.key}
              onClick={() => setAudience(a.key)}
              className={`relative px-3.5 h-8 text-sm rounded-lg transition-colors duration-150 whitespace-nowrap ${
                audience === a.key ? "text-white" : "text-muted hover:text-foreground"
              }`}
            >
              {audience === a.key && (
                <motion.div layoutId="audience-active" className="absolute inset-0 bg-accent rounded-lg" transition={{ type: "spring", stiffness: 400, damping: 32 }} />
              )}
              <span className="relative z-10">{a.label}</span>
            </button>
          ))}
        </div>
      </div>

      <Card className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <SectionLabel icon={<Mic2 size={15} />} className="">
            Executive Narrator — {AUDIENCES.find((a) => a.key === audience)?.label} Report
          </SectionLabel>
          {loadingNarrative && <span className="text-xs text-muted-2">generating…</span>}
        </div>
        <AnimatePresence mode="wait">
          <motion.p
            key={narrative}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="text-sm leading-relaxed text-foreground/90"
          >
            {narrative || "Loading narrative…"}
          </motion.p>
        </AnimatePresence>
      </Card>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card>
          <SectionLabel>Estimated Impact by Risk Category (14d)</SectionLabel>
          <div className="space-y-3">
            {breakdown.length === 0 && <div className="text-xs text-muted-2">No material business impact detected.</div>}
            {breakdown.map((b) => (
              <div key={b.risk_category}>
                <div className="flex flex-wrap justify-between gap-x-3 text-sm mb-1">
                  <span>{CATEGORY_LABEL[b.risk_category] ?? b.risk_category}</span>
                  <span className="font-medium font-display">{formatUsd(b.total_usd)}</span>
                </div>
                <div className="h-2 bg-surface-2 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-accent to-rose-400"
                    initial={{ width: 0 }}
                    animate={{ width: `${(b.total_usd / maxImpact) * 100}%` }}
                    transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                  />
                </div>
                <div className="text-xs text-muted-2 mt-0.5">{b.count} flagged interaction(s)</div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <SectionLabel icon={<Lightbulb size={15} />}>Prescriptive Actions</SectionLabel>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {recs.length === 0 && <div className="text-xs text-muted-2">No recommendations yet.</div>}
            {recs.map((r) => (
              <div key={r.id} className="border-b border-border/60 last:border-0 pb-3 last:pb-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="text-sm font-medium">{r.issue}</div>
                  <Badge className={r.priority === 1 ? "text-rose-400 bg-rose-400/10 border-rose-400/30" : "text-muted bg-surface-2 border-border"}>
                    P{r.priority}
                  </Badge>
                </div>
                <div className="text-xs text-muted-2 mt-1">
                  <span className="text-foreground/80">Root cause:</span> {r.root_cause}
                </div>
                <div className="text-xs text-muted-2 mt-1">
                  <span className="text-foreground/80">Action:</span> {r.action}
                </div>
                <div className="flex items-center gap-3 mt-1.5 text-xs">
                  <span className="text-emerald-400">{formatUsd(r.estimated_value_usd)} value</span>
                  <span className="text-muted-2">{Math.round(r.confidence * 100)}% confidence</span>
                  <span className="text-muted-2">{r.method === "llm_generated" ? "LLM-proposed" : "rule-based"}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
