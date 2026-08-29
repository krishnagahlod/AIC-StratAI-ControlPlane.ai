"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, PageHeader, StatCard } from "@/components/ui";
import AppFilter from "@/components/AppFilter";
import type { AppSummary, PlaygroundMetrics, PlaygroundRecommendation } from "@/lib/types";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function PlaygroundPage() {
  const [apps, setApps] = useState<AppSummary[]>([]);
  const [appId, setAppId] = useState<number | null>(null);
  const [threshold, setThreshold] = useState(50);
  const [metrics, setMetrics] = useState<PlaygroundMetrics | null>(null);
  const [recommendation, setRecommendation] = useState<PlaygroundRecommendation | null>(null);

  useEffect(() => {
    api.listApps().then(setApps).catch(console.error);
  }, []);

  useEffect(() => {
    api.recommendPlayground(appId).then(setRecommendation).catch(console.error);
  }, [appId]);

  useEffect(() => {
    const id = setTimeout(() => {
      api.simulatePlayground(threshold, appId).then(setMetrics).catch(console.error);
    }, 150);
    return () => clearTimeout(id);
  }, [threshold, appId]);

  return (
    <div>
      <PageHeader
        title="Policy Playground"
        description="Backtest a 'block if TrustScore < threshold' policy against labeled historical incidents before ever deploying it — no more guessing at guardrail aggressiveness."
      />

      <div className="mb-6">
        <AppFilter apps={apps} value={appId} onChange={setAppId} />
      </div>

      <Card className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium">Block if TrustScore &lt; {threshold}</label>
          {recommendation && (
            <button
              onClick={() => setThreshold(recommendation.recommended_threshold)}
              className="text-xs text-accent hover:underline"
            >
              Use recommended ({recommendation.recommended_threshold})
            </button>
          )}
        </div>
        <input
          type="range"
          min={5}
          max={95}
          step={5}
          value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))}
          className="w-full accent-[var(--accent)]"
        />
        {recommendation && <p className="text-xs text-muted mt-2">{recommendation.reason}</p>}
      </Card>

      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatCard label="Would Block" value={`${metrics.would_block} / ${metrics.total_labeled}`} />
          <StatCard
            label="False Positive Rate"
            value={`${(metrics.false_positive_rate * 100).toFixed(1)}%`}
            accentClass={metrics.false_positive_rate > 0.3 ? "text-rose-400" : "text-emerald-400"}
            sub="Fine responses incorrectly blocked"
          />
          <StatCard
            label="Recall"
            value={`${(metrics.recall * 100).toFixed(1)}%`}
            accentClass={metrics.recall < 0.5 ? "text-rose-400" : "text-emerald-400"}
            sub="Real problems actually caught"
          />
          <StatCard label="F1 Score" value={metrics.f1.toFixed(3)} />
        </div>
      )}

      {metrics && (
        <Card className="mb-6">
          <div className="text-sm font-medium mb-4">Confusion Matrix at threshold {threshold}</div>
          <div className="grid grid-cols-2 gap-3 max-w-md">
            <div className="bg-emerald-400/10 border border-emerald-400/30 rounded-lg p-3">
              <div className="text-xs text-muted">True Positives</div>
              <div className="text-xl font-semibold text-emerald-400">{metrics.true_positives}</div>
              <div className="text-xs text-muted">correctly blocked</div>
            </div>
            <div className="bg-rose-400/10 border border-rose-400/30 rounded-lg p-3">
              <div className="text-xs text-muted">False Positives</div>
              <div className="text-xl font-semibold text-rose-400">{metrics.false_positives}</div>
              <div className="text-xs text-muted">fine responses blocked</div>
            </div>
            <div className="bg-amber-400/10 border border-amber-400/30 rounded-lg p-3">
              <div className="text-xs text-muted">False Negatives</div>
              <div className="text-xl font-semibold text-amber-400">{metrics.false_negatives}</div>
              <div className="text-xs text-muted">real problems missed</div>
            </div>
            <div className="bg-surface-2 border border-border rounded-lg p-3">
              <div className="text-xs text-muted">True Negatives</div>
              <div className="text-xl font-semibold">{metrics.true_negatives}</div>
              <div className="text-xs text-muted">correctly allowed</div>
            </div>
          </div>
        </Card>
      )}

      {recommendation && (
        <Card>
          <div className="text-sm font-medium mb-4">F1 Score Across Thresholds</div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={recommendation.candidates}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="threshold" stroke="var(--muted)" fontSize={11} />
                <YAxis domain={[0, 1]} stroke="var(--muted)" fontSize={11} width={30} />
                <Tooltip contentStyle={{ background: "var(--surface-2)", border: "1px solid var(--border)", fontSize: 12 }} />
                <ReferenceLine x={threshold} stroke="#6d5efc" strokeDasharray="4 4" />
                <Line isAnimationActive={false} type="monotone" dataKey="f1" name="F1" stroke="#34d399" strokeWidth={2} dot={false} />
                <Line isAnimationActive={false} type="monotone" dataKey="false_positive_rate" name="FPR" stroke="#fb7185" strokeWidth={1.5} dot={false} />
                <Line isAnimationActive={false} type="monotone" dataKey="recall" name="Recall" stroke="#38bdf8" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}
    </div>
  );
}
