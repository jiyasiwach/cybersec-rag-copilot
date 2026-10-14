/** Pipeline diagram (inline SVG) + the design choices behind it. */
const STEPS = [
  { id: 'q', label: 'Question', sub: '≤ 1000 chars' },
  { id: 'g', label: 'Guardrail', sub: 'heuristics → LLM classifier' },
  { id: 'r', label: 'Hybrid retrieval', sub: 'vector + BM25, RRF k=60' },
  { id: 'p', label: 'Prompt', sub: 'numbered context, delimited' },
  { id: 'l', label: 'LLM', sub: 'streamed tokens' },
  { id: 'a', label: 'Answer', sub: 'citations [n] + metrics' },
];

function Diagram() {
  const W = 150, H = 60, GAP = 26;
  const total = STEPS.length * W + (STEPS.length - 1) * GAP;
  return (
    <svg viewBox={`0 0 ${total} ${H + 40}`} className="w-full" role="img" aria-label="RAG pipeline diagram">
      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
          <path d="M0,0 L8,4 L0,8 z" fill="var(--color-accent)" />
        </marker>
      </defs>
      {STEPS.map((s, i) => {
        const x = i * (W + GAP);
        const danger = s.id === 'g';
        return (
          <g key={s.id}>
            <rect x={x} y={10} width={W} height={H} rx={8} fill="var(--color-panel)" stroke={danger ? 'var(--color-danger)' : 'var(--color-line)'} />
            <text x={x + W / 2} y={34} textAnchor="middle" fill="#fff" fontSize="13" fontWeight="600" fontFamily="var(--font-sans)">{s.label}</text>
            <text x={x + W / 2} y={52} textAnchor="middle" fill="var(--color-muted)" fontSize="10" fontFamily="var(--font-mono)">{s.sub}</text>
            {i < STEPS.length - 1 && (
              <line x1={x + W + 2} y1={10 + H / 2} x2={x + W + GAP - 4} y2={10 + H / 2} stroke="var(--color-accent)" strokeWidth="1.5" markerEnd="url(#arrow)" />
            )}
          </g>
        );
      })}
      {/* blocked branch out of the guardrail */}
      <line x1={W + GAP + W / 2} y1={10 + H} x2={W + GAP + W / 2} y2={H + 30} stroke="var(--color-danger)" strokeWidth="1.5" strokeDasharray="4 3" />
      <text x={W + GAP + W / 2 + 6} y={H + 32} fill="var(--color-danger)" fontSize="10" fontFamily="var(--font-mono)">blocked → verdict + reason</text>
      {/* knowledge base feeding retrieval */}
      <text x={2 * (W + GAP) + W / 2} y={H + 32} textAnchor="middle" fill="var(--color-muted)" fontSize="10" fontFamily="var(--font-mono)">↑ ChromaDB + BM25 over MITRE · OWASP · CISA KEV</text>
    </svg>
  );
}

const CHOICES: { title: string; body: string }[] = [
  {
    title: 'One natural unit per chunk',
    body: 'A technique, an OWASP category or a CVE is one chunk; only oversized units are split into ~500-token pieces with 60-token overlap and the title repeated. Citations then point at something a human recognises.',
  },
  {
    title: 'Hybrid retrieval with Reciprocal Rank Fusion',
    body: 'Vector search handles paraphrased, conceptual questions; BM25 nails exact IDs like T1059.001 or CVE-2015-5477 that embeddings blur. RRF (k=60) merges the two rankings without tuning weights, and an exact-ID boost pins a matching chunk to position 1.',
  },
  {
    title: 'Two-layer guardrail, before retrieval',
    body: 'Cheap regex heuristics catch obvious injections for free; only ambiguous scores go to a small LLM classifier returning strict JSON. Retrieved chunks are wrapped in delimiters and declared as data, never instructions, to blunt indirect injection.',
  },
  {
    title: 'Grounded or nothing',
    body: 'The prompt only allows claims from the numbered context and requires a [n] citation on each. If the context lacks the answer, the model must say so — measured by the faithfulness and citation-accuracy evals.',
  },
  {
    title: 'Server-sent events',
    body: 'One POST streams guardrail → sources → tokens → done. The UI can show the verdict and the source chips before the first token arrives, and the final event carries latency, tokens and cost.',
  },
];

export default function ArchitecturePage() {
  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 py-8">
      <div>
        <h1 className="text-xl font-semibold text-white">Architecture</h1>
        <p className="mt-1 text-sm text-muted">FastAPI + ChromaDB + rank_bm25 + OpenAI on the backend; React + Vite on the front.</p>
      </div>
      <div className="overflow-x-auto rounded-lg border border-line bg-bg p-4">
        <div className="min-w-[900px]"><Diagram /></div>
      </div>
      <section className="grid gap-3 sm:grid-cols-2">
        {CHOICES.map((c) => (
          <div key={c.title} className="rounded-lg border border-line bg-panel p-4">
            <h2 className="text-sm font-semibold text-white">{c.title}</h2>
            <p className="mt-1 text-sm leading-relaxed text-text/85">{c.body}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
