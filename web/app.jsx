// SceneTwin — main app

const APP_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "indigo",
  "theme": "dark"
}/*EDITMODE-END*/;

function App() {
  const [page, setPage] = useState('hero');
  const [tweaks, setTweak] = useTweaks(APP_DEFAULTS);
  const [showIntro, setShowIntro] = useState(() => {
    try {
      return sessionStorage.getItem('scenetwin_intro_seen') !== '1';
    } catch (e) {
      return true;
    }
  });

  const closeIntro = useCallback(() => {
    try {
      sessionStorage.setItem('scenetwin_intro_seen', '1');
    } catch (e) {}
    setShowIntro(false);
  }, []);

  const openIntro = useCallback(() => setShowIntro(true), []);

  // Apply theme + accent globally
  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('light', tweaks.theme === 'light');
    const found = ACCENT_OPTIONS.find(a => a.name === tweaks.accent) || ACCENT_OPTIONS[0];
    root.style.setProperty('--accent', found.value);
    root.style.setProperty('--accent-ink', found.ink);
  }, [tweaks.theme, tweaks.accent]);

  // Scroll to top on page change
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }); }, [page]);

  let content;
  if (page === 'audit') content = <AuditPage />;
  else if (page === 'cached') content = <CachedClipsPage />;
  else if (page === 'benchmark') content = <BenchmarkPage />;
  else if (page === 'tribe') content = <TribeRiskPage />;
  else if (page === 'compare') content = <ComparePage setPage={setPage} />;
  else content = <HeroPage setPage={setPage} />;

  return (
    <>
      <TopBar page={page} setPage={setPage} onIntro={openIntro} />
      {showIntro && <IntroReel onClose={closeIntro} setPage={setPage} />}
      {content}
      <Footer />
      <AppTweaks tweaks={tweaks} setTweak={setTweak} />
    </>
  );
}

function IntroReel({ onClose, setPage }) {
  const slides = [
    {
      label: 'Frame-grounded ADQA',
      sub: 'Scene-specific questions expose whether the AD actually covers the action.',
      img: '../output/charts/scenetwin_per_tier_heatmap.png',
    },
    {
      label: 'Professional AD wins',
      sub: 'Benchmark ranking rewards complete descriptions over short caption-style summaries.',
      img: '../output/charts/scenetwin_bootstrap_ci.png',
    },
    {
      label: 'TRIBE risk triage',
      sub: 'Brain-backed visual-lift maps show where missing visual information is most expensive.',
      img: '../output/charts/tribe_clip_brains/clip_14_tribe_gap.png',
    },
    {
      label: 'Contest-ready workflow',
      sub: 'Cached clips for the stable story, Live Audit for fresh YouTube stress tests.',
      img: '../output/charts/scenetwin_failure_forecast.png',
    },
  ];
  const frames = [
    '../output/scenetwin_timing_20clip/adqa_v2/frames/clip_14/frame_00_t0.63.jpg',
    '../output/scenetwin_timing_20clip/adqa_v2/frames/clip_14/frame_01_t1.89.jpg',
    '../output/scenetwin_timing_20clip/adqa_v2/frames/clip_14/frame_03_t4.41.jpg',
    '../output/scenetwin_timing_20clip/adqa_v2/frames/clip_14/frame_07_t9.45.jpg',
  ];
  const [slide, setSlide] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setSlide(s => (s + 1) % slides.length), 2300);
    return () => clearInterval(timer);
  }, [slides.length]);

  useEffect(() => {
    const onKey = e => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const jump = target => {
    onClose();
    setPage(target);
  };

  return (
    <div className="intro-backdrop" role="dialog" aria-modal="true" aria-label="SceneTwin highlight reel">
      <section className="intro-reel">
        <button className="intro-close" onClick={onClose} aria-label="Close intro">X</button>
        <div className="intro-grid">
          <div className="intro-copy">
            <div className="intro-kicker">NJBDA demo reel</div>
            <h1 className="intro-title">
              Audio description audit that <span className="hot">shows its work.</span>
            </h1>
            <p className="intro-lede">
              SceneTwin checks whether an AD preserves the visual facts a blind or low-vision viewer needs, then ranks which clips deserve review first.
            </p>
            <div className="intro-metrics">
              <div className="intro-metric">
                <strong>0.929</strong>
                <span>CLIP + ADQA benchmark rho</span>
              </div>
              <div className="intro-metric">
                <strong>54/54</strong>
                <span>professional AD wins in pairwise checks</span>
              </div>
              <div className="intro-metric">
                <strong>100%</strong>
                <span>TRIBE recall@2 for known failure clips</span>
              </div>
            </div>
            <div className="intro-actions">
              <button className="intro-button primary" onClick={() => jump('cached')}>Start with cached clips</button>
              <button className="intro-button" onClick={() => jump('tribe')}>Show TRIBE risk</button>
              <button className="intro-button" onClick={() => jump('audit')}>Live YouTube audit</button>
            </div>
          </div>

          <div className="intro-stage">
            <div className="intro-screen">
              <div className="intro-filmstrip" aria-hidden="true">
                {frames.map((src, i) => (
                  <div className="intro-frame" key={src}>
                    <img src={src} alt="" />
                  </div>
                ))}
              </div>
              <div className="intro-main-visual">
                {slides.map((s, i) => (
                  <article className={"intro-slide " + (i === slide ? 'active' : '')} key={s.label}>
                    <img src={s.img} alt="" />
                    <div className="intro-slide-copy">
                      <strong>{s.label}</strong>
                      <span>{s.sub}</span>
                    </div>
                  </article>
                ))}
              </div>
            </div>
            <div className="intro-progress" aria-label="Intro slides">
              {slides.map((s, i) => (
                <button
                  key={s.label}
                  className={i === slide ? 'active' : ''}
                  onClick={() => setSlide(i)}
                  aria-label={`Show ${s.label}`}
                />
              ))}
            </div>
            <div className="intro-ticker">
              <span>
                DOWNLOAD ok / SAMPLE FRAMES ok / GENERATE AD ok / CLIP ok / ADQA ok / TRIBE RISK ready / cached benchmark ready / live YouTube optional
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function AppTweaks({ tweaks, setTweak }) {
  return (
    <TweaksPanel title="Tweaks">
      <TweakSection label="Theme" />
      <TweakRadio
        label="Mode"
        value={tweaks.theme}
        onChange={v => setTweak('theme', v)}
        options={['dark', 'light']}
      />
      <TweakSection label="Accent" />
      <TweakColor
        label="Color"
        value={ACCENT_OPTIONS.find(a => a.name === tweaks.accent)?.value || ACCENT_OPTIONS[0].value}
        options={ACCENT_OPTIONS.map(a => a.value)}
        onChange={v => {
          const found = ACCENT_OPTIONS.find(a => a.value === v) || ACCENT_OPTIONS[0];
          setTweak('accent', found.name);
        }}
      />
    </TweaksPanel>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
