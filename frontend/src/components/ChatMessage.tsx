import type { CitedChunk, GuardrailResult, Metrics, RetrievalMode } from '../types';
import AnswerMarkdown from './AnswerMarkdown';
import BlockedMessage from './BlockedMessage';
import MetricsStrip from './MetricsStrip';
import SourceBadge from './SourceBadge';

/** One Q&A turn. `status` drives the streaming caret and spinners. */
export interface Turn {
  id: number;
  question: string;
  mode: RetrievalMode;
  status: 'guarding' | 'retrieving' | 'generating' | 'done' | 'error';
  guardrail?: GuardrailResult;
  sources: CitedChunk[];
  answer: string;
  metrics?: Metrics;
  error?: string;
}

interface Props { turn: Turn; onCite: (turn: Turn, n: number) => void }

export default function ChatMessage({ turn, onCite }: Props) {
  const blocked = turn.guardrail?.blocked === true;
  return (
    <div className="space-y-3">
      {/* user */}
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-lg bg-panel-2 px-3 py-2 text-sm text-white">{turn.question}</div>
      </div>

      {/* assistant */}
      <div className="max-w-[95%] rounded-lg border border-line bg-panel p-3">
        <div className="mb-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-muted">
          <span>copilot</span><span>·</span><span>{turn.mode}</span>
          {turn.status !== 'done' && turn.status !== 'error' && <span className="text-accent">· {turn.status}…</span>}
        </div>

        {blocked && turn.guardrail && <BlockedMessage g={turn.guardrail} />}

        {!blocked && turn.sources.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-1.5">
            {turn.sources.map((s) => (
              <button
                key={s.chunk_id}
                type="button"
                onClick={() => onCite(turn, s.n)}
                className="flex items-center gap-1.5 rounded border border-line bg-panel-2 px-2 py-1 text-left hover:border-accent/60"
                title={s.title}
              >
                <span className="font-mono text-[10px] text-accent">[{s.n}]</span>
                <SourceBadge source={s.source} />
                <span className="font-mono text-[11px] text-text">{s.doc_id}</span>
              </button>
            ))}
          </div>
        )}

        {!blocked && (turn.answer || turn.status === 'generating') && (
          <AnswerMarkdown
            text={turn.answer}
            citationCount={turn.sources.length}
            streaming={turn.status === 'generating'}
            onCite={(n) => onCite(turn, n)}
          />
        )}

        {turn.status === 'error' && <p className="text-sm text-danger">{turn.error ?? 'Request failed.'}</p>}
        {turn.metrics && !blocked && <MetricsStrip m={turn.metrics} />}
      </div>
    </div>
  );
}
