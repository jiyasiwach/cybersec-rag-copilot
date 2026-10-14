import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';

interface Props {
  text: string;
  citationCount: number;
  streaming: boolean;
  onCite: (n: number) => void;
}

/**
 * Renders the answer as markdown and turns [n] citation markers into clickable chips.
 * Trick: rewrite `[n]` to a markdown link `[n](#cite-n)` before parsing, then render
 * those links as buttons. Only numbers that exist in the sources list become chips.
 */
export default function AnswerMarkdown({ text, citationCount, streaming, onCite }: Props) {
  const withLinks = text.replace(/\[(\d{1,2})\]/g, (m, n: string) =>
    Number(n) >= 1 && Number(n) <= citationCount ? `[${n}](#cite-${n})` : m,
  );

  const components: Components = {
    a: ({ href, children }) => {
      const match = href?.match(/^#cite-(\d+)$/);
      if (!match) return <a href={href} target="_blank" rel="noreferrer" className="text-accent underline">{children}</a>;
      const n = Number(match[1]);
      return (
        <button
          type="button"
          onClick={() => onCite(n)}
          className="mx-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded bg-accent-dim/40 px-1 align-text-top font-mono text-[10px] text-accent hover:bg-accent/30"
          aria-label={`Open source ${n}`}
        >
          {n}
        </button>
      );
    },
  };

  return (
    <div className={`answer text-sm leading-relaxed ${streaming ? 'caret' : ''}`}>
      <ReactMarkdown components={components}>{withLinks}</ReactMarkdown>
    </div>
  );
}
