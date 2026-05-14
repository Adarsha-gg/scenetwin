#!/usr/bin/env python3
"""SceneTwin demo, Gradio app.

Two tabs.
  Cached benchmark: replay the 18 clip audit shipped for NJBDA 2026.
  Live YouTube:     paste a URL, run the audit on a fresh clip.

Run:   python3 demo/scenetwin_demo.py
"""
from __future__ import annotations

import re
from pathlib import Path
from textwrap import dedent

import pandas as pd

import gradio_client.utils as _gcu
_orig_get_type = _gcu.get_type
_orig_jspt = _gcu._json_schema_to_python_type
def _safe_get_type(schema):
    if isinstance(schema, bool):
        return "Any"
    return _orig_get_type(schema)
def _safe_jspt(schema, defs):
    if isinstance(schema, bool):
        return "Any"
    return _orig_jspt(schema, defs)
_gcu.get_type = _safe_get_type
_gcu._json_schema_to_python_type = _safe_jspt

import gradio as gr

import live_pipeline as lp
from live_presets import LIVE_DEMO_DEFAULT, LIVE_DEMO_PRESETS


# Paths.
ROOT = Path(__file__).resolve().parents[1]
CLIPS_DIR = ROOT / "demo" / "clips"
FRAMES_DIR = ROOT / "demo" / "frames"
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
ENS = TIMING / "ensemble"
ADQA = TIMING / "adqa_v4"
TRIBE = TIMING / "tribe_native"
NEED = TIMING / "need"


def _safe_read_csv(path: Path, cols: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=cols or [])
    try:
        df = pd.read_csv(path)
        if cols:
            keep = [c for c in cols if c in df.columns]
            return df[keep] if keep else df
        return df
    except Exception:
        return pd.DataFrame(columns=cols or [])


ensemble_df = _safe_read_csv(ENS / "adqa_clip_ensemble_scores.csv", [
    "clip_idx", "tier", "gt", "clip_mean", "adqa_v2_score",
    "ensemble_mean_clip_mean",
]).rename(columns={
    "adqa_v2_score": "adqa_score",
    "ensemble_mean_clip_mean": "ensemble",
})
questions_df = _safe_read_csv(ADQA / "adqa_v4_questions.csv")
grades_df = _safe_read_csv(ADQA / "adqa_v4_grades.csv")
tribe_df = _safe_read_csv(TRIBE / "tribe_failure_forecast.csv")
need_curve_df = _safe_read_csv(NEED / "neural_description_need_curve.csv")


CACHE_READY = (
    not ensemble_df.empty and not questions_df.empty
    and not grades_df.empty and not tribe_df.empty
)


text_cols = {
    "tier0_cross":       "tier0_cross_text",
    "tier1_vatex_short": "tier1_vatex_short_text",
    "tier2_vatex_long":  "tier2_vatex_long_text",
    "tier3_va11y":       "tier3_va11y_text",
}
word_cols = {
    "tier0_cross":       "tier0_cross_words",
    "tier1_vatex_short": "tier1_vatex_short_words",
    "tier2_vatex_long":  "tier2_vatex_long_words",
    "tier3_va11y":       "tier3_va11y_words_feature",
}
TIER_LABEL = {
    "tier3_va11y":       "Tier 3, Professional AD",
    "tier2_vatex_long":  "Tier 2, VATEX long",
    "tier1_vatex_short": "Tier 1, VATEX short",
    "tier0_cross":       "Tier 0, Cross category (wrong scene)",
}
TIER_COLOR = {
    "tier3_va11y":       "#0d7f83",
    "tier2_vatex_long":  "#285a8f",
    "tier1_vatex_short": "#c88a20",
    "tier0_cross":       "#b73558",
}
TIER_ORDER = ["tier3_va11y", "tier2_vatex_long",
              "tier1_vatex_short", "tier0_cross"]

if not tribe_df.empty:
    available_clips: list[tuple[int, str]] = []
    for idx in sorted(tribe_df["clip_idx"].unique()):
        row = tribe_df[tribe_df["clip_idx"] == idx].iloc[0]
        cat = row.get("category_feature", row.get("category", ""))
        available_clips.append((int(idx), str(cat)))
    CLIP_OPTIONS = [f"clip_{idx:02d}, {cat}" for idx, cat in available_clips]
    OPT_TO_IDX = {opt: idx for opt, (idx, _) in zip(CLIP_OPTIONS, available_clips)}
else:
    available_clips = []
    CLIP_OPTIONS = []
    OPT_TO_IDX = {}


def find_clip_video(idx: int):
    for ext in ("mp4", "mkv", "webm"):
        p = CLIPS_DIR / f"clip_{idx:02d}.{ext}"
        if p.exists():
            return str(p)
    return None


def extract_frames(idx: int, n: int = 8) -> list[str]:
    out_dir = FRAMES_DIR / f"clip_{idx:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    cached = sorted(out_dir.glob("frame_*.jpg"))
    if len(cached) >= n:
        return [str(p) for p in cached[:n]]
    video = find_clip_video(idx)
    if not video:
        return []
    try:
        import cv2
    except ImportError:
        return []
    cap = cv2.VideoCapture(video)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    idxs = [int(round(i * (total - 1) / max(n - 1, 1))) for i in range(n)]
    paths = []
    for i, fi in enumerate(idxs):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ok, frame = cap.read()
        if not ok:
            continue
        p = out_dir / f"frame_{i:02d}.jpg"
        cv2.imwrite(str(p), frame)
        paths.append(str(p))
    cap.release()
    return paths


def need_curve_plot(idx: int):
    """Return a matplotlib Figure of TRIBE need score over time, or None."""
    if need_curve_df.empty:
        return None
    sub = need_curve_df[need_curve_df["clip_idx"] == idx].sort_values("t")
    if sub.empty:
        return None
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None
    fig, ax = plt.subplots(figsize=(6.5, 2.4), dpi=110, facecolor="white")
    ax.set_facecolor("white")
    times = sub["start_s"].to_numpy()
    need = sub["need_score"].to_numpy()
    ax.fill_between(times, 0, need, color="#0d7f83", alpha=0.25)
    ax.plot(times, need, color="#0d7f83", linewidth=2.0)
    ax.axhline(0.5, color="#b73558", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.set_xlabel("time (s)", color="#222")
    ax.set_ylabel("AD need", color="#222")
    ax.tick_params(colors="#222")
    ax.set_ylim(0, max(1.0, need.max() * 1.1))
    ax.set_title("TRIBE accessibility gap over time",
                 fontsize=10, loc="left", color="#222")
    for spine in ax.spines.values():
        spine.set_color("#aaa")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


# Cached tab renderer.
def render_clip(clip_opt: str):
    blank = (
        "## Pick a clip", None, [], "_no questions cached_",
        "<i>no scores cached</i>", "<i>no TRIBE data</i>", None, None,
    )
    if not CACHE_READY:
        return (
            "### Cached benchmark data is missing.\n"
            "Expected files under `output/scenetwin_timing_20clip/`. "
            "The Live YouTube tab can still run.",
            None, [], "", "", "", None, None,
        )
    idx = OPT_TO_IDX.get(clip_opt)
    if idx is None:
        return blank
    tr = tribe_df[tribe_df["clip_idx"] == idx].iloc[0]
    video = find_clip_video(idx)
    frames = extract_frames(idx)

    qs = questions_df[questions_df["clip_idx"] == idx].sort_values("q_idx")
    questions_md = "### Frame grounded ADQA questions (GPT-4o)\n\n"
    for _, r in qs.iterrows():
        questions_md += (
            f"**Q{int(r['q_idx'])+1}.** {r['question']}\n\n"
            f"&nbsp;&nbsp;_visual evidence required:_ "
            f"`{r['required_visual_evidence']}`\n\n"
        )

    tier_md_parts = []
    for tier in TIER_ORDER:
        row = ensemble_df[(ensemble_df["clip_idx"] == idx) &
                          (ensemble_df["tier"] == tier)]
        if row.empty:
            continue
        row = row.iloc[0]
        text = tr[text_cols[tier]]
        words = tr[word_cols[tier]]
        grades = grades_df[(grades_df["clip_idx"] == idx) &
                           (grades_df["tier"] == tier)]
        if grades.empty:
            grades_str = ""
        else:
            yn = ["✓" if s >= 0.5 else "✗"
                  for s in grades["score"]]
            grades_str = " ".join(yn)
        color = TIER_COLOR[tier]
        ensemble = row["ensemble"]
        clip_s = row["clip_mean"]
        adqa_s = row["adqa_score"]
        bar = int(round(ensemble * 100))
        tier_md_parts.append(dedent(f"""
        <div class="st-card" style="border-left:6px solid {color}">
          <div style="font-weight:700;color:{color} !important;font-size:1.05em">
            {TIER_LABEL[tier]}, {words} words
          </div>
          <div style="margin:0.3em 0;font-style:italic">"{text}"</div>
          <div style="display:flex;gap:1.5em;font-size:0.95em">
            <span><b>Ensemble:</b> {ensemble:.2f}</span>
            <span><b>CLIP:</b> {clip_s:.2f}</span>
            <span><b>ADQA:</b> {adqa_s:.2f}  {grades_str}</span>
          </div>
          <div style="margin-top:0.3em;background:#eee;border-radius:3px;
                      height:10px;width:100%;overflow:hidden">
            <div style="background:{color};height:100%;width:{bar}%"></div>
          </div>
        </div>
        """))
    tiers_html = "".join(tier_md_parts)

    risk = float(tr["mean_standard_slot_score"])
    rank = int(tr["risk_rank"])
    fragile = bool(tr["all4_fail"])
    risk_color = "#b73558" if fragile else "#0d7f83"
    pressure = float(tr.get("tribe_pressure_feature",
                            tr.get("tribe_pressure", 0.0)))
    risk_md = dedent(f"""
    <div class="st-card" style="border:2px solid {risk_color}">
      <div class="st-muted" style="font-size:0.85em;text-transform:uppercase;
                  font-weight:700;text-align:center">
        TRIBE risk forecast
      </div>
      <div style="font-size:1.8em;font-weight:900;color:{risk_color} !important;
                  text-align:center">
        {risk:.3f}
      </div>
      <div style="font-size:0.95em;text-align:center">
        Risk rank: <b>{rank}</b> of 18,
        {'<span style="color:#b73558 !important"><b>flagged for review</b></span>'
         if fragile else 'evaluator should be reliable'}
      </div>
      <hr style="border:none;border-top:1px solid #eee;margin:0.6em 0">
      <div class="st-muted" style="font-size:0.85em">
        TRIBE pressure (mean across clip): <b>{pressure:.3f}</b><br>
        Brain accessibility gap is the residual after audio prediction.
        High gap means visual content is doing work that the audio track
        alone cannot replace, so AD is load bearing here.
      </div>
    </div>
    """)

    cat = str(tr.get("category_feature", tr.get("category", "")))
    duration = float(tr.get("duration_s", 0))
    header_md = (
        f"## clip_{idx:02d}, {cat}, {duration:.1f} sec\n\n"
        f"_Source: VideoA11y / VATEX. Pre cached scores, no live API._"
    )

    fig = need_curve_plot(idx)
    return header_md, video, frames, questions_md, tiers_html, risk_md, idx, fig


def example_choices_for(idx: int | None) -> list[tuple[str, str]]:
    if idx is None or tribe_df.empty:
        return []
    tr = tribe_df[tribe_df["clip_idx"] == idx]
    if tr.empty:
        return []
    tr = tr.iloc[0]
    choices = []
    for tier in TIER_ORDER:
        words = int(tr[word_cols[tier]])
        label = f"{TIER_LABEL[tier]}, {words} words"
        choices.append((label, tier))
    return choices


def grade_cached(clip_opt: str, example_tier: str):
    if not CACHE_READY:
        return "Cached data not available."
    idx = OPT_TO_IDX.get(clip_opt)
    if idx is None or not example_tier:
        return "Pick a clip and an example description first."
    tr = tribe_df[tribe_df["clip_idx"] == idx].iloc[0]
    text = str(tr[text_cols[example_tier]])
    row = ensemble_df[(ensemble_df["clip_idx"] == idx) &
                      (ensemble_df["tier"] == example_tier)]
    if row.empty:
        return "No cached score for that pair."
    row = row.iloc[0]
    ensemble = float(row["ensemble"])
    clip_s = float(row["clip_mean"])
    adqa_s = float(row["adqa_score"])
    color = TIER_COLOR[example_tier]
    grades = grades_df[(grades_df["clip_idx"] == idx) &
                       (grades_df["tier"] == example_tier)].sort_values("q_idx")
    q_lookup = {int(r["q_idx"]): r["question"]
                for _, r in questions_df[questions_df["clip_idx"] == idx].iterrows()}
    lines = []
    yes_count = 0
    for _, g in grades.iterrows():
        is_yes = g["score"] >= 0.5
        icon = "✓" if is_yes else "✗"
        if is_yes:
            yes_count += 1
        q_text = q_lookup.get(int(g["q_idx"]), "")
        ev = str(g.get("evidence_quote", "")).strip()
        rat = str(g.get("grade_rationale", "")).strip()
        ev_md = f"_evidence:_ \"{ev}\"" if ev and ev != "nan" else ""
        rat_md = f"_grader:_ {rat}" if rat and rat != "nan" else ""
        lines.append(
            f"**Q{int(g['q_idx'])+1}** {icon}  {q_text}\n\n"
            f"&nbsp;&nbsp;{ev_md}\n\n"
            f"&nbsp;&nbsp;{rat_md}"
        )
    bar = int(round(ensemble * 100))
    header = dedent(f"""
    <div class="st-card" style="border-left:8px solid {color}">
      <div class="st-muted" style="font-size:0.95em;font-weight:700">
        Candidate description
      </div>
      <div style="font-style:italic;margin:0.35em 0;font-size:1.05em">
        "{text}"
      </div>
      <div style="display:flex;gap:1.5em;margin-top:0.4em">
        <span><b>Ensemble:</b> <span style="color:{color} !important;font-weight:800;
              font-size:1.15em">{ensemble:.2f}</span></span>
        <span><b>CLIP grounding:</b> {clip_s:.2f}</span>
        <span><b>ADQA:</b> {adqa_s:.2f}, {yes_count} of {len(grades)} ✓</span>
      </div>
      <div style="margin-top:0.4em;background:#eee;border-radius:3px;
                  height:10px;width:100%;overflow:hidden">
        <div style="background:{color};height:100%;width:{bar}%"></div>
      </div>
    </div>
    """)
    return header + "\n\n".join(lines)


# Live YouTube tab.
def _badge(ok: bool, label: str, msg: str) -> str:
    color = "#0d7f83" if ok else "#b73558"
    icon = "✓" if ok else "✗"
    return (
        f"<div style='display:inline-block;margin:0.15em 0.4em 0.15em 0;"
        f"padding:0.25em 0.7em;border-radius:14px;background:{color};"
        f"color:#fff;font-size:0.85em;font-weight:700'>"
        f"{icon} {label}: {msg}</div>"
    )


def run_live_pipeline(url: str, candidate_ad: str, run_tribe: bool,
                      progress=gr.Progress()):
    """Generator that yields UI updates as each stage finishes."""
    stages_html = ""
    ad_text = (candidate_ad or "").strip()
    empty_outputs = (stages_html, None, [], ad_text, "<i>not run</i>",
                     "<i>not run</i>", "<i>not run</i>")

    if not url or not url.strip():
        stages_html = _badge(False, "URL", "paste a YouTube link first")
        yield (stages_html, None, [], ad_text,
               "<i>not run</i>", "<i>not run</i>", "<i>not run</i>")
        return

    progress(0.05, desc="downloading")
    ok, msg, dl = lp.stage_download(url.strip(), max_seconds=30)
    stages_html += _badge(ok, "download", msg)
    if not ok:
        yield (stages_html, None, [], ad_text,
               "<i>skipped</i>", "<i>skipped</i>", "<i>skipped</i>")
        return
    video = dl["video"]
    slug = dl["slug"]
    yield (stages_html, video, [], ad_text,
           "<i>pending</i>", "<i>pending</i>", "<i>pending</i>")

    progress(0.2, desc="extracting frames")
    ok, msg, fr = lp.stage_frames(video, slug, n=8)
    stages_html += _badge(ok, "frames", msg)
    if not ok:
        yield (stages_html, video, [], ad_text,
               "<i>skipped</i>", "<i>skipped</i>", "<i>skipped</i>")
        return
    frames = fr["frames"]
    yield (stages_html, video, frames, ad_text,
           "<i>pending</i>", "<i>pending</i>", "<i>pending</i>")

    if not ad_text:
        progress(0.35, desc="generating AD")
        ok, msg, gen = lp.stage_generate_ad(frames)
        stages_html += _badge(ok, "AD gen", msg)
        if ok:
            ad_text = gen["ad"]
        yield (stages_html, video, frames, ad_text,
               "<i>pending</i>", "<i>pending</i>", "<i>pending</i>")
    else:
        stages_html += _badge(True, "AD", "using your text")
        yield (stages_html, video, frames, ad_text,
               "<i>pending</i>", "<i>pending</i>", "<i>pending</i>")

    if not ad_text:
        yield (stages_html, video, frames, ad_text,
               "<i>no AD to score</i>", "<i>no AD to score</i>",
               "<i>no AD to score</i>")
        return

    progress(0.55, desc="CLIP grounding")
    ok, msg, cl = lp.stage_clip_grounding(frames, ad_text)
    stages_html += _badge(ok, "CLIP", msg)
    if ok:
        clip_html = (
            f"<div class='st-card' style='border:1px solid #0d7f83'>"
            f"<div style='font-weight:700;color:#0d7f83 !important'>"
            f"CLIP visual grounding</div>"
            f"<div style='margin-top:0.3em'>mean across frames: "
            f"<b>{cl['mean']:.3f}</b>, top 3 frames: <b>{cl['top3']:.3f}</b></div>"
            f"<div class='st-muted' style='margin-top:0.3em;font-size:0.9em'>"
            f"per frame: " + ", ".join(f"{x:.2f}" for x in cl["per_frame"])
            + "</div></div>"
        )
    else:
        clip_html = f"<i>{msg}</i>"
    yield (stages_html, video, frames, ad_text, clip_html,
           "<i>pending</i>", "<i>pending</i>")

    progress(0.75, desc="ADQA gen + grade")
    ok, msg, aq = lp.stage_adqa(frames, ad_text)
    stages_html += _badge(ok, "ADQA", msg)
    if ok:
        rows = []
        for g in aq["graded"]:
            icon = "✓" if g["score"] else "✗"
            color = "#0d7f83" if g["score"] else "#b73558"
            rows.append(
                f"<div class='st-card' style='border-left:4px solid {color};"
                f"margin:0.3em 0'>"
                f"<b>{icon} {g['question']}</b><br>"
                f"<span class='st-muted' style='font-size:0.9em'>"
                f"needed: {g['evidence']}</span><br>"
                f"<span class='st-note' style='font-size:0.9em'>"
                f"grader: {g['rationale']}</span></div>"
            )
        adqa_html = (
            f"<div class='st-card' style='border:1px solid #285a8f'>"
            f"<div style='font-weight:700;color:#285a8f !important'>"
            f"Frame grounded ADQA, score {aq['score']:.2f}</div>"
            + "".join(rows) + "</div>"
        )
    else:
        adqa_html = f"<i>{msg}</i>"
    yield (stages_html, video, frames, ad_text, clip_html, adqa_html,
           "<i>pending</i>")

    if run_tribe:
        progress(0.9, desc="TRIBE encoder")
        ok, msg, tr = lp.stage_tribe_proxy(video, ad_text)
        stages_html += _badge(ok, "TRIBE", msg)
        if ok:
            align = tr["alignment_cosine"]
            verdict = (
                "AD aligns with video-only prediction"
                if align > 0.95
                else "AD drifts from video-only prediction"
            )
            color = "#0d7f83" if align > 0.95 else "#c88a20"
            tribe_html = (
                f"<div style='border:2px solid {color};padding:0.7em 0.9em;"
                f"border-radius:6px;background:#fff'>"
                f"<div style='font-weight:700;color:{color}'>"
                f"TRIBE neural alignment proxy</div>"
                f"<div style='font-size:1.6em;font-weight:900;color:{color};"
                f"margin:0.3em 0'>{align:.3f}</div>"
                f"<div style='color:#333'>{verdict}</div>"
                f"<div style='margin-top:0.4em;color:#666;font-size:0.85em'>"
                f"Predicted fMRI activation, video only vs video plus AD. "
                f"Higher cosine means the AD substitutes the visual "
                f"signal in TRIBE's predicted cortex. Proxy only, no real "
                f"fMRI here.<br>"
                f"LH mean (video / +AD): {tr['video_mean_lh']:.3f} / "
                f"{tr['video_ad_mean_lh']:.3f}, "
                f"RH mean: {tr['video_mean_rh']:.3f} / "
                f"{tr['video_ad_mean_rh']:.3f}</div></div>"
            )
        else:
            tribe_html = (
                f"<i>{msg}</i><br>"
                f"<span style='font-size:0.85em;color:#777'>"
                f"TRIBE is heavy (Python 3.11+ and ~6 GB weights). "
                f"Toggle it off if you do not need the neural proxy.</span>"
            )
    else:
        stages_html += _badge(True, "TRIBE", "skipped by user")
        tribe_html = "<i>TRIBE skipped</i>"

    progress(1.0, desc="done")
    yield (stages_html, video, frames, ad_text, clip_html, adqa_html,
           tribe_html)


def load_live_preset(label: str):
    return LIVE_DEMO_PRESETS.get(label, ""), ""


# Gradio UI.
def build_app():
    with gr.Blocks(
        title="SceneTwin demo",
        theme=gr.themes.Soft(primary_hue="teal", secondary_hue="amber"),
        css="""
        .gradio-container { max-width: 1400px !important }
        h1 { color: #0d7f83 }
        .small-note { color:#666; font-size:0.9em }
        /* Panels stay legible in both light and dark themes. */
        .st-card {
          background: #ffffff !important;
          color: #1a1a1a !important;
          border-radius: 6px;
          padding: 0.7em 0.9em;
          margin: 0.4em 0;
          box-shadow: 0 1px 2px rgba(0,0,0,0.08);
        }
        .st-card * { color: inherit !important; }
        .st-card b, .st-card strong { color: #000 !important; font-weight:700 }
        .st-muted { color: #555 !important; }
        .st-note  { color: #444 !important; }
        """,
    ) as app:
        gr.Markdown(
            "# SceneTwin\n"
            "*A reference free audit of audio description for blind and low "
            "vision viewers. Two signal core (CLIP plus frame grounded ADQA) "
            "with TRIBE as a neural side car.*"
        )

        with gr.Tabs():
            # Cached benchmark tab.
            with gr.Tab("Cached benchmark (18 clips)"):
                if not CACHE_READY:
                    gr.Markdown(
                        "_Cached benchmark data missing under "
                        "`output/scenetwin_timing_20clip/`. Falling back to "
                        "the live tab._"
                    )
                gr.Markdown(
                    "Pick a clip from the 18 clip benchmark. The audit "
                    "replays from cached results, no live API calls."
                )

                with gr.Row():
                    with gr.Column(scale=2):
                        clip_picker = gr.Dropdown(
                            choices=CLIP_OPTIONS,
                            value=CLIP_OPTIONS[0] if CLIP_OPTIONS else None,
                            label="Clip",
                        )
                        header_md = gr.Markdown()
                        video = gr.Video(label="Source clip", autoplay=False)
                    with gr.Column(scale=3):
                        frames = gr.Gallery(
                            label="Eight sampled frames",
                            columns=4, rows=2, height=320,
                            object_fit="cover", show_label=True,
                        )
                        risk_md = gr.HTML()

                with gr.Row():
                    need_plot = gr.Plot(label="TRIBE need curve")

                with gr.Row():
                    with gr.Column():
                        questions_md = gr.Markdown()
                    with gr.Column():
                        gr.Markdown("### Four candidate audio descriptions, ranked")
                        tiers_html = gr.HTML()

                clip_idx_state = gr.State(value=None)

                gr.Markdown("---")
                gr.Markdown(
                    "## Try a candidate description\n"
                    "Pick any of the four candidates and see the cached grade."
                )
                with gr.Row():
                    with gr.Column(scale=2):
                        example_picker = gr.Radio(
                            choices=example_choices_for(
                                available_clips[0][0] if available_clips else None),
                            value=TIER_ORDER[0] if CACHE_READY else None,
                            label="Candidate description",
                        )
                        grade_btn = gr.Button("Show cached grade",
                                              variant="primary")
                    with gr.Column(scale=3):
                        live_out = gr.HTML()

                def on_clip_change(opt):
                    idx = OPT_TO_IDX.get(opt)
                    outputs = render_clip(opt)
                    new_choices = example_choices_for(idx)
                    value = TIER_ORDER[0] if new_choices else None
                    return (*outputs,
                            gr.update(choices=new_choices, value=value))

                clip_picker.change(
                    fn=on_clip_change,
                    inputs=clip_picker,
                    outputs=[header_md, video, frames, questions_md,
                             tiers_html, risk_md, clip_idx_state,
                             need_plot, example_picker],
                )
                grade_btn.click(
                    fn=grade_cached,
                    inputs=[clip_picker, example_picker],
                    outputs=live_out,
                )
                if CACHE_READY:
                    app.load(
                        fn=render_clip,
                        inputs=clip_picker,
                        outputs=[header_md, video, frames, questions_md,
                                 tiers_html, risk_md, clip_idx_state,
                                 need_plot],
                    )

            # Live YouTube tab.
            with gr.Tab("Live YouTube (CLIP + ADQA only)"):
                gr.HTML(
                    "<div class='st-card' style='border-left:6px solid #c88a20'>"
                    "<b style='color:#8a5a00 !important'>Scope of this tab.</b><br>"
                    "Live YouTube runs the two signal core only, CLIP visual "
                    "grounding plus frame grounded ADQA. The TRIBE neural "
                    "risk forecaster needs ground truth fMRI from human "
                    "viewers, which does not exist for arbitrary clips. "
                    "TRIBE's full result (AUC = 1.00, recall@2/18 = 100%, "
                    "p = 0.0065) is on the <b>Cached benchmark</b> tab where "
                    "the 18 clips have real fMRI alignment."
                    "</div>"
                )
                gr.Markdown(
                    "Paste a short YouTube URL. The pipeline downloads the "
                    "clip (trimmed to 30 seconds), samples 8 frames, runs "
                    "CLIP grounding, then generates and grades 3 frame "
                    "grounded ADQA questions."
                )
                openai_present = lp.get_api_key("openai") is not None
                anth_present = lp.get_api_key("anthropic") is not None
                key_status = []
                key_status.append(
                    f"OpenAI key {'✓' if openai_present else '✗'}"
                )
                key_status.append(
                    f"Anthropic key {'✓' if anth_present else '✗'}"
                )
                gr.Markdown(
                    "<div class='small-note'>"
                    "Keys read from env or `.env`. " + ", ".join(key_status)
                    + ". CLIP runs locally and needs no key. ADQA needs "
                    "OPENAI_API_KEY. AD generation prefers OpenAI then "
                    "Anthropic. TRIBE is optional.</div>"
                )

                with gr.Row():
                    with gr.Column(scale=2):
                        demo_picker = gr.Dropdown(
                            choices=list(LIVE_DEMO_PRESETS),
                            value=LIVE_DEMO_DEFAULT,
                            label="Demo video",
                        )
                        load_demo_btn = gr.Button("Load demo video")
                        url_in = gr.Textbox(
                            label="YouTube URL",
                            value=LIVE_DEMO_PRESETS[LIVE_DEMO_DEFAULT],
                            placeholder="https://www.youtube.com/watch?v=...",
                        )
                        ad_in = gr.Textbox(
                            label="Candidate AD (optional, leave blank to auto generate)",
                            lines=3,
                        )
                        run_tribe_chk = gr.State(value=False)
                        go_btn = gr.Button("Run pipeline", variant="primary")
                        stages_html = gr.HTML(label="Stage status")
                    with gr.Column(scale=3):
                        live_video = gr.Video(label="Downloaded clip",
                                              autoplay=False)
                        live_frames = gr.Gallery(
                            label="Sampled frames",
                            columns=4, rows=2, height=300,
                            object_fit="cover",
                        )
                        live_ad = gr.Textbox(label="AD in use", lines=3,
                                             interactive=False)

                with gr.Row():
                    live_clip_html = gr.HTML()
                with gr.Row():
                    live_adqa_html = gr.HTML()
                # TRIBE output is intentionally hidden on the live tab.
                live_tribe_html = gr.HTML(visible=False)

                go_btn.click(
                    fn=run_live_pipeline,
                    inputs=[url_in, ad_in, run_tribe_chk],
                    outputs=[stages_html, live_video, live_frames, live_ad,
                             live_clip_html, live_adqa_html, live_tribe_html],
                )
                load_demo_btn.click(
                    fn=load_live_preset,
                    inputs=demo_picker,
                    outputs=[url_in, ad_in],
                )

    return app


if __name__ == "__main__":
    app = build_app()
    app.queue()
    app.launch(server_name="0.0.0.0", server_port=7860,
               inbrowser=False, show_api=False, share=False)
