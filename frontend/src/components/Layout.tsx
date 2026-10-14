import { NavLink, Outlet } from 'react-router-dom';

const links = [
  { to: '/', label: 'Chat' },
  { to: '/eval', label: 'Eval' },
  { to: '/architecture', label: 'Architecture' },
];

/** App shell: top bar with brand + nav, page content below. */
export default function Layout() {
  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b border-line bg-panel px-4 py-2.5">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-accent shadow-[0_0_8px_var(--color-accent)]" />
          <span className="font-mono text-sm tracking-wide text-text">cybersec<span className="text-accent">::</span>rag</span>
        </div>
        <nav className="flex gap-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              className={({ isActive }) =>
                `rounded px-3 py-1 text-sm ${isActive ? 'bg-panel-2 text-accent' : 'text-muted hover:text-text'}`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="min-h-0 flex-1">
        <Outlet />
      </main>
    </div>
  );
}
