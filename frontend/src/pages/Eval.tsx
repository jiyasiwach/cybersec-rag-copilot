import { useEffect, useState } from 'react';
import { getEvalResults } from '../api/client';
import type { EvalResults, RetrievalMode } from '../types';

const pct = (x: number) => `${(x * 100).toFixed(0)}%`;
const MODES: RetrievalMode[] = ['hybrid', 'vector', 'bm25'];

function Card({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-lg border border-line bg-panel p-4">
      <div className="text-[10px] uppercase tracking-wider text-muted">{label}</div>
      <div className="mt-1 font-mono text-2xl text-accent">{value}</div>
      {sub && <div className="mt-1 text-xs text-muted">{sub}</div>}
    </div>
  );
}

export default function EvalPage() {
  const [data, setData] = useState<EvalResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getEvalResults().then(setData).catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="p-6 text-sm text-danger">Could not load eval results: {error}</p>;
  if (!data) return <p className="p-6 font-mono text-sm text-muted">loading results…</p>;

  const best = MODES.reduce((a, b) => (data.retrieval[b].mrr > data.retrieval[a].mrr ? b : a));

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 py-8">
      <div>
        <h1 className="text-xl font-semibold text-white">Evaluation</h1>
        <p className="mt-1 font-mono text-xs text-muted">
          run {new Date(data.run_at).toLocaleString()} · {data.counts.questions} questions · {data.counts.attacks} attacks · {data.counts.off_topic} off-topic · {data.llm_model} / {data.embedding_model}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Card label="Hybrid Hit@5" value={pct(data.retrieval.hybrid.hit_at_5)} sub={`MRR ${data.retrieval.hybrid.mrr.toFixed(2)}`} />
        <Card label="Faithfulness" value={pct(data.answers.faithfulness)} sub="LLM-as-judge, hybrid answers" />
        <Card label="Citation accuracy" value={pct(data.answers.citation_accuracy)} sub="cited chunk supports the claim" />
        <Card label="Avg latency" value={`${(data.avg_latency_ms / 1000).toFixed(2)} s`} sub={`$${data.avg_cost_usd.toFixed(5)} per query`} />
      </div>

      <section>
        <h2 className="mb-2 text-sm font-semibold text-white">Retrieval modes</h2>
        <table className="w-full overflow-hidden rounded-lg border border-line text-sm">
          <thead className="bg-panel-2 text-left text-[10px] uppercase tracking-wider text-muted">
            <tr><th className="px-3 py-2">Mode</th><th className="px-3 py-2">Hit@5</th><th className="px-3 py-2">MRR</th><th className="px-3 py-2"></th></tr>
          </thead>
          <tbody className="bg-panel font-mono">
            {MODES.map((m) => (
              <tr key={m} className="border-t border-line">
                <td className="px-3 py-2 text-text">{m}</td>
                <td className="px-3 py-2">{pct(data.retrieval[m].hit_at_5)}</td>
                <td className="px-3 py-2">{data.retrieval[m].mrr.toFixed(3)}</td>
                <td className="px-3 py-2 text-xs text-accent">{m === best ? 'best' : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2 className="mb-2 text-sm font-semibold text-white">Guardrail</h2>
        <div className="grid gap-3 sm:grid-cols-3">
          <Card label="Attacks blocked" value={pct(data.guardrail.block_rate)} sub={`${data.counts.attacks} prompt-injection attempts`} />
          <Card label="Off-topic refused" value={pct(data.guardrail.off_topic_block_rate)} sub={`${data.counts.off_topic} non-security questions`} />
          <Card label="False positives" value={pct(data.guardrail.false_positive_rate)} sub={`normal questions wrongly blocked (of ${data.counts.questions})`} />
        </div>
      </section>
    </div>
  );
}
