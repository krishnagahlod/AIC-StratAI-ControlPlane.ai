export type Severity = "low" | "medium" | "high" | "critical";

export interface Flag {
  type: string;
  dimension: "performance" | "cost" | "responsibility";
  severity: Severity;
  method: "deterministic" | "llm_judge" | "rule_based";
  detail: string;
  evidence?: Record<string, unknown>;
  action_taken?: string;
}

export interface AppWeights {
  performance: number;
  cost: number;
  responsibility: number;
}

export interface AppSummary {
  id: number;
  key: string;
  name: string;
  app_type: string;
  risk_tolerance: string;
  latency_budget_ms: number;
  weights: AppWeights;
  daily_budget_usd: number;
  daily_spend_usd: number;
  budget_remaining_pct: number;
}

export interface EvaluationSummary {
  performance_score: number;
  cost_score: number;
  responsibility_score: number;
  trust_score: number;
  risk_level: "minimal" | "low" | "moderate" | "critical";
  response_cost_usd: number;
  flags: Flag[];
}

export interface BusinessImpactSummary {
  risk_category: string;
  estimated_impact_usd: number;
  affected_users: number;
  confidence: number;
  narrative: string;
}

export interface EscalationSummary {
  decision: string;
  status: string;
  sla_seconds: number | null;
  sla_deadline: string | null;
}

export interface InteractionSummary {
  id: number;
  app_id: number;
  app_name: string | null;
  created_at: string;
  task_type: string;
  prompt: string;
  response: string;
  model: string;
  latency_ms: number;
  sync_action: string;
  sync_flags: Array<Record<string, unknown>>;
  source: "live" | "seed";
  evaluation: EvaluationSummary | null;
  business_impact: BusinessImpactSummary | null;
  escalation: EscalationSummary | null;
  raw_response?: string;
  rag_context?: string | null;
}

export interface TrendPoint {
  day: string;
  avg_trust_score: number;
  avg_performance: number;
  avg_cost: number;
  avg_responsibility: number;
  total_cost_usd: number;
  count: number;
}

export interface AlertItem {
  id: number;
  severity: string;
  message: string;
  count: number;
  app_id: number | null;
  interaction_id: number | null;
  updated_at: string;
}

export interface Recommendation {
  id: number;
  app_id: number | null;
  priority: number;
  issue: string;
  root_cause: string;
  action: string;
  expected_impact: string;
  estimated_value_usd: number;
  confidence: number;
  method: string;
  created_at: string;
}

export interface Summary {
  window_days: number;
  total_interactions: number;
  avg_trust_score: number;
  total_business_impact_usd: number;
  total_ai_spend_usd: number;
  pending_human_reviews: number;
  critical_incidents: number;
  assumptions: Record<string, number>;
}

export interface ReviewQueueItem {
  id: number;
  interaction_id: number;
  app_name: string | null;
  prompt: string | null;
  response: string | null;
  trust_score: number | null;
  flags: Flag[];
  decision: string;
  status: string;
  sla_seconds: number | null;
  seconds_remaining: number | null;
  reviewer_decision: string | null;
  created_at: string;
}

export interface PlaygroundMetrics {
  threshold: number;
  total_labeled: number;
  would_block: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  true_negatives: number;
  precision: number;
  recall: number;
  false_positive_rate: number;
  f1: number;
}

export interface GroundingVerdict {
  status: "verified" | "corrected" | "fallback" | "unavailable";
  passed: boolean;
  unsupported_terms: string[];
  checked_terms?: number;
  attempts: number;
  method: string;
}

export interface NarrativeResponse {
  narrative: string;
  grounding: GroundingVerdict;
  cached: boolean;
}

export interface ImpactBreakdownItem {
  risk_category: string;
  total_usd: number;
  count: number;
}

export interface PlaygroundRecommendation {
  recommended_threshold: number;
  reason: string;
  candidates: PlaygroundMetrics[];
}
