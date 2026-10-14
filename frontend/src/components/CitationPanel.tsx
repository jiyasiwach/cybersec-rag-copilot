import type { CitedChunk } from '../types';
import SourceBadge from './SourceBadge';

interface Props { chunk: CitedChunk | null; onClose: () => void }

/** Right-hand side panel showing the full retrieved chunk behind a citation chip. */
export default function CitationPanel({ chunk, onClose }: Props) {
  if (!chunk) return null;
  return (
    <aside className="flex h-full w-full flex-col border-l border-line bg-panel md:w-[380px]">
      <div className="flex items-center justify-between border-b border-line px-4 py-2.5">
        <span className="font-mono text-xs text-muted">source [{chunk.n}]</span>
        <button type="button" onClick={onClose} className="text-muted hover:text-text" aria-label="Close">✕</button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        <div className="flex flex-wrap items-center gap-2">
          <SourceBadge source={chunk.source} />
          <span className="font-mono text-xs text-accent">{chunk.doc_id}</span>
          {chunk.score !== undefined && <span className="font-mono text-[10px] text-muted">score {chunk.score.toFixed(3)}</span>}
        </div>
        <h3 className="mt-2 text-sm font-semibold text-white">{chunk.title}</h3>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-text/90">{chunk.text}</p>
        <a href={chunk.url} target="_blank" rel="noreferrer" className="mt-4 inline-flex items-center gap-1 text-xs text-accent hover:underline">
          Open original source ↗
        </a>
        <p className="mt-3 font-mono text-[10px] text-muted">{chunk.chunk_id}</p>
      </div>
    </aside>
  );
}
