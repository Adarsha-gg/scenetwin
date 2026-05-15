// Compare page: why SceneTwin is not just another VLM grader

function ComparePage({ setPage }) {
  const rows = [
    {
      label: 'Generic VLM caption judge',
      blindValue: 'Can sound plausible while missing visual events blind viewers need.',
      method: 'Single model reads frames and text.',
      weakness: 'No neural need signal, no held-out risk routing, easy to reward fluent captions.',
    },
    {
      label: 'Reference metrics',
      blindValue: 'Grades similarity to a caption, not accessibility usefulness.',
      method: 'BLEU/CIDEr/embedding overlap against a target sentence.',
      weakness: 'Needs references and punishes valid alternate descriptions.',
    },
    {
      label: 'SceneTwin',
      blindValue: 'Asks whether the AD covers visible evidence needed to understand the scene.',
      method: 'CLIP grounding + frame-grounded ADQA + cached TRIBE neural risk.',
      weakness: 'Live mode is frame sampled; video-native grading is future work for full scripts.',
    },
  ];

  return (
    <main className="page" style={{ paddingTop: 40 }}>
      <SectionHead
        eyebrow="Comparison"
        title="Why this is more than a VLM vibe check"
        sub="SceneTwin is built around accessibility failure modes: what visual evidence is missing, whether a blind viewer receives it in the AD, and which clips deserve human review first."
        right={<button className="btn primary" onClick={() => setPage('audit')}>Try live audit</button>}
      />

      <section style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
        <div className="card" style={{ padding: 18 }}>
          <div className="row justify-between items-center" style={{ marginBottom: 14 }}>
            <div>
              <div className="eyebrow">Result</div>
              <h2 style={{ margin: '6px 0 0', fontSize: 24, fontWeight: 500 }}>SceneTwin ranks accessibility quality</h2>
            </div>
            <Tag color="var(--good)">rho 0.929</Tag>
          </div>
          <img src="../output/charts/scenetwin_per_tier_heatmap.png" style={{ width: '100%', display: 'block', border: '1px solid var(--border)', background: '#fff' }} />
        </div>

        <div className="card" style={{ padding: 18 }}>
          <div className="row justify-between items-center" style={{ marginBottom: 14 }}>
            <div>
              <div className="eyebrow">Failure routing</div>
              <h2 style={{ margin: '6px 0 0', fontSize: 24, fontWeight: 500 }}>TRIBE cuts review work</h2>
            </div>
            <Tag color="var(--accent)">recall@2 100%</Tag>
          </div>
          <img src="../output/charts/scenetwin_failure_forecast.png" style={{ width: '100%', display: 'block', border: '1px solid var(--border)', background: '#fff' }} />
        </div>
      </section>

      <section style={{ marginTop: 18, display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12 }}>
        <div className="card card-pad"><Stat label="No reference AD" value="0" sub="human gold scripts required for live clips" /></div>
        <div className="card card-pad"><Stat label="Evidence questions" value="3" sub="visual checks per live audit" /></div>
        <div className="card card-pad"><Stat label="Human review cut" value="2/18" sub="TRIBE review budget in benchmark" /></div>
      </section>

      <section className="card" style={{ marginTop: 18, overflow: 'hidden' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '0.9fr 1.2fr 1.1fr 1.2fr', borderBottom: '1px solid var(--border)' }}>
          {['Approach', 'Blind/low-vision value', 'How it scores', 'What it misses'].map(h => (
            <div key={h} className="eyebrow" style={{ padding: 14 }}>{h}</div>
          ))}
        </div>
        {rows.map((row, i) => (
          <div key={row.label} style={{
            display: 'grid',
            gridTemplateColumns: '0.9fr 1.2fr 1.1fr 1.2fr',
            borderBottom: i === rows.length - 1 ? 0 : '1px solid var(--border)',
            background: row.label === 'SceneTwin' ? 'var(--panel-2)' : 'var(--panel)',
          }}>
            <div style={{ padding: 14, fontWeight: 600 }}>{row.label}</div>
            <div style={{ padding: 14, color: 'var(--fg-muted)', lineHeight: 1.45 }}>{row.blindValue}</div>
            <div style={{ padding: 14, color: 'var(--fg-muted)', lineHeight: 1.45 }}>{row.method}</div>
            <div style={{ padding: 14, color: 'var(--fg-muted)', lineHeight: 1.45 }}>{row.weakness}</div>
          </div>
        ))}
      </section>

      <section style={{ marginTop: 18, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
        <div className="card card-pad">
          <div className="eyebrow accent">For blind viewers</div>
          <h2 style={{ margin: '8px 0 0', fontSize: 23, fontWeight: 500 }}>The unit is missing visual evidence</h2>
          <p style={{ color: 'var(--fg-muted)', lineHeight: 1.55 }}>
            SceneTwin does not ask whether a caption sounds good. It asks whether the AD tells a viewer about salient visual events, objects, motion, setting, and scene changes that are otherwise inaccessible.
          </p>
          <div className="col gap-8">
            {['Can I understand who is doing what?', 'Did the AD mention the action, not just the noun?', 'Does the description substitute visual signal when audio alone is insufficient?'].map(text => (
              <div key={text} className="card" style={{ padding: 12, borderLeft: '3px solid var(--good)' }}>{text}</div>
            ))}
          </div>
        </div>

        <div className="card card-pad">
          <div className="eyebrow accent">For demo honesty</div>
          <h2 style={{ margin: '8px 0 0', fontSize: 23, fontWeight: 500 }}>Live mode and benchmark mode are separate</h2>
          <p style={{ color: 'var(--fg-muted)', lineHeight: 1.55 }}>
            Live YouTube uses CLIP and ADQA because arbitrary videos do not have fMRI. TRIBE appears on cached benchmark clips only, where neural predictions and risk routing are defensible.
          </p>
          <img src="../output/charts/scenetwin_methodology.png" style={{ width: '100%', display: 'block', border: '1px solid var(--border)', background: '#fff' }} />
        </div>
      </section>
    </main>
  );
}

Object.assign(window, { ComparePage });

