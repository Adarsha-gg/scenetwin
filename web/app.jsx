// SceneTwin — main app

const APP_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "indigo",
  "theme": "dark"
}/*EDITMODE-END*/;

function App() {
  const [page, setPage] = useState('audit');
  const [tweaks, setTweak] = useTweaks(APP_DEFAULTS);

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
  else if (page === 'benchmark') content = <BenchmarkPage />;
  else content = <HeroPage setPage={setPage} />;

  return (
    <>
      <TopBar page={page} setPage={setPage} />
      {content}
      <Footer />
      <AppTweaks tweaks={tweaks} setTweak={setTweak} />
    </>
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
