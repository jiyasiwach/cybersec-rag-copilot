import type { Metrics } from '../types';

function Item({ label, value }: { label: string; value: string }) {
  return (
    <span className="flex items-baseline gap-1">
      <span className="text-[10px] uppercase tracking-wider text-muted">{label}</span>
      <span className="font-mono text-xs text-text">{value}</span>
    </span>
  );
}

/** Latency / tokens / cost line shown under each answer. */
export default function MetricsStrip({ m }: { m: Metrics }) {
  return (
    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 border-t border-line pt-2">
      <Item label="retrieval" value={`${m.retrieval_ms} ms`} />
      <Item label="generation" value={`${m.generation_ms} ms`} />
      <Item label="total" value={`${m.total_ms} ms`} />
      <Item label="tokens" value={`${m.prompt_tokens} in / ${m.completion_tokens} out`} />
      <Item label="cost" value={`$${m.est_cost_usd.toFixed(5)}`} />
    </div>
  );
}
