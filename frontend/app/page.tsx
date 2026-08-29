"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { usePolling } from "@/lib/hooks";
import { formatUsd, formatRelativeTime, trustScoreColor } from "@/lib/format";
import { Card, PageHeader, StatCard, TrustRing } from "@/components/ui";
import type { AlertItem, AppSummary, Recommendation, Summary, TrendPoint } from "@/lib/types";
import Link from "next/link";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function OverviewPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [apps, setApps] = useState<AppSummary[]>([]);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [recs, setRecs] = useState<Recommendation[]>([]);

  usePolling(() => {
    api.getSummary(14).then(setSummary).catch(console.error);
    api.listApps().then(setApps).catch(console.error);
    api.getTrends({ days: 14 }).then(setTrends).catch(console.error);
    api.listAlerts(8).then(setAlerts).catch(console.error);
    api.listRecommendations().then((r) => setRecs(r.slice(0, 5))).catch(console.error);
  }, 8000);

  return (
    <div>
      <PageHeader
        title="AI Fleet Overview"
        description="Real-time trust, cost, and risk posture across every monitored application — last 14 days."
      />

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4 mb-6">
        <StatCard
          label="Avg TrustScore"
          value={summary ? summary.avg_trust_score.toFixed(1) : "—"}
          accentClass={summary ? trustScoreColor(summary.avg_trust_score) : ""}
          sub={`${summary?.total_interactions ?? 0} interactions evaluated`}
        />
        <StatCard
          label="Business Impact at Risk"
          value={summary ? formatUsd(summary.total_business_impact_usd) : "—"}
          accentClass="text-rose-400"
          sub="Estimated, illustrative assumptions"
        />
        <StatCard
          label="AI Spend"
          value={summary ? formatUsd(summary.total_ai_spend_usd) : "—"}
          sub="Across all monitored apps"
        />
        <StatCard
          label="Pending Human Reviews"
          value={summary ? String(summary.pending_human_reviews) : "—"}
          accentClass="text-amber-400"
          sub="Awaiting SLA-timed decision"
        />
        <StatCard
          label="Critical Incidents"
          value={summary ? String(summary.critical_incidents) : "—"}
          accentClass="text-rose-400"
          sub="TrustScore < 30"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card className="xl:col-span-2">
          <div className="text-sm font-medium mb-4">TrustScore Trend (all apps)</div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends}>
                <XAxis dataKey="day" stroke="var(--muted)" fontSize={11} tickLine={false} />
                <YAxis domain={[0, 100]} stroke="var(--muted)" fontSize={11} tickLine={false} width={30} />
                <Tooltip
                  contentStyle={{ background: "var(--surface-2)", border: "1px solid var(--border)", fontSize: 12 }}
                />
                <Line isAnimationActive={false} type="monotone" dataKey="avg_trust_score" stroke="#6d5efc" strokeWidth={2} dot={false} name="TrustScore" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <div className="text-sm font-medium mb-4">Apps Under Management</div>
          <div className="space-y-3">
            {apps.map((app) => (
              <div key={app.id} className="flex items-center justify-between border-b border-border/60 last:border-0 pb-3 last:pb-0">
                <div>
                  <div className="text-sm font-medium">{app.name}</div>
                  <div className="text-xs text-muted capitalize">{app.app_type.replace("_", " ")}</div>
                </div>
                <div className="text-xs text-muted text-right">
                  <div>{formatUsd(app.daily_spend_usd)} / {formatUsd(app.daily_budget_usd)}</div>
                  <div>{app.budget_remaining_pct}% budget left</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-6">
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-medium">🔔 Smart Alerts</div>
            <span className="text-xs text-muted">deduplicated, last hour</span>
          </div>
          <div className="space-y-2">
            {alerts.length === 0 && <div className="text-xs text-muted">No active alerts.</div>}
            {alerts.map((a) => (
              <div key={a.id} className="flex items-start gap-2 text-sm">
                <span
                  className={`mt-1 w-2 h-2 rounded-full shrink-0 ${
                    a.severity === "critical" ? "bg-rose-400" : a.severity === "medium" ? "bg-amber-400" : "bg-slate-400"
                  }`}
                />
                <div className="flex-1">
                  <div className="text-foreground/90">{a.message}</div>
                  <div className="text-xs text-muted">
                    {a.count > 1 ? `${a.count}x · ` : ""}
                    {formatRelativeTime(a.updated_at)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-medium">💡 Top Prescriptive Actions</div>
            <Link href="/impact" className="text-xs text-accent hover:underline">
              view all
            </Link>
          </div>
          <div className="space-y-3">
            {recs.length === 0 && <div className="text-xs text-muted">No recommendations yet.</div>}
            {recs.map((r) => (
              <div key={r.id} className="text-sm">
                <div className="font-medium">{r.issue}</div>
                <div className="text-xs text-muted">{r.action}</div>
                <div className="text-xs text-emerald-400 mt-0.5">{formatUsd(r.estimated_value_usd)} potential value</div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="mt-8 flex items-center gap-4 text-xs text-muted">
        <TrustRing score={summary?.avg_trust_score ?? 100} size={36} />
        <span>
          TrustScore = weighted(Performance, Cost, Responsibility) per app policy. See{" "}
          <Link href="/trends" className="text-accent hover:underline">
            Trends
          </Link>{" "}
          for the breakdown by dimension.
        </span>
      </div>
    </div>
  );
}
