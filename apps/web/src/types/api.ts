/** TypeScript types matching the FastAPI backend schemas. */

export interface Event {
  event_id: string;
  title: string;
  summary?: string;
  status: 'candidate' | 'researching' | 'verified' | 'disputed' | 'rejected' | 'archived';
  severity?: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  topic_label?: string;
  created_at: string;
  updated_at?: string;
  entities?: Record<string, unknown>;
  geography?: Record<string, unknown>;
}

export interface Evidence {
  claim: string;
  stance?: string;
  reliability_score: number;
  evidence_text?: string;
  source_url?: string;
}

export interface AgentDecision {
  agent_name: string;
  status: string;
  output: Record<string, unknown>;
  latency_ms?: number;
  created_at: string;
}

export interface Report {
  report_id: string;
  event_id?: string;
  title: string;
  markdown?: string;
  confidence: number;
  citations?: Citation[];
  created_at: string;
}

export interface Citation {
  source_name: string;
  url: string;
  claim: string;
  reliability_score: number;
}

export interface TopicCluster {
  topic_id: string;
  label: string;
  keywords: string[];
  article_count: number;
  coherence_score?: number;
  velocity_score?: number;
}

export interface SemanticVelocity {
  topic_id: string;
  label: string;
  velocity_score: number;
  acceleration_score: number;
  anomaly_score: number;
  article_count: number;
  window_start: string;
  window_end: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: string;
}

export interface AgentActivity {
  agent_name: string;
  event_id: string;
  event_title: string;
  status: 'running' | 'completed' | 'failed';
  latency_ms?: number;
  model_name?: string;
  cost_usd?: number;
  started_at: string;
}

export interface AnalyzeRequest {
  articles: {
    title: string;
    body: string;
    source?: string;
    url?: string;
  }[];
  default_reliability_score?: number;
}

export interface AnalyzeResponse {
  status: string;
  event: Event;
  report: Report;
  evidence: Evidence[];
  decisions: AgentDecision[];
}

export interface HealthResponse {
  status: string;
  services: {
    postgres: string;
    redis: string;
    qdrant: string;
  };
}
