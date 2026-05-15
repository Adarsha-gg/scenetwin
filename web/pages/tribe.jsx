// TRIBE neural risk page

function riskColor(score) {
  if (score >= 0.2) return 'var(--bad)';
  if (score >= 0.08) return 'var(--warn)';
  return 'var(--good)';
}

function TribeRiskPage() {
  const [data, setData] = useState(null);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API_BASE}/api/tribe-risk`)
      .then(r => r.json())
      .then(json => {
        setData(json);
        setSelected(json.clips?.[0] || null);
      })
      .catch(() => setError('TRIBE risk endpoint is not reachable.'));
  }, []);

  const clips = data?.clips || [];
  const highRisk = clips.filter(c => c.target).length;

  return (
    <main className="page" style={{ paddingTop: 40 }}>
      <SectionHead
        eyebrow="TRIBE risk"
        title="Neural forecast over the 18 cached clips"
        sub="TRIBE is not the live YouTube grader. It is the fMRI-backed sidecar: it predicts where visual information is neurologically needed, then flags clips where caption-style AD is likely to fail."
        right={<Tag color="var(--accent)">18 clips</Tag>}
      />

      {error && <div className="card card-pad" style={{ borderColor: 'var(--bad)', color: 'var(--bad)' }}>{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 12 }}>
        <div className="card card-pad"><Stat label="Recall@2" value={data ? `${Math.round(data.recall_at_topk * 100)}` : '—'} unit="%" sub="both known failures caught" /></div>
        <div className="card card-pad"><Stat label="p value" value={data ? data.p_value.toFixed(4) : '—'} sub="hypergeometric top-k" /></div>
        <div className="card card-pad"><Stat label="Risk clips" value={data ? `${highRisk}/${data.n}` : '—'} sub="quality failure targets" /></div>
        <div className="card card-pad"><Stat label="Review budget" value={data ? data.review_budget_clips : '—'} sub="clips a human checks first" /></div>
      </div>

      <section style={{ marginTop: 20, display: 'grid', gridTemplateColumns: 'minmax(0, 1.1fr) minmax(360px, 0.9fr)', gap: 18 }}>
        <div className="card" style={{ padding: 18 }}>
          <div className="row justify-between items-center" style={{ marginBottom: 14 }}>
            <div>
              <div className="eyebrow">Selected clip brain map</div>
              <h2 style={{ margin: '6px 0 0', fontSize: 23, fontWeight: 500 }}>
                {selected ? `clip_${String(selected.clip_idx).padStart(2, '0')} · ${selected.category}` : 'Where visual description is neurologically needed'}
              </h2>
            </div>
            <Tag color={selected ? riskColor(selected.risk_score) : 'var(--good)'}>{selected ? `rank #${selected.risk_rank}` : 'TRIBE'}</Tag>
          </div>
          <img
            src={selected?.brain_map_url || '../output/charts/scenetwin_brain_three_panel.png'}
            style={{ width: '100%', display: 'block', border: '1px solid var(--border)', background: '#fff' }}
          />
          <div className="row justify-between gap-16" style={{ marginTop: 12, color: 'var(--fg-muted)', fontSize: 12, lineHeight: 1.45 }}>
            <span>Each cached benchmark clip has its own TRIBE surface panel.</span>
            <span className="mono">P_AV / P_A / |gap|</span>
          </div>
        </div>

        <div className="card" style={{ padding: 18 }}>
          <div className="row justify-between items-center">
            <div className="eyebrow">Risk-ranked clips</div>
            <span className="mono" style={{ color: 'var(--fg-muted)', fontSize: 11 }}>click rows</span>
          </div>
          <div className="col gap-8" style={{ marginTop: 14, maxHeight: 610, overflowY: 'auto', paddingRight: 4 }}>
            {clips.map(clip => (
              <button
                key={clip.clip_idx}
                className="card"
                onClick={() => setSelected(clip)}
                style={{
                  padding: 12,
                  textAlign: 'left',
                  borderColor: selected?.clip_idx === clip.clip_idx ? 'var(--accent)' : 'var(--border)',
                  background: selected?.clip_idx === clip.clip_idx ? 'var(--panel-2)' : 'var(--panel)',
                }}
              >
                <div className="row justify-between gap-12">
                  <strong>clip_{String(clip.clip_idx).padStart(2, '0')} · {clip.category}</strong>
                  <span className="mono" style={{ color: riskColor(clip.risk_score) }}>#{clip.risk_rank}</span>
                </div>
                <div className="row items-center gap-10" style={{ marginTop: 10 }}>
                  <ScoreBar value={Math.min(1, clip.risk_score * 4)} width="100%" color={riskColor(clip.risk_score)} />
                  <span className="mono" style={{ color: 'var(--fg-muted)', fontSize: 11 }}>{clip.risk_score.toFixed(3)}</span>
                </div>
                <div style={{ marginTop: 8, color: 'var(--fg-muted)', fontSize: 12 }}>{clip.quality_risk}</div>
                <div className="mono" style={{ marginTop: 8, color: 'var(--fg-muted)', fontSize: 10 }}>brain map ready</div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {selected && (
        <section className="card card-pad" style={{ marginTop: 18 }}>
          <div className="row justify-between gap-24">
            <div>
              <div className="eyebrow">Selected clip</div>
              <h2 style={{ margin: '6px 0 0', fontSize: 24, fontWeight: 500 }}>
                clip_{String(selected.clip_idx).padStart(2, '0')} · {selected.category}
              </h2>
            </div>
            <Tag color={riskColor(selected.risk_score)}>{selected.target ? 'review first' : 'lower risk'}</Tag>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 12, marginTop: 18 }}>
            <div className="card card-pad"><Stat label="Risk score" value={selected.risk_score.toFixed(3)} /></div>
            <div className="card card-pad"><Stat label="Need" value={selected.mean_need.toFixed(2)} /></div>
            <div className="card card-pad"><Stat label="High-need sec" value={`${Math.round(selected.high_need_seconds_frac * 100)}`} unit="%" /></div>
            <div className="card card-pad"><Stat label="Tier margin" value={selected.tier3_margin.toFixed(2)} /></div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginTop: 16 }}>
            <div className="card card-pad">
              <div className="eyebrow">TRIBE route</div>
              <p style={{ margin: '8px 0 0', lineHeight: 1.5 }}>{selected.tribe_route}</p>
              <p style={{ margin: '10px 0 0', color: 'var(--fg-muted)', lineHeight: 1.5 }}>{selected.quality_risk}</p>
            </div>
            <div className="card card-pad">
              <div className="eyebrow">Professional AD candidate</div>
              <p style={{ margin: '8px 0 0', color: 'var(--fg-muted)', lineHeight: 1.5 }}>{selected.pro_ad_text}</p>
            </div>
          </div>
        </section>
      )}
    </main>
  );
}

Object.assign(window, { TribeRiskPage });
