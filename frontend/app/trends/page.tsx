"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { usePolling } from "@/lib/hooks";
import { Card, PageHeader, SectionLabel } from "@/components/ui";
import { formatUsdAxis, usdAxisWidth } from "@/lib/format";
import AppFilter from "@/components/AppFilter";
import type { AppSummary, TrendPoint } from "@/lib/types";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function TrendsPage() {
  const [apps, setApps] = useState<AppSummary[]>([]);
  const [appId, setAppId] = useState<number | null>(null);
  const [days, setDays] = useState(14);
  const [trends, setTrends] = useState<TrendPoint[]>([]);

  usePolling(() => {
    api.listApps().then(setApps).catch(console.error);
  }, 15000);

  usePolling(() => {
    api.getTrends({ appId, days }).then(setTrends).catch(console.error);
  }, 5000, [appId, days]);

  const tooltipStyle = { background: "#ffffff", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12, boxShadow: "0 4px 16px -4px rgba(10,0,17,0.12)" };
  const maxSpend = trends.length ? Math.max(...trends.map((t) => t.total_cost_usd)) : 0;

  return (
    <div>
      <PageHeader title="Trends" description="Day-over-day drift in TrustScore and its sub-dimensions — the signal for catching silent degradation." />

      <div className="flex gap-3 mb-6 overflow-x-auto no-scrollbar pb-1">
        <AppFilter apps={apps} value={appId} onChange={setAppId} />
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="bg-white border border-border rounded-xl px-3.5 h-10 text-sm font-medium shrink-0 focus:outline-none focus:ring-2 focus:ring-accent/30"
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
        </select>
      </div>

      <Card className="mb-6">
        <SectionLabel>TrustScore & Sub-Scores</SectionLabel>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="day" stroke="var(--muted-2)" fontSize={11} />
              <YAxis domain={[0, 100]} stroke="var(--muted-2)" fontSize={11} width={30} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line isAnimationActive={false} type="monotone" dataKey="avg_trust_score" name="TrustScore" stroke="var(--series-1)" strokeWidth={2.5} dot={false} />
              <Line isAnimationActive={false} type="monotone" dataKey="avg_performance" name="Performance" stroke="var(--series-3)" strokeWidth={1.5} dot={false} />
              <Line isAnimationActive={false} type="monotone" dataKey="avg_cost" name="Cost" stroke="var(--series-2)" strokeWidth={1.5} dot={false} />
              <Line isAnimationActive={false} type="monotone" dataKey="avg_responsibility" name="Responsibility" stroke="var(--series-4)" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <SectionLabel>Daily Interaction Volume</SectionLabel>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="day" stroke="var(--muted-2)" fontSize={11} />
                <YAxis stroke="var(--muted-2)" fontSize={11} width={30} />
                <Tooltip contentStyle={tooltipStyle} />
                <Line isAnimationActive={false} type="monotone" dataKey="count" name="Interactions" stroke="var(--series-1)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <SectionLabel>Daily AI Spend (USD)</SectionLabel>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends} margin={{ left: 4, right: 8, top: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="day" stroke="var(--muted-2)" fontSize={11} />
                <YAxis
                  stroke="var(--muted-2)"
                  fontSize={11}
                  width={usdAxisWidth(maxSpend)}
                  // Headroom so peak days don't flatten against the top of the plot.
                  domain={[0, maxSpend > 0 ? maxSpend * 1.15 : "auto"]}
                  tickFormatter={(v: number) => formatUsdAxis(v, maxSpend)}
                />
                <Tooltip contentStyle={tooltipStyle} formatter={(v) => formatUsdAxis(Number(v), maxSpend)} />
                <Line isAnimationActive={false} type="monotone" dataKey="total_cost_usd" name="Cost (USD)" stroke="var(--series-2)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-muted-2 mt-2">
            Per-call inference cost is genuinely sub-cent at this volume — the axis scales to keep
            day-over-day movement legible.
          </p>
        </Card>
      </div>
    </div>
  );
}
