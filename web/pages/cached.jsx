// Cached benchmark clips page

const CACHED_API_BASE = (typeof window !== 'undefined' && window.SCENETWIN_API)
  || (typeof API_BASE !== 'undefined' ? API_BASE : 'http://127.0.0.1:8000');

function tierTone(tier) {
  if (tier === 'tier3_va11y') return 'var(--good)';
  if (tier === 'tier2_vatex_long') return 'var(--accent)';
  if (tier === 'tier1_vatex_short') return 'var(--warn)';
  return 'var(--bad)';
}

function scorePct(v) {
  return `${Math.round((Number(v) || 0) * 100)}`;
}

function CachedClipsPage() {
  const [data, setData] = useState(null);
  const [selected, setSelected] = useState(null);
  const [tier, setTier] = useState('tier3_va11y');
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${CACHED_API_BASE}/api/cached-clips`)
      .then(r => r.json())
      .then(json => {
        setData(json);
        setSelected(json.clips?.[0] || null);
      })
      .catch(() => setError('Cached clip endpoint is not reachable.'));
  }, []);

  const clips = data?.clips || [];
  const cand = selected?.candidates?.find(c => c.tier === tier) || selected?.candidates?.[0];

  return (
    <main className="page" style={{ paddingTop: 22, maxWidth: 1680 }}>
      <div className="row justify-between items-end gap-24" style={{ marginBottom: 14 }}>
        <div>
          <div className="eyebrow accent">Cached benchmark clips</div>
          <h1 style={{ margin: '8px 0 0', fontSize: 36, lineHeight: 1.05, fontWeight: 500 }}>
            Inspect the VATEX-style candidate set
          </h1>
        </div>
        <div className="row gap-8 wrap" style={{ justifyContent: 'flex-end' }}>
          <Tag color="var(--accent)">{data ? `${data.n} clips` : 'loading'}</Tag>
          <Tag color="var(--good)">no live API run</Tag>
        </div>
      </div>

      {error && <div className="card card-pad" style={{ borderColor: 'var(--bad)', color: 'var(--bad)', marginBottom: 12 }}>{error}</div>}

      <section style={{
        display: 'grid',
        gridTemplateColumns: '330px minmax(0, 1fr)',
        gap: 14,
        height: 'calc(100vh - 142px)',
        minHeight: 680,
      }}>
        <div className="card" style={{ padding: 14, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          <div className="row justify-between items-center">
            <div className="eyebrow">Training / eval clips</div>
            <span className="mono" style={{ color: 'var(--fg-muted)', fontSize: 11 }}>click rows</span>
          </div>
          <div className="col gap-8" style={{ marginTop: 12, overflowY: 'auto', minHeight: 0, paddingRight: 4 }}>
            {clips.map(clip => (
              <button
                key={clip.clip_idx}
                className="card"
                onClick={() => {
                  setSelected(clip);
                  setTier('tier3_va11y');
                }}
                style={{
                  padding: 10,
                  textAlign: 'left',
                  borderColor: selected?.clip_idx === clip.clip_idx ? 'var(--accent)' : 'var(--border)',
                  background: selected?.clip_idx === clip.clip_idx ? 'var(--panel-2)' : 'var(--panel)',
                }}
              >
                <div className="row justify-between gap-10">
                  <strong style={{ fontSize: 13 }}>clip_{String(clip.clip_idx).padStart(2, '0')} · {clip.category}</strong>
                  <span className="mono" style={{ color: 'var(--fg-muted)', fontSize: 11 }}>{clip.duration_s.toFixed(1)}s</span>
                </div>
                <div style={{ marginTop: 8, color: 'var(--fg-muted)', fontSize: 11, lineHeight: 1.35 }}>
                  {clip.video_id}
                </div>
                <div className="row items-center gap-8" style={{ marginTop: 8 }}>
                  <ScoreBar value={Math.min(1, clip.risk_score * 4)} width="100%" color={clip.risk_score > 0.2 ? 'var(--bad)' : clip.risk_score > 0.08 ? 'var(--warn)' : 'var(--good)'} />
                  <span className="mono" style={{ color: 'var(--fg-muted)', fontSize: 10 }}>{clip.risk_score.toFixed(3)}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {selected && cand && (
          <div style={{ minHeight: 0, display: 'grid', gridTemplateRows: 'minmax(300px, 1fr) minmax(300px, 0.95fr)', gap: 12 }}>
            <div style={{ minHeight: 0, display: 'grid', gridTemplateColumns: 'minmax(0, 1.05fr) minmax(360px, 0.95fr)', gap: 12 }}>
              <div className="card" style={{ padding: 14, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <div className="row justify-between items-start gap-16" style={{ marginBottom: 10 }}>
                  <div>
                    <div className="eyebrow">Clip preview</div>
                    <h2 style={{ margin: '5px 0 0', fontSize: 23, fontWeight: 500 }}>
                      clip_{String(selected.clip_idx).padStart(2, '0')} · {selected.category}
                    </h2>
                  </div>
                  <Tag color="var(--accent)">cached</Tag>
                </div>
                <div style={{ minHeight: 0, flex: 1, border: '1px solid var(--border)', background: 'var(--panel-2)', display: 'grid', placeItems: 'center' }}>
                  {selected.video_url ? (
                    <video src={selected.video_url} controls muted style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                  ) : (
                    <div className="mono" style={{ color: 'var(--fg-muted)' }}>no local video</div>
                  )}
                </div>
              </div>

              <div className="card" style={{ padding: 14, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <div className="row justify-between items-center">
                  <div className="eyebrow">Sample frames</div>
                  <span className="mono" style={{ color: 'var(--fg-muted)', fontSize: 11 }}>{selected.frames.length} cached</span>
                </div>
                <div style={{
                  marginTop: 10,
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
                  gap: 8,
                  overflowY: 'auto',
                  minHeight: 0,
                }}>
                  {selected.frames.map((f, i) => (
                    <div key={`${f.url}-${i}`} style={{ position: 'relative', border: '1px solid var(--border)', background: 'var(--panel-2)' }}>
                      <img src={f.url} style={{ width: '100%', aspectRatio: '16 / 9', objectFit: 'cover', display: 'block' }} />
                      <div className="mono" style={{ position: 'absolute', left: 6, bottom: 6, fontSize: 9, background: 'var(--panel)', border: '1px solid var(--border)', padding: '1px 4px' }}>{f.name.split('_t').pop()?.replace('.jpg', 's')}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ minHeight: 0, display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 420px', gap: 12 }}>
              <div className="card" style={{ padding: 14, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <div className="row justify-between items-center gap-12">
                  <div>
                    <div className="eyebrow">Candidate AD</div>
                    <h2 style={{ margin: '5px 0 0', fontSize: 22, fontWeight: 500 }}>{cand.label}</h2>
                  </div>
                  <div className="row gap-8 wrap" style={{ justifyContent: 'flex-end' }}>
                    {selected.candidates.map(c => (
                      <button
                        key={c.tier}
                        className="btn sm"
                        onClick={() => setTier(c.tier)}
                        style={{
                          borderColor: c.tier === tier ? tierTone(c.tier) : 'var(--border-strong)',
                          color: c.tier === tier ? tierTone(c.tier) : 'var(--fg)',
                        }}
                      >
                        {c.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(0, 1fr))', gap: 8, marginTop: 12 }}>
                  <div className="card" style={{ padding: 10 }}><Stat label="GT tier" value={cand.gt} /></div>
                  <div className="card" style={{ padding: 10 }}><Stat label="Words" value={cand.word_count} /></div>
                  <div className="card" style={{ padding: 10 }}><Stat label="CLIP top3" value={cand.clip_top3.toFixed(2)} /></div>
                  <div className="card" style={{ padding: 10 }}><Stat label="ADQA" value={cand.adqa_score.toFixed(2)} /></div>
                  <div className="card" style={{ padding: 10 }}><Stat label="Yes" value={scorePct(cand.adqa_yes_rate)} unit="%" /></div>
                </div>

                <div className="card" style={{ marginTop: 12, padding: 14, overflowY: 'auto', minHeight: 0, flex: 1, borderLeft: `3px solid ${tierTone(cand.tier)}` }}>
                  <div className="eyebrow">{cand.kind}</div>
                  <p style={{ margin: '8px 0 0', fontSize: 17, lineHeight: 1.55 }}>{cand.text || 'No candidate text cached.'}</p>
                </div>
              </div>

              <div className="card" style={{ padding: 14, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <div className="row justify-between items-baseline">
                  <div className="eyebrow">ADQA questions</div>
                  <span className="mono" style={{ color: 'var(--fg-muted)', fontSize: 11 }}>{cand.grades.length} graded</span>
                </div>
                <div className="col gap-8" style={{ marginTop: 10, overflowY: 'auto', minHeight: 0 }}>
                  {cand.grades.map(g => (
                    <div key={g.q_idx} className="card" style={{ padding: 10, borderLeft: `3px solid ${g.score > 0 ? 'var(--good)' : 'var(--bad)'}` }}>
                      <div className="row justify-between gap-10">
                        <strong style={{ fontSize: 12, lineHeight: 1.35 }}>Q{g.q_idx + 1}. {g.question}</strong>
                        <span className="mono" style={{ color: g.score > 0 ? 'var(--good)' : 'var(--bad)', fontSize: 11 }}>{g.label || g.score}</span>
                      </div>
                      <div style={{ color: 'var(--fg-muted)', fontSize: 11, lineHeight: 1.35, marginTop: 7 }}>
                        Need: {g.required_visual_evidence}
                      </div>
                      {g.grade_rationale && (
                        <div style={{ color: 'var(--fg-muted)', fontSize: 11, lineHeight: 1.35, marginTop: 7 }}>
                          {g.grade_rationale}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}

Object.assign(window, { CachedClipsPage });
