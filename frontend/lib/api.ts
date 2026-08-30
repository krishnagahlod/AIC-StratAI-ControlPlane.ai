import type {
  AlertItem,
  AppSummary,
  ImpactBreakdownItem,
  InteractionSummary,
  NarrativeResponse,
  PlaygroundMetrics,
  PlaygroundRecommendation,
  Recommendation,
  ReviewQueueItem,
  Summary,
  TrendPoint,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Request to ${path} failed (${res.status}): ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listApps: () => request<AppSummary[]>("/api/apps"),

  listInteractions: (params: { appId?: number | null; sinceId?: number; limit?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.appId) qs.set("app_id", String(params.appId));
    if (params.sinceId) qs.set("since_id", String(params.sinceId));
    qs.set("limit", String(params.limit ?? 50));
    return request<InteractionSummary[]>(`/api/interactions?${qs.toString()}`);
  },

  getInteraction: (id: number) => request<InteractionSummary>(`/api/interactions/${id}`),

  getTrends: (params: { appId?: number | null; days?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.appId) qs.set("app_id", String(params.appId));
    qs.set("days", String(params.days ?? 14));
    return request<TrendPoint[]>(`/api/trends?${qs.toString()}`);
  },

  listAlerts: (limit = 20) => request<AlertItem[]>(`/api/alerts?limit=${limit}`),

  listRecommendations: (appId?: number | null) => {
    const qs = new URLSearchParams();
    if (appId) qs.set("app_id", String(appId));
    return request<Recommendation[]>(`/api/recommendations?${qs.toString()}`);
  },

  getSummary: (days = 7) => request<Summary>(`/api/summary?days=${days}`),

  getImpactBreakdown: (appId?: number | null, days = 14) => {
    const qs = new URLSearchParams({ days: String(days) });
    if (appId) qs.set("app_id", String(appId));
    return request<ImpactBreakdownItem[]>(`/api/impact-breakdown?${qs.toString()}`);
  },

  getNarrative: (audience: string, appId?: number | null, days = 7) => {
    const qs = new URLSearchParams({ audience, days: String(days) });
    if (appId) qs.set("app_id", String(appId));
    return request<NarrativeResponse>(`/api/narrator?${qs.toString()}`);
  },

  listReviewQueue: (status?: string) => {
    const qs = new URLSearchParams();
    if (status) qs.set("status", status);
    return request<ReviewQueueItem[]>(`/api/review-queue?${qs.toString()}`);
  },

  decideReview: (id: number, action: "approve" | "reject" | "edit", note?: string, editedResponse?: string) =>
    request<{ ok: boolean; status: string }>(`/api/review-queue/${id}/decision`, {
      method: "POST",
      body: JSON.stringify({ action, note, edited_response: editedResponse }),
    }),

  simulatePlayground: (threshold: number, appId?: number | null) => {
    const qs = new URLSearchParams({ threshold: String(threshold) });
    if (appId) qs.set("app_id", String(appId));
    return request<PlaygroundMetrics>(`/api/playground/simulate?${qs.toString()}`);
  },

  recommendPlayground: (appId?: number | null) => {
    const qs = new URLSearchParams();
    if (appId) qs.set("app_id", String(appId));
    return request<PlaygroundRecommendation>(`/api/playground/recommend?${qs.toString()}`);
  },

  sendChat: (payload: {
    appKey: string;
    prompt: string;
    ragContext?: string;
    taskType?: string;
  }) =>
    request<{
      choices: Array<{ message: { content: string } }>;
      controlplane: { interaction_id: number; sync_action: string; sync_flags: unknown[]; latency_ms: number };
      usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
    }>("/v1/chat/completions", {
      method: "POST",
      body: JSON.stringify({
        messages: [{ role: "user", content: payload.prompt }],
        metadata: { app_key: payload.appKey, task_type: payload.taskType ?? "general" },
        rag_context: payload.ragContext || undefined,
      }),
    }),
};
