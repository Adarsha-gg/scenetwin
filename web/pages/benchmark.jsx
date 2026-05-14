// SceneTwin benchmark page

function BenchmarkPage() {
  const charts = [
    {
      title: 'Failure forecast',
      src: '../output/charts/scenetwin_failure_forecast.png',
      note: 'TRIBE separates weak descriptions on the cached 18-clip benchmark.',
    },
    {
      title: 'Per-tier heatmap',
      src: '../output/charts/scenetwin_per_tier_heatmap.png',
      note: 'Candidate quality rises from cross-scene negatives to professional AD.',
    },
    {
      title: 'Methodology',
      src: '../output/charts/scenetwin_methodology.png',
      note: 'CLIP grounding plus frame-grounded ADQA, with TRIBE as cached neural risk.',
    },
  ];

  return (
    <main className="page" style={{ paddingTop: 40 }}>
      <SectionHead
        eyebrow="Cached benchmark"
        title="Poster-ready results"
        sub="The live demo audits arbitrary YouTube clips. The benchmark tab keeps the NJBDA evidence in one clean view."
        right={<a className="btn" href="../output/scenetwin_njbda_poster.pdf" target="_blank">Open poster PDF</a>}
      />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 12 }}>
        <div className="card card-pad"><Stat label="Held-out rho" value="0.84" sub="live frame-based demo" /></div>
        <div className="card card-pad"><Stat label="Benchmark rho" value="0.929" sub="poster headline" /></div>
        <div className="card card-pad"><Stat label="TRIBE AUC" value="1.00" sub="cached fMRI benchmark" /></div>
        <div className="card card-pad"><Stat label="Recall@2" value="100" unit="%" sub="18-clip benchmark" /></div>
      </div>

      <section style={{ marginTop: 28, display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: 18 }}>
        <div className="card" style={{ padding: 18 }}>
          <div className="row justify-between items-center" style={{ marginBottom: 14 }}>
            <div>
              <div className="eyebrow">Main chart</div>
              <h2 style={{ margin: '6px 0 0', fontSize: 24, fontWeight: 500 }}>Why SceneTwin flags weak AD</h2>
            </div>
            <Tag color="var(--accent)">NJBDA 2026</Tag>
          </div>
          <img src="../output/charts/scenetwin_brain_three_panel.png" style={{ width: '100%', display: 'block', border: '1px solid var(--border)', background: 'var(--panel-2)' }} />
        </div>

        <div className="col gap-12">
          {[
            ['No reference needed', 'Scores the candidate against visual evidence, not against a single human caption.'],
            ['Frame-grounded ADQA', 'Questions are generated from sampled frames, then graded against the AD.'],
            ['Neural sidecar', 'TRIBE stays on cached benchmark clips where fMRI alignment exists.'],
          ].map(([title, body], i) => (
            <div key={title} className="card card-pad">
              <div className="row gap-12 items-center">
                <VideoFrame width={76} height={48} seed={120 + i} label={`0${i + 1}`} />
                <div>
                  <div style={{ fontWeight: 600 }}>{title}</div>
                  <div style={{ color: 'var(--fg-muted)', fontSize: 13, lineHeight: 1.45, marginTop: 4 }}>{body}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section style={{ marginTop: 18, display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 18 }}>
        {charts.map(chart => (
          <article key={chart.title} className="card" style={{ overflow: 'hidden' }}>
            <img src={chart.src} style={{ width: '100%', aspectRatio: '4 / 3', objectFit: 'contain', display: 'block', background: '#fff' }} />
            <div style={{ padding: 16 }}>
              <div style={{ fontWeight: 600 }}>{chart.title}</div>
              <p style={{ margin: '6px 0 0', color: 'var(--fg-muted)', fontSize: 13, lineHeight: 1.45 }}>{chart.note}</p>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}

Object.assign(window, { BenchmarkPage });

