// TRIBE neural risk page

const TRIBE_API_BASE = (typeof window !== 'undefined' && window.SCENETWIN_API)
  || (typeof API_BASE !== 'undefined' ? API_BASE : 'http://127.0.0.1:8000');

function riskColor(score) {
  if (score >= 0.2) return 'var(--bad)';
  if (score >= 0.08) return 'var(--warn)';
  return 'var(--good)';
}

function routeColor(route) {
  if (!route) return 'var(--fg-muted)';
  const r = String(route).toLowerCase();
  if (r.includes('extended') || r.includes('integrated')) return 'var(--bad)';
  if (r.includes('standard')) return 'var(--warn)';
  return 'var(--good)';
}

function routeShort(route) {
  if (!route) return 'unknown';
  const r = String(route).toLowerCase();
  if (r.includes('extended') || r.includes('integrated')) return 'extended AD';
  if (r.includes('standard')) return 'standard AD';
  return 'low pressure';
}

function speechChip(density) {
  if (density === null || density === undefined || Number.isNaN(density)) return null;
  if (density < 0.3) return { label: 'silent', color: 'var(--bad)' };
  if (density > 0.8) return { label: 'talky', color: 'var(--good)' };
  return { label: 'mixed', color: 'var(--fg-muted)' };
}

function bandColor(rec) {
  if (!rec) return 'var(--panel-3)';
  const r = String(rec).toLowerCase();
  if (r.includes('extended') || r.includes('integrated')) return 'var(--bad)';
  if (r.includes('standard')) return 'var(--warn)';
  if (r.includes('inspect')) return 'var(--accent)';
  return 'var(--panel-3)';
}

function ROI_LABELS() {
  return {
    retrosplenial_pos: 'Retrosplenial (scene context)',
    scene_ppa: 'Scene PPA (place area)',
    early_visual_v1: 'Early visual V1',
    higher_visual_v2v3v4: 'Higher visual V2/V3/V4',
    language_control: 'Language control',
    face_ffc: 'Face FFC',
    body_eba_region: 'Body EBA',
    motion_mt_complex: 'Motion MT',
    lateral_object_loc: 'Lateral object',
    auditory_control: 'Auditory control',
  };
}

function NeedCurve({ curve, windows }) {
  if (!curve || curve.length === 0) {
    return <div style={{ color: 'var(--fg-muted)', fontSize: 12 }}>No need curve for this clip.</div>;
  }
  const maxT = Math.max(...curve.map(p => p.end_s || p.start_s || 0), 1);
  const maxNeed = Math.max(1.0, ...curve.map(p => p.need_score || 0));
  const W = 560;
  const H = 130;
  const padL = 28;
  const padR = 8;
  const padT = 8;
  const padB = 22;
  const innerW = W - padL - padR;
  const innerH = H - padT - padB;
  const xOf = (s) => padL + (s / maxT) * innerW;
  const yOf = (v) => padT + innerH - (v / maxNeed) * innerH;
  const pathPts = curve.map(p => `${xOf(p.start_s)},${yOf(p.need_score)}`).join(' ');
  const areaPts = `${xOf(curve[0].start_s)},${padT + innerH} ${pathPts} ${xOf(curve[curve.length - 1].start_s)},${padT + innerH}`;
  const threshold = 0.5;
  return (
    <div>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display: 'block', background: 'var(--panel)' }}>
        {(windows || []).map((w, i) => (
          <rect
            key={i}
            x={xOf(w.start_s)}
            y={padT + innerH + 4}
            width={Math.max(1, xOf(w.end_s) - xOf(w.start_s))}
            height={10}
            fill={bandColor(w.recommendation)}
            opacity="0.85"
          >
            <title>{`${w.start_s.toFixed(1)}-${w.end_s.toFixed(1)}s: ${w.recommendation}`}</title>
          </rect>
        ))}
        <line x1={padL} y1={yOf(threshold)} x2={W - padR} y2={yOf(threshold)}
              stroke="var(--fg-dim)" strokeWidth="1" strokeDasharray="3 3" />
        <polygon points={areaPts} fill="var(--accent)" opacity="0.18" />
        <polyline points={pathPts} fill="none" stroke="var(--accent)" strokeWidth="1.6" />
        {curve.map((p, i) => (
          <circle key={i} cx={xOf(p.start_s)} cy={yOf(p.need_score)} r="2"
                  fill="var(--accent)">
            <title>{`t=${p.start_s.toFixed(1)}s, need=${p.need_score.toFixed(2)}, speech=${p.speech_density.toFixed(2)}`}</title>
          </circle>
        ))}
        <text x={padL - 6} y={yOf(0) + 4} textAnchor="end"
              style={{ fontSize: 9, fill: 'var(--fg-muted)', fontFamily: 'var(--font-mono)' }}>0</text>
        <text x={padL - 6} y={yOf(maxNeed) + 4} textAnchor="end"
              style={{ fontSize: 9, fill: 'var(--fg-muted)', fontFamily: 'var(--font-mono)' }}>{maxNeed.toFixed(1)}</text>
        <text x={W - padR} y={H - 4} textAnchor="end"
              style={{ fontSize: 9, fill: 'var(--fg-muted)', fontFamily: 'var(--font-mono)' }}>
          {maxT.toFixed(1)}s
        </text>
        <text x={padL} y={H - 4} textAnchor="start"
              style={{ fontSize: 9, fill: 'var(--fg-muted)', fontFamily: 'var(--font-mono)' }}>0s</text>
      </svg>
      <div className="row gap-12" style={{ marginTop: 8, flexWrap: 'wrap', fontSize: 11, color: 'var(--fg-muted)' }}>
        <span className="row items-center gap-4"><span style={{ width: 10, height: 10, background: 'var(--bad)', display: 'inline-block' }} /> extended/integrated</span>
        <span className="row items-center gap-4"><span style={{ width: 10, height: 10, background: 'var(--warn)', display: 'inline-block' }} /> standard slot</span>
        <span className="row items-center gap-4"><span style={{ width: 10, height: 10, background: 'var(--accent)', display: 'inline-block' }} /> inspect event</span>
        <span className="row items-center gap-4"><span style={{ width: 10, height: 10, background: 'var(--panel-3)', display: 'inline-block', border: '1px solid var(--border)' }} /> low need</span>
      </div>
    </div>
  );
}

function RoiBars({ rois }) {
  if (!rois || rois.length === 0) {
    return (
      <div style={{ color: 'var(--fg-muted)', fontSize: 12, lineHeight: 1.5 }}>
        Full per-ROI tensors only reconstructed for clips 00 and 01 in the
        current run. Other clips show the aggregate failure forecast above.
      </div>
    );
  }
  const labels = ROI_LABELS();
  const sorted = [...rois].sort((a, b) => b.cos_gap - a.cos_gap);
  const maxGap = Math.max(...sorted.map(r => r.cos_gap), 0.01);
  return (
    <div className="col gap-6">
      {sorted.map(r => {
        const label = labels[r.roi] || r.roi;
        const pct = (r.cos_gap / maxGap) * 100;
        const color = r.cos_gap > 0.5 ? 'var(--bad)'
          : r.cos_gap > 0.2 ? 'var(--warn)'
          : r.cos_gap > 0.05 ? 'var(--accent)'
          : 'var(--fg-muted)';
        return (
          <div key={r.roi} className="row items-center gap-10" style={{ fontSize: 12 }}>
            <div style={{ width: 180, color: 'var(--fg)' }}>{label}</div>
            <div style={{ flex: 1, height: 12, background: 'var(--panel-3)', border: '1px solid var(--border)', position: 'relative' }}>
              <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${Math.max(2, pct)}%`, background: color }} />
            </div>
            <div className="mono" style={{ width: 64, textAlign: 'right', color: 'var(--fg-muted)' }}>
              {r.cos_gap.toFixed(3)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function TribeRiskPage() {
  const [data, setData] = useState(null);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${TRIBE_API_BASE}/api/tribe-risk`)
      .then(r => r.json())
      .then(json => {
        setData(json);
        setSelected(json.clips?.[0] || null);
      })
      .catch(() => setError('TRIBE risk endpoint is not reachable.'));
  }, []);

  const clips = data?.clips || [];
  const highRisk = clips.filter(c => c.target).length;
  const headline = data?.headline_correlation;
  const selectedSpeech = selected ? speechChip(selected.mean_speech_density) : null;

  return (
    <main className="page" style={{ paddingTop: 22, maxWidth: 1680 }}>
      <div className="row justify-between items-end gap-24" style={{ marginBottom: 14 }}>
        <div>
          <div className="eyebrow accent">TRIBE risk</div>
          <h1 style={{ margin: '8px 0 0', fontSize: 36, lineHeight: 1.05, fontWeight: 500 }}>
            Neural forecast over the 18 cached clips
          </h1>
        </div>
        <div className="row gap-8 wrap" style={{ justifyContent: 'flex-end' }}>
          <Tag color="var(--accent)">18 clips</Tag>
          <Tag color="var(--good)">single-screen view</Tag>
        </div>
      </div>

      {error && <div className="card card-pad" style={{ borderColor: 'var(--bad)', color: 'var(--bad)', marginBottom: 12 }}>{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(0, 1fr))', gap: 10, marginBottom: 12 }}>
        <div className="card" style={{ padding: 12 }}><Stat label="Recall@2" value={data ? `${Math.round(data.recall_at_topk * 100)}` : '—'} unit="%" sub="both known failures caught" /></div>
        <div className="card" style={{ padding: 12 }}><Stat label="p value" value={data ? data.p_value.toFixed(4) : '—'} sub="hypergeometric top-k" /></div>
        <div className="card" style={{ padding: 12 }}><Stat label="Risk clips" value={data ? `${highRisk}/${data.n}` : '—'} sub="quality failure targets" /></div>
        <div className="card" style={{ padding: 12 }}><Stat label="Review budget" value={data ? data.review_budget_clips : '—'} sub="clips a human checks first" /></div>
        <div className="card" style={{ padding: 12 }}>
          <Stat
            label="ρ (TRIBE vs judges)"
            value={headline ? headline.rho.toFixed(2) : '—'}
            sub={headline ? `p = ${headline.p.toExponential(1)}, n = ${headline.n}` : 'spearman correlation'}
          />
        </div>
      </div>

      <section style={{
        display: 'grid',
        gridTemplateColumns: '340px minmax(0, 1fr)',
        gap: 14,
        height: 'calc(100vh - 210px)',
        minHeight: 660,
      }}>
        <div className="card" style={{ padding: 14, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          <div className="row justify-between items-center">
            <div className="eyebrow">Risk-ranked clips</div>
            <span className="mono" style={{ color: 'var(--fg-muted)', fontSize: 11 }}>click rows</span>
          </div>
          <div className="col gap-8" style={{ marginTop: 12, overflowY: 'auto', minHeight: 0, paddingRight: 4 }}>
            {clips.map(clip => {
              const route = routeShort(clip.tribe_route);
              const rColor = routeColor(clip.tribe_route);
              const speech = speechChip(clip.mean_speech_density);
              return (
                <button
                  key={clip.clip_idx}
                  className="card"
                  onClick={() => setSelected(clip)}
                  style={{
                    padding: 10,
                    textAlign: 'left',
                    borderColor: selected?.clip_idx === clip.clip_idx ? 'var(--accent)' : 'var(--border)',
                    background: selected?.clip_idx === clip.clip_idx ? 'var(--panel-2)' : 'var(--panel)',
                  }}
                >
                  <div className="row justify-between gap-10">
                    <strong style={{ fontSize: 13 }}>clip_{String(clip.clip_idx).padStart(2, '0')} · {clip.category}</strong>
                    <span className="mono" style={{ color: riskColor(clip.risk_score), fontSize: 12 }}>#{clip.risk_rank}</span>
                  </div>
                  <div className="row items-center gap-6" style={{ marginTop: 7, flexWrap: 'wrap' }}>
                    <span className="mono" style={{
                      fontSize: 9, padding: '2px 5px', border: `1px solid ${rColor}`,
                      color: rColor, textTransform: 'uppercase',
                    }}>{route}</span>
                    {speech && (
                      <span className="mono" style={{
                        fontSize: 9, padding: '2px 5px', border: `1px solid ${speech.color}`,
                        color: speech.color, textTransform: 'uppercase',
                      }}>{speech.label}</span>
                    )}
                  </div>
                  <div className="row items-center gap-8" style={{ marginTop: 8 }}>
                    <ScoreBar value={Math.min(1, clip.risk_score * 4)} width="100%" color={riskColor(clip.risk_score)} />
                    <span className="mono" style={{ color: 'var(--fg-muted)', fontSize: 10 }}>{clip.risk_score.toFixed(3)}</span>
                  </div>
                  <div style={{ marginTop: 6, color: 'var(--fg-muted)', fontSize: 11, lineHeight: 1.35 }}>{clip.quality_risk}</div>
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ minHeight: 0, display: 'grid', gridTemplateRows: 'minmax(300px, 1.1fr) minmax(250px, 0.9fr)', gap: 12 }}>
          <div className="card" style={{ padding: 14, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
            <div className="row justify-between items-start gap-16" style={{ marginBottom: 10 }}>
              <div>
                <div className="eyebrow">Selected clip brain map</div>
                <h2 style={{ margin: '5px 0 0', fontSize: 23, fontWeight: 500 }}>
                  {selected ? `clip_${String(selected.clip_idx).padStart(2, '0')} · ${selected.category}` : 'Where visual description is neurologically needed'}
                </h2>
              </div>
              {selected && (
                <div className="row gap-8 wrap" style={{ justifyContent: 'flex-end' }}>
                  <Tag color={riskColor(selected.risk_score)}>rank #{selected.risk_rank}</Tag>
                  <Tag color={selected.target ? 'var(--bad)' : 'var(--good)'}>{selected.target ? 'review first' : 'lower risk'}</Tag>
                </div>
              )}
            </div>
            <div style={{ minHeight: 0, flex: 1, display: 'flex', alignItems: 'center', background: '#fff', border: '1px solid var(--border)' }}>
              <img
                src={selected?.brain_map_url || '../output/charts/scenetwin_brain_three_panel.png'}
                style={{ width: '100%', maxHeight: '100%', objectFit: 'contain', display: 'block' }}
              />
            </div>
            <div className="row justify-between gap-16" style={{ marginTop: 9, color: 'var(--fg-muted)', fontSize: 11, lineHeight: 1.35 }}>
              <span>Yellow/red = directional visual lift: regions where video adds predicted cortical signal beyond audio alone.</span>
              <span className="mono">max(P_AV-P_A,0)</span>
            </div>
          </div>

          {selected && (
            <div style={{ minHeight: 0, display: 'grid', gridTemplateColumns: '1.1fr 1fr 1fr', gap: 12 }}>
              <div className="card" style={{ padding: 14, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <div className="row justify-between items-baseline">
                  <div className="eyebrow">AD need over time</div>
                  <span className="mono" style={{ color: 'var(--fg-muted)', fontSize: 10 }}>per-TR + 3s windows</span>
                </div>
                <div style={{ marginTop: 10 }}>
                  <NeedCurve curve={selected.need_curve} windows={selected.coarse_windows} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginTop: 10 }}>
                  <div className="card" style={{ padding: 9 }}><Stat label="Risk" value={selected.risk_score.toFixed(3)} /></div>
                  <div className="card" style={{ padding: 9 }}><Stat label="Need" value={selected.mean_need.toFixed(2)} /></div>
                  <div className="card" style={{ padding: 9 }}><Stat label="High need" value={`${Math.round(selected.high_need_seconds_frac * 100)}`} unit="%" /></div>
                </div>
              </div>

              <div className="card" style={{ padding: 14, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <div className="eyebrow">Decision</div>
                <div className="row items-center gap-8" style={{ marginTop: 9, flexWrap: 'wrap' }}>
                  <span className="mono" style={{
                    fontSize: 11, padding: '3px 8px', border: `1px solid ${routeColor(selected.tribe_route)}`,
                    color: routeColor(selected.tribe_route), textTransform: 'uppercase',
                  }}>{routeShort(selected.tribe_route)}</span>
                  {selectedSpeech && (
                    <span className="mono" style={{
                      fontSize: 11, padding: '3px 8px', border: `1px solid ${selectedSpeech.color}`,
                      color: selectedSpeech.color, textTransform: 'uppercase',
                    }}>{selectedSpeech.label}</span>
                  )}
                </div>
                <p style={{ margin: '10px 0 0', color: 'var(--fg-muted)', lineHeight: 1.45, fontSize: 13 }}>
                  {selected.quality_risk}. {selected.tribe_route}.
                </p>
                <div style={{ marginTop: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  <div className="card" style={{ padding: 9 }}><Stat label="Speech" value={selected.mean_speech_density !== null && selected.mean_speech_density !== undefined ? selected.mean_speech_density.toFixed(2) : '—'} /></div>
                  <div className="card" style={{ padding: 9 }}><Stat label="Tier margin" value={selected.tier3_margin.toFixed(2)} /></div>
                </div>
                <div className="eyebrow" style={{ marginTop: 12 }}>Professional AD</div>
                <p style={{ margin: '7px 0 0', color: 'var(--fg-muted)', lineHeight: 1.42, fontSize: 12, overflowY: 'auto', minHeight: 0 }}>
                  {selected.pro_ad_text}
                </p>
              </div>

              <div className="card" style={{ padding: 14, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <div className="row justify-between items-baseline">
                  <div className="eyebrow">Per-ROI gap</div>
                  <span className="mono" style={{ color: 'var(--fg-muted)', fontSize: 10 }}>cosine gap</span>
                </div>
                <p style={{ margin: '7px 0 10px', color: 'var(--fg-muted)', fontSize: 11, lineHeight: 1.35 }}>
                  Brain encoder summary. It supports routing; it is not a literal video attention map.
                </p>
                <div style={{ overflowY: 'auto', minHeight: 0 }}>
                  <RoiBars rois={selected.per_roi} />
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

Object.assign(window, { TribeRiskPage });
