"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { usePolling } from "@/lib/hooks";
import { Card, PageHeader, SectionLabel } from "@/components/ui";
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

  const tooltipStyle = { background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 };

  return (
    <div>
      <PageHeader title="Trends" description="Day-over-day drift in TrustScore and its sub-dimensions — the signal for catching silent degradation." />

      <div className="flex gap-3 mb-6 overflow-x-auto no-scrollbar pb-1">
        <AppFilter apps={apps} value={appId} onChange={setAppId} />
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="bg-surface-2 border border-border rounded-xl px-3.5 h-10 text-sm shrink-0 focus:outline-none focus:ring-2 focus:ring-accent/50"
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
              <XAxis dataKey="day" stroke="var(--muted)" fontSize={11} />
              <YAxis domain={[0, 100]} stroke="var(--muted)" fontSize={11} width={30} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line isAnimationActive={false} type="monotone" dataKey="avg_trust_score" name="TrustScore" stroke="var(--accent)" strokeWidth={2.5} dot={false} />
              <Line isAnimationActive={false} type="monotone" dataKey="avg_performance" name="Performance" stroke="#38bdf8" strokeWidth={1.5} dot={false} />
              <Line isAnimationActive={false} type="monotone" dataKey="avg_cost" name="Cost" stroke="var(--accent-2)" strokeWidth={1.5} dot={false} />
              <Line isAnimationActive={false} type="monotone" dataKey="avg_responsibility" name="Responsibility" stroke="#fb923c" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card>
        <SectionLabel>Daily Interaction Volume & AI Spend</SectionLabel>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="day" stroke="var(--muted)" fontSize={11} />
              <YAxis yAxisId="left" stroke="var(--muted)" fontSize={11} width={30} />
              <YAxis yAxisId="right" orientation="right" stroke="var(--muted)" fontSize={11} width={40} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line isAnimationActive={false} yAxisId="left" type="monotone" dataKey="count" name="Interactions" stroke="#a78bfa" strokeWidth={2} dot={false} />
              <Line isAnimationActive={false} yAxisId="right" type="monotone" dataKey="total_cost_usd" name="Cost (USD)" stroke="#f472b6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}
