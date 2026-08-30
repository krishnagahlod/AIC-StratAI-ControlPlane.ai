"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Bell, Lightbulb, ShieldAlert } from "lucide-react";
import { api } from "@/lib/api";
import { usePolling } from "@/lib/hooks";
import { formatUsd, formatRelativeTime, trustScoreColor } from "@/lib/format";
import { Card, PageHeader, SectionLabel, Skeleton, StatCard, TrustRing } from "@/components/ui";
import type { AlertItem, AppSummary, Recommendation, Summary, TrendPoint } from "@/lib/types";
import Link from "next/link";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const listVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.05 } },
};
const itemVariants = {
  hidden: { opacity: 0, x: -6 },
  show: { opacity: 1, x: 0 },
};

export default function OverviewPage() {
  // `null` means "not loaded yet", `[]` means "loaded and genuinely empty". Collapsing
  // those two into one value is what made the dashboard show a confident 0/$0 on first
  // paint, and an identical-looking empty shell when the backend was unreachable.
  const [summary, setSummary] = useState<Summary | null>(null);
  const [apps, setApps] = useState<AppSummary[] | null>(null);
  const [trends, setTrends] = useState<TrendPoint[] | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[] | null>(null);
  const [recs, setRecs] = useState<Recommendation[] | null>(null);

  usePolling(() => {
    api.getSummary(14).then(setSummary).catch(console.error);
    api.listApps().then(setApps).catch(console.error);
    api.getTrends({ days: 14 }).then(setTrends).catch(console.error);
    api.listAlerts(8).then(setAlerts).catch(console.error);
    api.listRecommendations().then((r) => setRecs(r.slice(0, 5))).catch(console.error);
  }, 8000);

  const loading = summary === null;

  return (
    <div>
      <PageHeader
        title="AI Fleet Overview"
        description="Real-time trust, cost, and risk posture across every monitored application — last 14 days."
      />

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4 mb-6">
        <StatCard
          label="Avg TrustScore"
          loading={loading}
          numericValue={summary?.avg_trust_score ?? 0}
          decimals={1}
          accentClass={summary ? trustScoreColor(summary.avg_trust_score) : ""}
          sub={`${summary?.total_interactions ?? 0} interactions evaluated`}
        />
        <StatCard
          label="Business Impact at Risk"
          loading={loading}
          numericValue={summary?.total_business_impact_usd ?? 0}
          prefix="$"
          accentClass="text-rose-600"
          sub="Estimated, illustrative assumptions"
        />
        <StatCard
          label="AI Spend"
          loading={loading}
          value={summary ? formatUsd(summary.total_ai_spend_usd) : "—"}
          sub="Across all monitored apps"
        />
        <StatCard
          label="Pending Human Reviews"
          loading={loading}
          numericValue={summary?.pending_human_reviews ?? 0}
          accentClass="text-amber-700"
          sub="Awaiting SLA-timed decision"
        />
        <StatCard
          label="Critical Incidents"
          loading={loading}
          numericValue={summary?.critical_incidents ?? 0}
          accentClass="text-rose-600"
          sub="TrustScore < 30"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card className="xl:col-span-2">
          <SectionLabel>TrustScore Trend (all apps)</SectionLabel>
          <div className="h-64">
            {trends === null ? (
              <div className="h-full flex flex-col justify-end gap-2 pb-6">
                <Skeleton className="h-full w-full opacity-60" />
              </div>
            ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends}>
                <XAxis dataKey="day" stroke="var(--muted)" fontSize={11} tickLine={false} />
                <YAxis domain={[0, 100]} stroke="var(--muted)" fontSize={11} tickLine={false} width={30} />
                <Tooltip
                  contentStyle={{ background: "#ffffff", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12, boxShadow: "0 4px 16px -4px rgba(10,0,17,0.12)" }}
                />
                <Line
                  isAnimationActive={false}
                  type="monotone"
                  dataKey="avg_trust_score"
                  stroke="var(--series-1)"
                  strokeWidth={2.5}
                  dot={false}
                  name="TrustScore"
                />
              </LineChart>
            </ResponsiveContainer>
            )}
          </div>
        </Card>

        <Card>
          <SectionLabel>Apps Under Management</SectionLabel>
          <div className="space-y-3">
            {apps === null &&
              [0, 1, 2].map((i) => (
                <div key={i} className="flex items-center justify-between pb-3">
                  <Skeleton className="h-8 w-40" />
                  <Skeleton className="h-8 w-24" />
                </div>
              ))}
            {(apps ?? []).map((app) => (
              <div key={app.id} className="flex items-center justify-between border-b border-border/60 last:border-0 pb-3 last:pb-0">
                <div>
                  <div className="text-sm font-medium">{app.name}</div>
                  <div className="text-xs text-muted-2 capitalize">{app.app_type.replace("_", " ")}</div>
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
            <SectionLabel icon={<Bell size={15} />} className="">Smart Alerts</SectionLabel>
            <span className="text-xs text-muted-2">deduplicated, last hour</span>
          </div>
          <motion.div variants={listVariants} initial="hidden" animate="show" className="space-y-2">
            {alerts === null && [0, 1, 2].map((i) => <Skeleton key={i} className="h-9 w-full" />)}
            {alerts?.length === 0 && (
              <div className="text-xs text-muted-2">
                No active alerts — nothing crossed a severity threshold in the last hour.
              </div>
            )}
            {(alerts ?? []).map((a) => (
              <motion.div key={a.id} variants={itemVariants} className="flex items-start gap-2 text-sm">
                <span
                  className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${
                    a.severity === "critical" ? "bg-rose-500 pulse-dot text-rose-600" : a.severity === "medium" ? "bg-amber-500" : "bg-slate-400"
                  }`}
                />
                <div className="flex-1">
                  <div className="text-foreground/90">{a.message}</div>
                  <div className="text-xs text-muted-2">
                    {a.count > 1 ? `${a.count}x · ` : ""}
                    {formatRelativeTime(a.updated_at)}
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-4">
            <SectionLabel icon={<Lightbulb size={15} />} className="">Top Prescriptive Actions</SectionLabel>
            <Link href="/impact" className="text-xs text-accent hover:underline">
              view all
            </Link>
          </div>
          <motion.div variants={listVariants} initial="hidden" animate="show" className="space-y-3">
            {recs === null && [0, 1, 2].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
            {recs?.length === 0 && (
              <div className="text-xs text-muted-2">
                No prescriptive actions outstanding — every flagged pattern has a resolution logged.
              </div>
            )}
            {(recs ?? []).map((r) => (
              <motion.div key={r.id} variants={itemVariants} className="text-sm">
                <div className="font-medium">{r.issue}</div>
                <div className="text-xs text-muted-2">{r.action}</div>
                <div className="text-xs text-emerald-600 mt-0.5">{formatUsd(r.estimated_value_usd)} potential value</div>
              </motion.div>
            ))}
          </motion.div>
        </Card>
      </div>

      <div className="mt-8 flex flex-wrap items-center gap-4 text-xs text-muted-2">
        {summary ? <TrustRing score={summary.avg_trust_score} size={36} /> : <Skeleton className="w-9 h-9 rounded-full" />}
        <span className="flex flex-wrap items-center gap-1.5 min-w-0">
          <ShieldAlert size={13} className="shrink-0" />
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
