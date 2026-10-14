/** Shared API types. These mirror the FastAPI models exactly (section 7 of the spec). */

export type Source = 'mitre' | 'owasp' | 'cisa_kev';
export type RetrievalMode = 'hybrid' | 'vector' | 'bm25';

export interface Chunk {
  chunk_id: string;
  source: Source;
  doc_id: string;   // e.g. T1053.005, A03:2021, CVE-2024-3400
  title: string;
  url: string;
  text: string;
}

/** A retrieved chunk as sent in the `sources` SSE event: numbered for [n] citations. */
export interface CitedChunk extends Chunk {
  n: number;
  score?: number;
}

export type Verdict = 'safe' | 'injection' | 'off_topic';
export type GuardLayer = 'heuristic' | 'classifier';

export interface GuardrailResult {
  blocked: boolean;
  verdict: Verdict;
  reason: string;
  layer: GuardLayer | null;   // which layer decided; null when nothing matched
  risk_score: number;         // 0..1 from the heuristic layer
}

export interface Metrics {
  retrieval_ms: number;
  generation_ms: number;
  total_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  est_cost_usd: number;
}

/** Discriminated union of SSE events, in the order the server emits them. */
export type ChatEvent =
  | { type: 'guardrail'; data: GuardrailResult }
  | { type: 'sources'; data: CitedChunk[] }
  | { type: 'token'; data: string }
  | { type: 'done'; data: Metrics }
  | { type: 'error'; data: { message: string } };

export interface ChatRequest {
  question: string;
  mode: RetrievalMode;
}

/** Shape of backend/evals/results.json (produced in M6). */
export interface EvalResults {
  run_at: string;                 // ISO timestamp
  llm_model: string;
  embedding_model: string;
  counts: { questions: number; attacks: number; off_topic: number };
  retrieval: Record<RetrievalMode, { hit_at_5: number; mrr: number }>;
  answers: { faithfulness: number; citation_accuracy: number };
  guardrail: { block_rate: number; off_topic_block_rate: number; false_positive_rate: number };
  avg_latency_ms: number;
  avg_cost_usd: number;
}
