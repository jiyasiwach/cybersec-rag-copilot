import type { GuardrailResult } from '../types';

const TITLE: Record<GuardrailResult['verdict'], string> = {
  injection: 'Blocked by guardrail',
  off_topic: 'Off-topic question',
  safe: 'Allowed',
};

/** Distinct red card with a shield icon for guardrail blocks. */
export default function BlockedMessage({ g }: { g: GuardrailResult }) {
  return (
    <div className="rounded-lg border border-danger/40 bg-danger/10 p-3">
      <div className="flex items-center gap-2 text-danger">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
          <path d="M12 2l8 4v6c0 5-3.5 9-8 10-4.5-1-8-5-8-10V6l8-4z" />
          <path d="M9 12l2 2 4-4" />
        </svg>
        <span className="text-sm font-semibold">{TITLE[g.verdict]}</span>
      </div>
      <p className="mt-1 text-sm text-text/90">
        {g.verdict === 'off_topic'
          ? 'I only answer cybersecurity questions grounded in MITRE ATT&CK, OWASP Top 10 and CISA KEV.'
          : 'This message was not sent to the model.'}
      </p>
      <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 font-mono text-xs text-muted">
        <dt>reason</dt><dd className="text-text/80">{g.reason}</dd>
        <dt>layer</dt><dd>{g.layer ?? '—'}</dd>
        <dt>risk</dt><dd>{g.risk_score.toFixed(2)}</dd>
      </dl>
    </div>
  );
}
