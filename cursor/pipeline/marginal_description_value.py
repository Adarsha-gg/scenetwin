#!/usr/bin/env python3
"""Marginal Description Value (MDV): score an AD on what it adds OVER the soundtrack.

Premise that unifies the whole SceneTwin thesis at the content level:
A blind listener already HEARS the audio (dialogue, narration, sound). An audio
description's job is the *marginal visual information it adds beyond the soundtrack* --
the content-level analogue of TRIBE's audiovisual-minus-audio accessibility gap.

Every current reference-free metric (incl. our ADQA) credits an AD for its TOTAL
coverage of frame-grounded questions. But questions the soundtrack already answers are
"free" -- the AD adds nothing there. MDV re-grounds ADQA:

  1. For each frame-grounded question, grade answerability FROM THE TRANSCRIPT ALONE
     (what the blind listener already gets). -> audio_score in {0, .5, 1}
  2. "Visual-only" questions = audio can't answer (audio_score == 0).
  3. raw ADQA  = AD recall over ALL questions          (status quo)
     MDV       = AD recall over VISUAL-ONLY questions  (marginal over audio)
  4. Audio-redundant fraction = share of questions the soundtrack already answers
     = how much the status-quo metric "leaks" credit for restating audio.

Reuses cached questions + per-tier AD grades that produced the 0.946/0.952 numbers,
so MDV is directly comparable. Only NEW LLM work: the text-only audio-baseline pass
(transcript + questions), ~60 calls. No humans, no new vision calls (the 2 Gemini-
blocked clips are fine here -- text only).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parent))
import machine_ad_tier as M  # noqa: E402  (shared provider-swappable LLM helpers)

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
Q_CSV = CURSOR / "output" / "external_adqa" / "external_adqa_questions.csv"
G_CSV = CURSOR / "output" / "external_adqa" / "external_adqa_grades.csv"
TRANSCRIPTS = CURSOR / "research" / "output" / "external_transcripts"
CACHE = CURSOR / "output" / "mdv" / "cache"
OUT_CSV = CURSOR / "output" / "mdv" / "mdv_per_clip.csv"
OUT_JSON = CURSOR / "output" / "marginal_description_value.json"
CHART = ROOT / "output" / "charts" / "scenetwin_mdv.png"
FINDINGS = CURSOR / "findings" / "marginal-description-value.md"

THREE = ["tier0_cross", "tier1_vatex_short", "tier3_va11y"]
GMAP = {t: i for i, t in enumerate(THREE)}

AUDIO_PROMPT = """You judge what a BLIND listener can answer from a video clip's SOUNDTRACK ALONE.
You are given the clip's audio transcript (all the listener hears: dialogue, narration,
sound described in words) and a list of questions about the VISUAL scene.

For EACH question, decide whether the transcript ALONE lets the listener answer it:
  1.0 = the transcript directly states or clearly implies the answer
  0.5 = the transcript hints at it but is ambiguous
  0.0 = the transcript gives no basis to answer (answer requires SEEING the video)

Judge ONLY from the transcript text. Do NOT use outside knowledge about what such a
video probably shows. An empty or contentless transcript means almost everything is 0.0.

Transcript:
\"\"\"{transcript}\"\"\"

Questions:
{questions}

Return JSON only: {{"grades":[{{"q_idx":0,"audio_score":0.0}}]}}"""


def grade_audio_baseline(cl, vid, transcript, questions, refresh):
    qpayload = [{"q_idx": int(q["q_idx"]), "question": q["question"], "answer_key": q["answer_key"]}
                for q in questions]
    payload = {"kind": "mdv_audio_baseline_v1", "model": M.MODEL, "video_id": vid,
               "transcript": transcript[:4000], "q": qpayload}

    def call():
        prompt = AUDIO_PROMPT.format(transcript=transcript.strip() or "(no speech / empty transcript)",
                                     questions=json.dumps(qpayload, indent=2))
        return M.parse_json(M.gen_content(cl, prompt))

    M.CACHE = CACHE  # redirect shared cache helper to MDV cache dir
    r = M.cache_json("audio", payload, call, refresh)
    out = {}
    grades = r.get("grades", []) if isinstance(r, dict) else []
    for g in grades:
        if isinstance(g, dict) and "q_idx" in g:
            try:
                out[int(g["q_idx"])] = float(g.get("audio_score", 0.0))
            except (TypeError, ValueError):
                pass
    return out


def rho3(df: pd.DataFrame, col: str) -> float:
    d = df[df.tier.isin(THREE)].copy()
    d["g"] = d.tier.map(GMAP)
    return float(spearmanr(d["g"], d[col])[0])


def full_order(df: pd.DataFrame, col: str) -> tuple[int, int]:
    fo = tot = 0
    for _, gg in df[df.tier.isin(THREE)].groupby("video_id"):
        by = dict(zip(gg.tier, gg[col]))
        if all(t in by for t in THREE):
            tot += 1
            fo += int(by[THREE[0]] < by[THREE[1]] < by[THREE[2]])
    return fo, tot


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--provider", default="gemini")
    ap.add_argument("--model", default=None)
    ap.add_argument("--refresh-cache", action="store_true")
    args = ap.parse_args()
    M.load_env(); M.configure(args.provider, args.model)
    print(f"Audio-baseline grader: {M.PROVIDER} / {M.MODEL}")
    cl = M.client()

    q = pd.read_csv(Q_CSV)
    g = pd.read_csv(G_CSV)
    vids = sorted(q.video_id.unique())
    if args.limit:
        vids = vids[: args.limit]

    # 1) audio-baseline grades per (clip, question)
    audio_rows = []
    for i, vid in enumerate(vids):
        tpath = TRANSCRIPTS / f"{vid}.txt"
        transcript = tpath.read_text(encoding="utf-8") if tpath.exists() else ""
        qs = q[q.video_id == vid].sort_values("q_idx").to_dict("records")
        ascore = grade_audio_baseline(cl, vid, transcript, qs, args.refresh_cache)
        for qi, s in ascore.items():
            audio_rows.append({"video_id": vid, "q_idx": qi, "audio_score": s})
        if (i + 1) % 10 == 0 or i == len(vids) - 1:
            print(f"  audio-baseline {i+1}/{len(vids)}")
    audio = pd.DataFrame(audio_rows)
    audio["audio_answerable"] = (audio["audio_score"] >= 0.5).astype(int)
    audio["visual_only"] = (audio["audio_score"] == 0.0).astype(int)

    # 2) merge with AD grades; per (clip, tier): raw ADQA recall vs MDV (visual-only recall)
    gg = g[g.video_id.isin(vids)].merge(audio[["video_id", "q_idx", "visual_only"]],
                                        on=["video_id", "q_idx"], how="inner")
    rows = []
    for (vid, tier), sub in gg.groupby(["video_id", "tier"]):
        vo = sub[sub.visual_only == 1]
        rows.append({
            "video_id": vid, "tier": tier, "category": sub["category"].iloc[0],
            "adqa": float(sub["score"].mean()),                      # status-quo: all questions
            "mdv": float(vo["score"].mean()) if len(vo) else np.nan,  # marginal: visual-only
            "n_q": len(sub), "n_visual_only": len(vo),
        })
    per = pd.DataFrame(rows)
    # clips where every question is audio-answerable have no MDV signal -> drop for MDV stats
    per_mdv = per.dropna(subset=["mdv"]).copy()

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    per.to_csv(OUT_CSV, index=False)

    # 3) audio-leak: fraction of questions the soundtrack already answers
    leak_overall = float(audio["audio_answerable"].mean())
    leak_by_cat = (q.merge(audio, on=["video_id", "q_idx"])
                    .groupby("category")["audio_answerable"].mean().sort_values(ascending=False))
    clip_leak = audio.groupby("video_id")["audio_answerable"].mean()

    # 4) does MDV change the metric? rho + ordering, status-quo vs marginal
    rep = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "grader": f"{M.PROVIDER}/{M.MODEL}", "n_clips": len(vids),
        "audio_leak_overall": leak_overall,
        "audio_leak_by_category": {k: float(v) for k, v in leak_by_cat.items()},
        "clips_fully_audio_redundant": int((clip_leak >= 0.999).sum()),
        "mean_visual_only_q_per_clip": float(per.groupby("video_id")["n_visual_only"].first().mean()),
    }
    for label, frame in [("all_clips", per), ("clips_with_visual_only_q", per_mdv)]:
        sub = frame.dropna(subset=["mdv"])
        fo_a, tot = full_order(sub, "adqa")
        fo_m, _ = full_order(sub, "mdv")
        rep[label] = {
            "n": int(sub.video_id.nunique()),
            "rho_adqa": rho3(sub, "adqa"), "rho_mdv": rho3(sub, "mdv"),
            "full_order_adqa": f"{fo_a}/{tot}", "full_order_mdv": f"{fo_m}/{tot}",
        }
        # pro vs crowd margin (tier3 - tier1): does scoring marginal-over-audio sharpen it?
        p = sub.pivot_table(index="video_id", columns="tier", values=["adqa", "mdv"])
        for sig in ("adqa", "mdv"):
            if (sig, "tier3_va11y") in p and (sig, "tier1_vatex_short") in p:
                d = (p[(sig, "tier3_va11y")] - p[(sig, "tier1_vatex_short")]).dropna()
                rep[label][f"pro_minus_crowd_{sig}_mean"] = float(d.mean())
                rep[label][f"pro_beats_crowd_{sig}_rate"] = float((d > 0).mean())

    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    # chart
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6))
    cats = leak_by_cat.index.tolist()
    ax1.barh(range(len(cats)), leak_by_cat.values, color="#6a1b9a")
    ax1.set_yticks(range(len(cats))); ax1.set_yticklabels(cats, fontsize=7)
    ax1.invert_yaxis(); ax1.set_xlabel("frac. of visual questions the SOUNDTRACK already answers")
    ax1.set_title(f"Audio-redundant credit ('metric leak')\noverall {leak_overall:.0%}", fontsize=10)
    ax1.axvline(leak_overall, color="k", ls="--", lw=0.8)
    sub = per_mdv
    tiers_lbl = ["tier0\ncross", "tier1\ncrowd", "tier3\npro"]
    adqa_m = [sub[sub.tier == t]["adqa"].mean() for t in THREE]
    mdv_m = [sub[sub.tier == t]["mdv"].mean() for t in THREE]
    x = np.arange(3); w = 0.36
    ax2.bar(x - w / 2, adqa_m, w, color="#90a4ae", label="ADQA (all questions)")
    ax2.bar(x + w / 2, mdv_m, w, color="#6a1b9a", label="MDV (marginal over audio)")
    ax2.set_xticks(x); ax2.set_xticklabels(tiers_lbl, fontsize=8)
    ax2.set_ylabel("mean recall"); ax2.set_ylim(0, 1)
    ax2.set_title("Tier scores: total vs marginal-over-audio", fontsize=10)
    ax2.legend(fontsize=8); ax2.grid(axis="y", alpha=0.25)
    fig.suptitle("Marginal Description Value: scoring what the AD adds beyond the soundtrack", fontsize=12)
    fig.tight_layout(); CHART.parent.mkdir(parents=True, exist_ok=True); fig.savefig(CHART, dpi=150)

    a = rep["clips_with_visual_only_q"]
    print(f"\nAUDIO LEAK overall: {leak_overall:.1%}  (clips fully audio-redundant: {rep['clips_fully_audio_redundant']})")
    print("Leak by category (top/bottom):")
    for k in list(leak_by_cat.index[:3]) + list(leak_by_cat.index[-3:]):
        print(f"   {k:28s} {leak_by_cat[k]:.0%}")
    print(f"\nrho:  ADQA={a['rho_adqa']:.3f}  MDV={a['rho_mdv']:.3f}   (n={a['n']})")
    print(f"full order: ADQA={a['full_order_adqa']}  MDV={a['full_order_mdv']}")
    print(f"pro>crowd margin: ADQA={a.get('pro_minus_crowd_adqa_mean'):.3f} ({a.get('pro_beats_crowd_adqa_rate'):.0%})  "
          f"MDV={a.get('pro_minus_crowd_mdv_mean'):.3f} ({a.get('pro_beats_crowd_mdv_rate'):.0%})")
    print(f"Wrote {OUT_JSON}\n      {CHART}\n      {OUT_CSV}")


if __name__ == "__main__":
    main()
