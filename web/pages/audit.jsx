// SceneTwin live audit page

const API_BASE = window.SCENETWIN_API || 'http://127.0.0.1:8000';

function absoluteMediaUrl(path) {
  if (!path) return '';
  if (/^https?:\/\//.test(path)) return path;
  return `${API_BASE}${path}`;
}

function stageLabel(name) {
  const labels = {
    download: 'Download',
    frames: 'Frames',
    ad_generation: 'AD',
    clip: 'CLIP',
    adqa: 'ADQA',
    tribe: 'TRIBE',
  };
  return labels[name] || name;
}

function verdictFor(result) {
  if (!result?.ok) return { label: 'Needs attention', color: 'var(--bad)' };
  const clip = result.clip?.top3 || 0;
  const adqa = result.adqa?.score || 0;
  if (adqa >= 1 && clip >= 0.3) return { label: 'Strong visual match', color: 'var(--good)' };
  if (adqa >= 0.67) return { label: 'Mostly covered', color: 'var(--warn)' };
  return { label: 'Likely misses visual content', color: 'var(--bad)' };
}

function adqaLabel(score) {
  if (score === null || score === undefined) return 'ADQA —';
  return `ADQA ${Math.round(score * 3)}/3`;
}

function clipLabel(score) {
  if (score === null || score === undefined) return 'CLIP —';
  return `CLIP ${score.toFixed(3)}`;
}

function groupPresets(presets) {
  const groups = [];
  for (const preset of presets) {
    const name = preset.group || 'Tested presets';
    let group = groups.find(g => g.name === name);
    if (!group) {
      group = { name, items: [] };
      groups.push(group);
    }
    group.items.push(preset);
  }
  return groups;
}

function idleStages(names) {
  return names.map(name => ({ name, ok: null, message: 'pending' }));
}

function parseStartSeconds(raw) {
  if (!raw) return 0;
  const text = String(raw).trim().toLowerCase();
  if (/^\d+$/.test(text)) return Number(text);
  const h = Number((text.match(/(\d+(?:\.\d+)?)h/) || [0, 0])[1]);
  const m = Number((text.match(/(\d+(?:\.\d+)?)m/) || [0, 0])[1]);
  const s = Number((text.match(/(\d+(?:\.\d+)?)s/) || [0, 0])[1]);
  return Math.round(h * 3600 + m * 60 + s);
}

function youtubePreview(url) {
  try {
    const parsed = new URL(url);
    let id = '';
    if (parsed.hostname.includes('youtu.be')) id = parsed.pathname.replace('/', '');
    else id = parsed.searchParams.get('v') || '';
    if (!id) return null;
    const start = parseStartSeconds(parsed.searchParams.get('t') || parsed.searchParams.get('start'));
    return {
      id,
      start,
      embedUrl: `https://www.youtube.com/embed/${id}?start=${start}`,
      label: start ? `${start}s` : 't=0',
    };
  } catch (e) {
    return null;
  }
}

function AuditPage() {
  const [presets, setPresets] = useState([]);
  const [url, setUrl] = useState('https://www.youtube.com/watch?v=avz06PDqDbM');
  const [selectedPreset, setSelectedPreset] = useState(null);
  const [ad, setAd] = useState('');
  const [running, setRunning] = useState(false);
  const [phase, setPhase] = useState(0);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/presets`)
      .then(r => r.json())
      .then(items => {
        setPresets(items);
        if (items?.[0]?.url) {
          setUrl(items[0].url);
          setSelectedPreset(items[0]);
        }
      })
      .catch(() => setError('API is not reachable on port 8000.'));
  }, []);

  useEffect(() => {
    if (!running) return undefined;
    const id = setInterval(() => setPhase(p => Math.min(p + 1, 4)), 1800);
    return () => clearInterval(id);
  }, [running]);

  const presetGroups = useMemo(() => groupPresets(presets), [presets]);
  const preview = useMemo(() => youtubePreview(url), [url]);

  function selectPreset(preset) {
    setSelectedPreset(preset);
    setUrl(preset.url);
    setResult(null);
    setError('');
  }

  async function runAudit(nextUrl = url) {
    if (!nextUrl || running) return;
    setUrl(nextUrl);
    setRunning(true);
    setError('');
    setResult(null);
    setPhase(0);
    try {
      const response = await fetch(`${API_BASE}/api/audit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: nextUrl,
          candidate_ad: ad.trim() || null,
          run_tribe: false,
          max_seconds: 30,
          frame_count: 8,
        }),
      });
      const json = await response.json();
      if (!response.ok || !json.ok) throw new Error(json.error || `Audit failed (${response.status})`);
      setResult(json);
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setRunning(false);
      setPhase(5);
    }
  }

  const verdict = verdictFor(result);
  const previewStages = ['Download', 'Sample frames', 'Generate AD', 'CLIP', 'ADQA'];

  return (
    <main className="page" style={{ paddingTop: 28 }}>
      <section style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(360px, 420px) minmax(0, 1fr)',
        gap: 24,
        alignItems: 'start',
      }}>
        <aside className="card" style={{ padding: 18, position: 'sticky', top: 72 }}>
          <div className="row justify-between items-center">
            <div>
              <div className="eyebrow accent">Live YouTube</div>
              <h1 style={{ margin: '8px 0 0', fontSize: 30, fontWeight: 500, letterSpacing: 0 }}>Audit a clip</h1>
            </div>
            <Tag color="var(--good)">FastAPI</Tag>
          </div>

          <div className="col gap-12" style={{ marginTop: 22 }}>
            <label className="col gap-6">
              <span className="eyebrow">YouTube URL</span>
              <input
                value={url}
                onChange={e => {
                  setUrl(e.target.value);
                  setSelectedPreset(null);
                  setResult(null);
                }}
                className="mono"
                style={{
                  height: 42,
                  padding: '0 12px',
                  background: 'var(--panel-2)',
                  border: '1px solid var(--border-strong)',
                  outline: 'none',
                  fontSize: 12,
                }}
              />
            </label>

            <button
              className="btn primary lg"
              onClick={() => runAudit(url)}
              disabled={running}
              style={{ justifyContent: 'center', opacity: running ? 0.75 : 1 }}
            >
              {running ? 'Running audit' : 'Run selected clip'}
            </button>

            <div className="col gap-8">
              <div className="row justify-between items-center">
                <div className="eyebrow">Tested presets</div>
                <div className="mono" style={{ fontSize: 11, color: 'var(--fg-muted)' }}>click to preview</div>
              </div>
              <div className="col gap-12" style={{ maxHeight: 360, overflowY: 'auto', paddingRight: 4 }}>
                {presetGroups.map(group => (
                  <div key={group.name} className="col gap-6">
                    <div className="mono" style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      {group.name}
                    </div>
                    {group.items.map(p => (
                      <button
                        key={p.url}
                        className="btn"
                        style={{
                          justifyContent: 'space-between',
                          alignItems: 'stretch',
                          height: 'auto',
                          minHeight: 48,
                          padding: '8px 10px',
                          borderColor: url === p.url ? 'var(--accent)' : 'var(--border-strong)',
                        }}
                        onClick={() => selectPreset(p)}
                      >
                        <span className="col gap-4" style={{ textAlign: 'left', minWidth: 0 }}>
                          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 245 }}>{p.label}</span>
                          <span className="mono" style={{ color: 'var(--fg-muted)', fontSize: 11 }}>
                            {clipLabel(p.clip_top3)} · {adqaLabel(p.adqa_score)}
                          </span>
                        </span>
                        <span className="mono" style={{ color: 'var(--fg-muted)', alignSelf: 'center', marginLeft: 10, whiteSpace: 'nowrap' }}>
                          {p.start_label || 't=0'}
                        </span>
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            </div>

            <label className="col gap-6">
              <span className="eyebrow">Candidate AD</span>
              <textarea
                value={ad}
                onChange={e => setAd(e.target.value)}
                placeholder="Leave blank to generate one."
                rows={4}
                style={{
                  resize: 'vertical',
                  padding: 12,
                  background: 'var(--panel-2)',
                  border: '1px solid var(--border-strong)',
                  outline: 'none',
                  lineHeight: 1.45,
                }}
              />
            </label>

            {error && <div className="card card-pad" style={{ borderColor: 'var(--bad)', color: 'var(--bad)' }}>{error}</div>}
          </div>
        </aside>

        <section className="col gap-16">
          <div className="card" style={{ padding: 18 }}>
            <div className="row justify-between items-center">
              <div>
                <div className="eyebrow">Pipeline</div>
                <div style={{ fontSize: 18, fontWeight: 600, marginTop: 4 }}>{result ? verdict.label : running ? previewStages[phase] || 'Scoring' : 'Choose a preset or paste a URL'}</div>
              </div>
              <div className="mono" style={{ color: result ? verdict.color : 'var(--fg-muted)' }}>
                {result ? `CLIP ${result.clip.top3.toFixed(3)} / ADQA ${Math.round(result.adqa.score * 3)}/3` : '30s / 8 frames'}
              </div>
            </div>
            <div className="row gap-8 wrap" style={{ marginTop: 16 }}>
              {(result?.stages || (running
                ? previewStages.map((s, i) => ({
                    name: s,
                    ok: i < phase ? true : null,
                    message: i === phase ? 'running' : i < phase ? 'ok' : 'pending',
                  }))
                : idleStages(previewStages))).map((s, idx) => (
                <div key={`${s.name}-${idx}`} className="card" style={{
                  padding: '10px 12px',
                  minWidth: 118,
                  borderColor: s.ok === true ? 'var(--good)' : s.ok === false ? 'var(--bad)' : 'var(--border)',
                }}>
                  <div className="eyebrow">{stageLabel(s.name)}</div>
                  <div className="mono" style={{
                    marginTop: 5,
                    fontSize: 11,
                    color: s.ok === true ? 'var(--good)' : s.ok === false ? 'var(--bad)' : 'var(--fg-muted)',
                  }}>{s.ok === true ? 'ok' : s.ok === false ? 'failed' : s.message}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="card" style={{ padding: 18 }}>
            {result?.video ? (
              <video src={absoluteMediaUrl(result.video.url)} controls style={{ width: '100%', display: 'block', border: '1px solid var(--border)' }} />
            ) : !running && preview ? (
              <div>
                <iframe
                  title="Selected clip preview"
                  src={preview.embedUrl}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                  style={{
                    width: '100%',
                    aspectRatio: '16 / 9',
                    display: 'block',
                    border: '1px solid var(--border)',
                    background: 'var(--panel-2)',
                  }}
                />
                <div className="row justify-between items-center" style={{ marginTop: 10, color: 'var(--fg-muted)', fontSize: 12 }}>
                  <span>{selectedPreset?.label || 'Custom YouTube clip'}</span>
                  <span className="mono">{selectedPreset?.start_label || preview.label}</span>
                </div>
              </div>
            ) : (
              <VideoFrame width="100%" height={9} seed={72} label={running ? 'loading clip' : 'paste a YouTube URL'} active />
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12 }}>
            <div className="card card-pad"><Stat label="CLIP top3" value={result?.clip ? result.clip.top3.toFixed(3) : '—'} /></div>
            <div className="card card-pad"><Stat label="ADQA" value={result?.adqa ? `${Math.round(result.adqa.score * 3)}/3` : '—'} /></div>
            <div className="card card-pad"><Stat label="Frames" value={result?.frames?.length || '—'} /></div>
          </div>

          <div className="card card-pad">
            <SectionHead eyebrow="Audio description" title="Candidate text" sub={null} />
            <p style={{ margin: 0, color: result?.ad ? 'var(--fg)' : 'var(--fg-muted)', lineHeight: 1.6 }}>
              {result?.ad || 'Run a clip to see the generated or supplied description.'}
            </p>
          </div>

          <div className="card card-pad">
            <SectionHead eyebrow="Sampled frames" title="Visual evidence" sub={null} />
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
              {result?.frames?.length ? result.frames.map((f, i) => (
                <div key={f.url} style={{ position: 'relative', border: '1px solid var(--border)', background: 'var(--panel-2)' }}>
                  <img src={absoluteMediaUrl(f.url)} style={{ width: '100%', display: 'block', aspectRatio: '16 / 9', objectFit: 'cover' }} />
                  <div className="mono" style={{ position: 'absolute', left: 6, bottom: 6, fontSize: 10, background: 'var(--panel)', border: '1px solid var(--border)', padding: '1px 5px' }}>f{i + 1}</div>
                </div>
              )) : Array.from({ length: 8 }).map((_, i) => <VideoFrame key={i} width="100%" height={9} seed={80 + i} label={`f${i + 1}`} />)}
            </div>
          </div>

          <div className="card card-pad">
            <SectionHead eyebrow="ADQA" title="Question-level grade" sub={null} />
            <div className="col gap-10">
              {(result?.adqa?.graded || []).map((g, i) => (
                <div key={i} className="card" style={{ padding: 14, borderLeft: `3px solid ${g.score ? 'var(--good)' : 'var(--bad)'}` }}>
                  <div className="row justify-between gap-12">
                    <strong>{g.question}</strong>
                    <Tag color={g.score ? 'var(--good)' : 'var(--bad)'}>{g.score ? 'YES' : 'NO'}</Tag>
                  </div>
                  <div style={{ marginTop: 8, color: 'var(--fg-muted)', lineHeight: 1.5 }}>{g.rationale}</div>
                </div>
              ))}
              {!result?.adqa?.graded?.length && <div style={{ color: 'var(--fg-muted)' }}>No grades yet.</div>}
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

Object.assign(window, { AuditPage });
