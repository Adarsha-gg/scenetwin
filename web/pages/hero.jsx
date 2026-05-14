// SceneTwin overview page

function HeroPage({ setPage }) {
  const previewFrames = [
    { label: 'motorcycle ridge', score: 0.33 },
    { label: 'steep drop', score: 0.31 },
    { label: 'dust hallway', score: 0.29 },
    { label: 'backlit figure', score: 0.28 },
  ];

  return (
    <main className="page" style={{ paddingTop: 56 }}>
      <section style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0, 1.05fr) minmax(360px, 0.95fr)',
        gap: 32,
        alignItems: 'stretch',
      }}>
        <div className="col justify-between" style={{ minHeight: 500, padding: '8px 0 24px' }}>
          <div>
            <div className="eyebrow accent">Reference-free audio description audit</div>
            <h1 className="serif" style={{
              margin: '18px 0 0',
              fontSize: 'clamp(54px, 7vw, 118px)',
              lineHeight: 0.92,
              fontWeight: 400,
              letterSpacing: 0,
              maxWidth: 920,
            }}>
              SceneTwin
            </h1>
            <p style={{
              maxWidth: 660,
              margin: '24px 0 0',
              fontSize: 18,
              lineHeight: 1.5,
              color: 'var(--fg-muted)',
            }}>
              Paste a YouTube clip and get a visual-access audit: sampled frames, generated or supplied AD, CLIP grounding, and frame-grounded ADQA.
            </p>
          </div>

          <div className="row gap-12 wrap" style={{ marginTop: 32 }}>
            <button className="btn primary lg" onClick={() => setPage('audit')}>Open live audit</button>
            <button className="btn lg" onClick={() => setPage('benchmark')}>View benchmark</button>
          </div>
        </div>

        <div className="card" style={{ padding: 18, minHeight: 500 }}>
          <div className="row justify-between items-center">
            <div className="eyebrow">Live audit preview</div>
            <Tag color="var(--good)">API READY</Tag>
          </div>
          <div style={{ marginTop: 18 }}>
            <iframe
              title="SceneTwin demo preview"
              src="https://www.youtube.com/embed/avz06PDqDbM?start=0"
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
              <span>Mission Impossible trailer from start</span>
              <span className="mono">t=0</span>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginTop: 16 }}>
            <div className="card card-pad"><Stat label="CLIP top3" value="0.333" /></div>
            <div className="card card-pad"><Stat label="ADQA" value="3/3" /></div>
            <div className="card card-pad"><Stat label="frames" value="8" /></div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 8, marginTop: 16 }}>
            {previewFrames.map((frame, i) => (
              <VideoFrame key={frame.label} width="100%" height={9} seed={90 + i} label={`f${i + 1}`} score={frame.score} />
            ))}
          </div>
          <div className="card card-pad" style={{ marginTop: 16 }}>
            <div className="row justify-between items-center">
              <div className="eyebrow">What the audit returns</div>
              <Tag color="var(--accent)">sample output</Tag>
            </div>
            <div className="col gap-10" style={{ marginTop: 14 }}>
              {[
                ['Motorcyclist on a high mountain peak?', true],
                ['Rider descends a steep rocky slope?', true],
                ['Backlit silhouetted figure appears?', true],
              ].map(([question, ok], i) => (
                <div key={question} className="card" style={{ padding: 12, borderLeft: `3px solid ${ok ? 'var(--good)' : 'var(--bad)'}` }}>
                  <div className="row justify-between gap-12">
                    <strong style={{ fontSize: 13 }}>{question}</strong>
                    <span className="mono" style={{ color: ok ? 'var(--good)' : 'var(--bad)', fontSize: 11 }}>{ok ? 'YES' : 'NO'}</span>
                  </div>
                  <div style={{ color: 'var(--fg-muted)', fontSize: 12, lineHeight: 1.45, marginTop: 6 }}>
                    The generated AD mentions the visible scene evidence.
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

Object.assign(window, { HeroPage });
