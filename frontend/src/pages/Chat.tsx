import { useEffect, useRef, useState } from 'react';
import { streamChat } from '../api/client';
import type { CitedChunk, RetrievalMode } from '../types';
import ChatMessage, { type Turn } from '../components/ChatMessage';
import CitationPanel from '../components/CitationPanel';
import ExampleQuestions from '../components/ExampleQuestions';
import ModeToggle from '../components/ModeToggle';

const MAX_CHARS = 1000;

export default function ChatPage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<RetrievalMode>('hybrid');
  const [cited, setCited] = useState<CitedChunk | null>(null);
  const abortRef = useRef<(() => void) | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const busy = turns.some((t) => t.status !== 'done' && t.status !== 'error');

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [turns]);
  useEffect(() => () => abortRef.current?.(), []);

  function patch(id: number, fn: (t: Turn) => Turn) {
    setTurns((prev) => prev.map((t) => (t.id === id ? fn(t) : t)));
  }

  function ask(question: string) {
    const q = question.trim();
    if (!q || busy) return;
    const id = Date.now();
    setTurns((prev) => [...prev, { id, question: q, mode, status: 'guarding', sources: [], answer: '' }]);
    setInput('');
    setCited(null);

    abortRef.current = streamChat({ question: q, mode }, (e) => {
      switch (e.type) {
        case 'guardrail':
          patch(id, (t) => ({ ...t, guardrail: e.data, status: e.data.blocked ? 'done' : 'retrieving' }));
          break;
        case 'sources':
          patch(id, (t) => ({ ...t, sources: e.data, status: 'generating' }));
          break;
        case 'token':
          patch(id, (t) => ({ ...t, answer: t.answer + e.data }));
          break;
        case 'done':
          patch(id, (t) => ({ ...t, metrics: e.data, status: 'done' }));
          break;
        case 'error':
          patch(id, (t) => ({ ...t, status: 'error', error: e.data.message }));
          break;
      }
    });
  }

  function stop() {
    abortRef.current?.();
    setTurns((prev) => prev.map((t) => (t.status === 'done' || t.status === 'error' ? t : { ...t, status: 'error', error: 'Stopped.' })));
  }

  function onCite(turn: Turn, n: number) {
    setCited(turn.sources.find((s) => s.n === n) ?? null);
  }

  return (
    <div className="flex h-full">
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="min-h-0 flex-1 overflow-y-auto">
          {turns.length === 0 ? (
            <ExampleQuestions onPick={ask} />
          ) : (
            <div className="mx-auto max-w-3xl space-y-6 px-4 py-6">
              {turns.map((t) => <ChatMessage key={t.id} turn={t} onCite={onCite} />)}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <form
          onSubmit={(e) => { e.preventDefault(); ask(input); }}
          className="border-t border-line bg-panel px-4 py-3"
        >
          <div className="mx-auto max-w-3xl">
            <div className="mb-2 flex items-center justify-between gap-2">
              <ModeToggle value={mode} onChange={setMode} disabled={busy} />
              <span className={`font-mono text-[10px] ${input.length > MAX_CHARS ? 'text-danger' : 'text-muted'}`}>
                {input.length}/{MAX_CHARS}
              </span>
            </div>
            <div className="flex gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(input); } }}
                rows={2}
                maxLength={MAX_CHARS}
                placeholder="Ask a cybersecurity question… (Enter to send, Shift+Enter for newline)"
                className="min-w-0 flex-1 resize-none rounded border border-line bg-bg px-3 py-2 text-sm text-text outline-none placeholder:text-muted focus:border-accent/60"
              />
              {busy ? (
                <button type="button" onClick={stop} className="rounded border border-danger/50 px-4 text-sm text-danger hover:bg-danger/10">Stop</button>
              ) : (
                <button type="submit" disabled={!input.trim()} className="rounded bg-accent px-4 text-sm font-semibold text-bg hover:bg-cyan-300 disabled:opacity-40">Send</button>
              )}
            </div>
          </div>
        </form>
      </div>

      {/* Citation side panel: overlays on mobile, docks on desktop */}
      {cited && (
        <div className="fixed inset-0 z-20 bg-black/60 md:static md:z-auto md:bg-transparent" onClick={() => setCited(null)}>
          <div className="absolute inset-y-0 right-0 w-[92%] max-w-[380px] md:static md:h-full md:w-auto md:max-w-none" onClick={(e) => e.stopPropagation()}>
            <CitationPanel chunk={cited} onClose={() => setCited(null)} />
          </div>
        </div>
      )}
    </div>
  );
}
