import type { RetrievalMode } from '../types';

const MODES: { value: RetrievalMode; label: string; hint: string }[] = [
  { value: 'hybrid', label: 'Hybrid', hint: 'Vector + BM25 fused with RRF' },
  { value: 'vector', label: 'Vector', hint: 'Embedding cosine similarity' },
  { value: 'bm25', label: 'BM25', hint: 'Keyword search' },
];

interface Props { value: RetrievalMode; onChange: (m: RetrievalMode) => void; disabled?: boolean }

export default function ModeToggle({ value, onChange, disabled }: Props) {
  return (
    <div className="inline-flex rounded border border-line bg-panel p-0.5" role="radiogroup" aria-label="Retrieval mode">
      {MODES.map((m) => (
        <button
          key={m.value}
          type="button"
          role="radio"
          aria-checked={value === m.value}
          title={m.hint}
          disabled={disabled}
          onClick={() => onChange(m.value)}
          className={`rounded px-2.5 py-1 font-mono text-xs transition ${
            value === m.value ? 'bg-accent-dim/40 text-accent' : 'text-muted hover:text-text'
          } disabled:opacity-50`}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}
