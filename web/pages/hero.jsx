// SceneTwin overview page

function HeroPage({ setPage }) {
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
            <VideoFrame width="100%" height={9} seed={31} label="youtube clip" active>
              <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center' }}>
                <div style={{ width: 74, height: 74, border: '1px solid var(--border-strong)', display: 'grid', placeItems: 'center', background: 'var(--panel)' }}>
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" style={{ marginLeft: 3 }}>
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </div>
              </div>
            </VideoFrame>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginTop: 16 }}>
            <div className="card card-pad"><Stat label="CLIP top3" value="0.333" /></div>
            <div className="card card-pad"><Stat label="ADQA" value="3/3" /></div>
            <div className="card card-pad"><Stat label="frames" value="8" /></div>
          </div>
          <div className="card card-pad" style={{ marginTop: 16 }}>
            <div className="eyebrow">Current best t=0 demos</div>
            <div className="col gap-12" style={{ marginTop: 14 }}>
              {['Mission Impossible', 'John Wick 4', 'Spider-Man', 'The Batman'].map((name, i) => (
                <div key={name} className="row items-center gap-12">
                  <VideoFrame width={96} height={54} seed={40 + i} label={`0${i + 1}`} />
                  <div className="flex-1">
                    <div style={{ fontWeight: 600 }}>{name}</div>
                    <div className="mono" style={{ fontSize: 12, color: 'var(--fg-muted)', marginTop: 4 }}>ADQA 3/3</div>
                  </div>
                  <ScoreBar value={[0.333, 0.332, 0.317, 0.305][i]} width={90} />
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

