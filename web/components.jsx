// Shared components for SceneTwin

const { useState, useEffect, useRef, useMemo, useCallback } = React;

// ---- Deterministic pseudo-random ----
function mulberry32(seed) {
  return function() {
    let t = (seed += 0x6D2B79F5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---- Top bar / nav ----
function TopBar({ page, setPage }) {
  const links = [
    { id: 'hero', label: 'Overview' },
    { id: 'audit', label: 'Live audit' },
    { id: 'benchmark', label: 'Benchmark' },
    { id: 'tribe', label: 'TRIBE risk', disabled: true },
    { id: 'compare', label: 'Compare', disabled: true },
  ];
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <button className="brand" onClick={() => setPage('hero')}>
          <span className="brand-mark" aria-hidden="true" />
          <span className="brand-name">SceneTwin<span className="sub mono">v0.3</span></span>
        </button>
        <nav className="nav">
          {links.map(l => (
            <button
              key={l.id}
              className={"nav-link " + (page === l.id ? 'active' : '')}
              onClick={() => !l.disabled && setPage(l.id)}
              style={l.disabled ? { opacity: 0.45, cursor: 'not-allowed' } : null}
            >
              {l.label}
              {l.disabled && <span className="mono" style={{ marginLeft: 6, fontSize: 10, color: 'var(--fg-dim)' }}>soon</span>}
            </button>
          ))}
        </nav>
        <div className="topbar-right">
          <span className="pill">arXiv:2509.14211</span>
          <a className="mono" href="../output/scenetwin_njbda_poster.pdf" target="_blank">poster</a>
          <a className="mono" href="https://github.com/Adarsha-gg/scenetwin" target="_blank">github</a>
          <button className="icon-btn" title="Toggle theme" onClick={() => document.documentElement.classList.toggle('light')}>
            <ThemeIcon />
          </button>
        </div>
      </div>
    </header>
  );
}

function ThemeIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4">
      <circle cx="8" cy="8" r="3" />
      <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.4 1.4M11.6 11.6L13 13M3 13l1.4-1.4M11.6 4.4L13 3" />
    </svg>
  );
}

// ---- Footer ----
function Footer() {
  return (
    <footer className="footer">
      <div className="page">
        <div>
          <div className="brand" style={{ marginBottom: 12 }}>
            <span className="brand-mark" aria-hidden="true" />
            <span className="brand-name">SceneTwin</span>
          </div>
          <p style={{ margin: 0, maxWidth: 380, lineHeight: 1.55 }}>
            Reference-free audit framework for audio descriptions. Scores AD scripts against the visual content of a clip, without any human-written reference track.
          </p>
        </div>
        <div>
          <h5>Research</h5>
          <ul>
            <li><a>Paper (arXiv)</a></li>
            <li><a>Benchmark v1</a></li>
            <li><a>TRIBE forecaster</a></li>
            <li><a>Citation</a></li>
          </ul>
        </div>
        <div>
          <h5>Product</h5>
          <ul>
            <li><a>Live audit</a></li>
            <li><a>Gallery</a></li>
            <li><a>API (beta)</a></li>
            <li><a>Pricing</a></li>
          </ul>
        </div>
        <div>
          <h5>Community</h5>
          <ul>
            <li><a>NJBDA 2026</a></li>
            <li><a>Newsletter</a></li>
            <li><a>Contact</a></li>
            <li><a>License — MIT</a></li>
          </ul>
        </div>
      </div>
    </footer>
  );
}

// ---- Striped video frame placeholder ----
function VideoFrame({ width = 160, height = 90, label, seed = 1, active = false, score, dim = false, children, style }) {
  // Striped placeholder with a label
  const rand = useMemo(() => mulberry32(seed), [seed]);
  const stripeAngle = useMemo(() => 18 + Math.floor(rand() * 30), [rand]);
  const id = `s${seed}-${width}-${height}`;
  return (
    <div
      style={{
        position: 'relative',
        width: width === '100%' ? '100%' : width,
        aspectRatio: `${typeof width === 'number' ? width : 16} / ${typeof width === 'number' ? height : 9}`,
        border: '1px solid var(--border)',
        background: 'var(--panel-2)',
        overflow: 'hidden',
        outline: active ? '1px solid var(--accent)' : 'none',
        outlineOffset: '-2px',
        opacity: dim ? 0.35 : 1,
        ...(style || {}),
      }}
    >
      <svg width="100%" height="100%" style={{ display: 'block', position: 'absolute', inset: 0 }} preserveAspectRatio="none">
        <defs>
          <pattern id={id} width="14" height="14" patternUnits="userSpaceOnUse" patternTransform={`rotate(${stripeAngle})`}>
            <rect width="14" height="14" fill="var(--panel-2)" />
            <line x1="0" y1="0" x2="0" y2="14" stroke="var(--border)" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill={`url(#${id})`} />
      </svg>
      {label && (
        <div style={{
          position: 'absolute', left: 6, bottom: 6,
          fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--fg-muted)',
          background: 'var(--panel)', border: '1px solid var(--border)',
          padding: '1px 5px',
        }}>{label}</div>
      )}
      {score !== undefined && (
        <div style={{
          position: 'absolute', right: 6, top: 6,
          fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--fg)',
          background: 'var(--panel)', border: '1px solid var(--border)',
          padding: '1px 5px',
        }}>{score.toFixed(2)}</div>
      )}
      {children}
    </div>
  );
}

// ---- Sparkline / score bar ----
function ScoreBar({ value, width = 80, height = 6, color, tickAt }) {
  const w = typeof width === 'number' ? width : 100;
  return (
    <div style={{
      width: typeof width === 'number' ? `${width}px` : width,
      height,
      background: 'var(--panel-3)',
      border: '1px solid var(--border)',
      position: 'relative',
    }}>
      <div style={{
        position: 'absolute', left: 0, top: 0, bottom: 0,
        width: `${Math.max(0, Math.min(1, value)) * 100}%`,
        background: color || 'var(--accent)',
      }} />
      {tickAt !== undefined && (
        <div style={{
          position: 'absolute', left: `${tickAt * 100}%`, top: -2, bottom: -2,
          width: 1, background: 'var(--fg-dim)',
        }} />
      )}
    </div>
  );
}

// ---- Heatmap cell (frame × span grid) ----
function HeatCell({ v, size = 22 }) {
  // 0..1 → color step. We use solid colors not rgba.
  const steps = [
    'var(--panel-2)',
    '#1f2330',
    '#262e44',
    '#2f3a5d',
    '#3b4a78',
    '#506299',
    '#6c7fbf',
    '#8b9cda',
    '#aab7e6',
  ];
  // Light mode: a different ramp
  const light = [
    '#f1f0eb', '#e3e6f0', '#cfd5e8', '#b8c1de', '#9aa5cf', '#7c8bbf', '#5e6fa8', '#42548a', '#2a3766',
  ];
  const idx = Math.max(0, Math.min(8, Math.round(v * 8)));
  // We'll pick via CSS variable trick? Use accent-tinted via direct color.
  // We'll just use the dark ramp and let the CSS class adjust if needed.
  const isLight = typeof document !== 'undefined' && document.documentElement.classList.contains('light');
  const c = (isLight ? light : steps)[idx];
  return <div style={{ width: size, height: size, background: c, border: '1px solid var(--border)' }} title={v.toFixed(2)} />;
}

// ---- Tier badge ----
function TierBadge({ tier }) {
  const map = {
    neg: { label: 'cross-neg', color: 'var(--bad)' },
    short: { label: 'short cap', color: 'var(--warn)' },
    long: { label: 'long cap', color: 'var(--fg-muted)' },
    pro: { label: 'pro AD', color: 'var(--good)' },
  };
  const t = map[tier];
  return (
    <span className="mono" style={{
      fontSize: 10, color: t.color, borderLeft: `2px solid ${t.color}`,
      paddingLeft: 6, textTransform: 'uppercase', letterSpacing: '0.05em',
    }}>{t.label}</span>
  );
}

// ---- Numeric label / data point ----
function Stat({ label, value, unit, sub }) {
  return (
    <div className="col gap-4">
      <div className="eyebrow">{label}</div>
      <div className="mono" style={{ fontSize: 28, fontWeight: 500, letterSpacing: '-0.02em' }}>
        {value}{unit && <span style={{ color: 'var(--fg-muted)', marginLeft: 4 }}>{unit}</span>}
      </div>
      {sub && <div style={{ fontSize: 12, color: 'var(--fg-muted)' }}>{sub}</div>}
    </div>
  );
}

// ---- Section header ----
function SectionHead({ eyebrow, title, sub, right }) {
  return (
    <div className="row items-end justify-between gap-24" style={{ marginBottom: 24 }}>
      <div className="col gap-8" style={{ maxWidth: 720 }}>
        {eyebrow && <div className="eyebrow accent">{eyebrow}</div>}
        <h2 style={{ margin: 0, fontSize: 28, fontWeight: 500, letterSpacing: '-0.02em', lineHeight: 1.15 }}>{title}</h2>
        {sub && <p style={{ margin: 0, color: 'var(--fg-muted)', fontSize: 14, lineHeight: 1.55 }}>{sub}</p>}
      </div>
      {right}
    </div>
  );
}

// ---- Code-style tag ----
function Tag({ children, color }) {
  return (
    <span className="mono" style={{
      fontSize: 11, padding: '2px 6px', border: '1px solid var(--border-strong)',
      color: color || 'var(--fg-muted)',
    }}>{children}</span>
  );
}

// ---- Theme color step (gives a CSS color for given accent) ----
const ACCENT_OPTIONS = [
  { name: 'indigo', value: '#8b8cff', ink: '#0a0b0d' },
  { name: 'amber',  value: '#e6b34a', ink: '#0a0b0d' },
  { name: 'lime',   value: '#a8d96f', ink: '#0a0b0d' },
  { name: 'coral',  value: '#f08572', ink: '#0a0b0d' },
];

Object.assign(window, {
  mulberry32, TopBar, Footer, VideoFrame, ScoreBar, HeatCell, TierBadge,
  Stat, SectionHead, Tag, ACCENT_OPTIONS,
});
