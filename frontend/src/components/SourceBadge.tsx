import type { Source } from '../types';

const META: Record<Source, { label: string; cls: string }> = {
  mitre: { label: 'MITRE ATT&CK', cls: 'bg-red-500/15 text-red-300 border-red-500/30' },
  owasp: { label: 'OWASP', cls: 'bg-blue-500/15 text-blue-300 border-blue-500/30' },
  cisa_kev: { label: 'CISA KEV', cls: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
};

export default function SourceBadge({ source }: { source: Source }) {
  const m = META[source];
  return <span className={`rounded border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider ${m.cls}`}>{m.label}</span>;
}
