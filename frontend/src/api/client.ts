import type { ChatEvent, ChatRequest, Chunk, EvalResults } from '../types';

export const API_URL: string = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000';

/** Parse one SSE frame ("event: x\ndata: y") into a ChatEvent. */
function parseFrame(frame: string): ChatEvent | null {
  let event = 'message';
  const dataLines: string[] = [];
  for (const line of frame.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim();
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart());
  }
  if (dataLines.length === 0) return null;
  const data = JSON.parse(dataLines.join('\n'));
  switch (event) {
    case 'guardrail': case 'sources': case 'token': case 'done': case 'error':
      return { type: event, data } as ChatEvent;
    default:
      return null;
  }
}

/**
 * POST /api/chat and read the SSE stream with fetch + ReadableStream
 * (EventSource can't POST). Returns an abort function.
 */
export function streamChat(req: ChatRequest, onEvent: (e: ChatEvent) => void): () => void {
  const controller = new AbortController();

  void (async () => {
    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
        signal: controller.signal,
      });
      if (!res.ok || !res.body) {
        const detail = res.status === 429 ? 'Rate limit: 10 requests per minute. Please wait.' : `Server error ${res.status}`;
        onEvent({ type: 'error', data: { message: detail } });
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let idx: number;
        while ((idx = buffer.indexOf('\n\n')) !== -1) {
          const frame = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          const ev = parseFrame(frame);
          if (ev) onEvent(ev);
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') onEvent({ type: 'error', data: { message: 'Could not reach the backend. Is it running?' } });
    }
  })();

  return () => controller.abort();
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const getChunk = (chunkId: string) => getJson<Chunk>(`/api/chunks/${encodeURIComponent(chunkId)}`);
export const getEvalResults = () => getJson<EvalResults>('/api/eval/results');
