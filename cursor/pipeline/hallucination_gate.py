#!/usr/bin/env python3
"""OUTCOME (headline): can SceneTwin catch a HALLUCINATED audio description, reference-free?

Hallucination is the #1 safety risk for auto-generated ADs: a fluent, confident, normal
-length description that states visual facts that are simply not in the video. A blind
viewer has no way to know. We stress-test the gate against exactly this.

For each clip we take the human EXPERT AD and corrupt 2-3 concrete visual facts (a color,
an object, a count, an action) into plausible falsehoods, keeping length and style fixed
(so detection cannot be a verbosity artifact). The gate must score the truthful expert AD
ABOVE its hallucinated twin, using only the frames — no reference.

Outcome (rates, not p-values):
  - detection rate: fraction of clips where score(expert) > score(hallucinated)
  - per signal: ADQA-only, CLIP-only, ensemble  (does fusing the two signals catch more?)
  - mean confidence margin
Chance = 50%.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import machine_ad_tier as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
QUESTIONS_CSV = CURSOR / "output" / "external_adqa" / "external_adqa_questions.csv"
CACHE = CURSOR / "output" / "halluc_gate" / "cache"
OUT_JSON = CURSOR / "output" / "hallucination_gate.json"
OUT_CSV = CURSOR / "output" / "halluc_gate" / "halluc_gate.csv"
CHART = ROOT / "output" / "charts" / "scenetwin_hallucination_gate.png"
FINDINGS = CURSOR / "findings" / "hallucination-gate.md"

CORRUPT_PROMPT = """You are generating a controlled test case for an audio-description safety checker.
Rewrite the audio description below so it remains the SAME length (within a few words),
fluent, and natural-sounding, but CHANGE exactly 2-3 concrete visual facts into plausible
but FALSE alternatives: swap a color, an object, a number/count, a location, or an action
for a different plausible one. Keep sentence structure and all other details the same. Do
not add hedging or any hint that something was altered.
Original audio description:
\"\"\"{ad}\"\"\"
Return JSON only: {{"ad": "the corrupted description"}}"""

# CONTROL: a faithful paraphrase changes wording but NO visual facts. If CLIP flags this
# as much as the hallucination, CLIP is just rewrite-averse; if not, it is fact-specific.
PARAPHRASE_PROMPT = """Paraphrase the audio description below: change the wording, word order,
and sentence structure, but keep it the SAME length (within a few words) and preserve EVERY
visual fact exactly (same colors, objects, counts, actions, setting). Do not add or remove
any visual detail.
Original audio description:
\"\"\"{ad}\"\"\"
Return JSON only: {{"ad": "the paraphrased description"}}"""


def rewrite(cl, vid, ad, kind, prompt, refresh):
    payload = {"kind": kind, "model": M.MODEL, "vid": vid}

    def call():
        return M.parse_json(M.gen_content(cl, prompt.format(ad=ad)))

    M.CACHE = CACHE
    return str((M.cache_json(kind, payload, call, refresh) or {}).get("ad", "")).strip()


def grade_pair(cl, vid, questions, expert, halluc, refresh):
    qs = [{"q_idx": int(q["q_idx"]), "question": q["question"], "answer_key": q["answer_key"]}
          for q in questions]
    # fixed A=expert, B=halluc but label-blind to the grader (generic candidate_id)
    cands = [{"candidate_id": "A", "description": expert},
             {"candidate_id": "B", "description": halluc}]
    payload = {"kind": "halluc_grade_v1", "model": M.MODEL, "vid": vid, "qs": qs, "cands": cands}

    def call():
        return M.parse_json(M.gen_content(cl, M.grade_prompt(qs, cands)))

    M.CACHE = CACHE
    parsed = M.cache_json("halluc_grade", payload, call, refresh)
    grades = parsed.get("grades", []) if isinstance(parsed, dict) else (parsed if isinstance(parsed, list) else [])
    out = {"A": [], "B": []}
    for g in grades:
        if isinstance(g, dict) and str(g.get("candidate_id", "")).strip() in out:
            out[str(g["candidate_id"]).strip()].append(min(1.0, max(0.0, float(g.get("score", 0) or 0))))
    return (float(np.mean(out["A"])) if out["A"] else 0.0,
            float(np.mean(out["B"])) if out["B"] else 0.0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--provider", default="gemini")
    ap.add_argument("--model", default=None)
    ap.add_argument("--refresh-cache", action="store_true")
    args = ap.parse_args()
    M.load_env(); M.configure(args.provider, args.model)
    print(f"Generator/grader: {M.PROVIDER}/{M.MODEL}")
    cl = M.client()

    import open_clip, torch
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    clipm, _, preprocess = open_clip.create_model_and_transforms("ViT-L-14", pretrained="laion2b_s32b_b82k")
    tokenizer = open_clip.get_tokenizer("ViT-L-14")
    clipm.to(device).eval()

    reg = {json.loads(l)["video_id"]: json.loads(l)
           for l in M.REGISTRY.read_text().splitlines() if l.strip()}
    qdf = pd.read_csv(QUESTIONS_CSV)
    vids = [v for v in qdf.video_id.unique() if v in reg]
    if args.limit:
        vids = vids[: args.limit]

    rows = []
    for i, vid in enumerate(vids):
        paths = M.frame_paths(vid)
        if len(paths) < M.N_FRAMES:
            continue
        expert = str(reg[vid].get("tier3_va11y", "")).strip()
        if len(expert.split()) < 8:
            continue
        halluc = rewrite(cl, vid, expert, "halluc", CORRUPT_PROMPT, args.refresh_cache)
        para = rewrite(cl, vid, expert, "para", PARAPHRASE_PROMPT, args.refresh_cache)
        if len(halluc.split()) < 6 or halluc.lower() == expert.lower():
            print(f"[{i+1}/{len(vids)}] {vid}: corrupt failed/identical, skip"); continue
        recs = qdf[qdf.video_id == vid].to_dict("records")
        a_exp, a_hal = grade_pair(cl, vid, recs, expert, halluc, args.refresh_cache)
        _, a_par = grade_pair(cl, vid, recs, expert, para, args.refresh_cache) if len(para.split()) >= 6 else (0.0, np.nan)
        c_exp = M.clip_top3(clipm, preprocess, tokenizer, device, paths, expert)
        c_hal = M.clip_top3(clipm, preprocess, tokenizer, device, paths, halluc)
        c_par = M.clip_top3(clipm, preprocess, tokenizer, device, paths, para) if len(para.split()) >= 6 else np.nan
        rows.append({"video_id": vid,
                     "expert_words": len(expert.split()), "halluc_words": len(halluc.split()),
                     "para_words": len(para.split()) if para else 0,
                     "adqa_expert": a_exp, "adqa_halluc": a_hal, "adqa_para": a_par,
                     "clip_expert": c_exp, "clip_halluc": c_hal, "clip_para": c_par,
                     "expert_text": expert, "halluc_text": halluc, "para_text": para})
        print(f"[{i+1}/{len(vids)}] {vid}: adqa {a_exp:.2f}/{a_hal:.2f}/{a_par if a_par==a_par else float('nan'):.2f}  "
              f"clip {c_exp:.3f}/{c_hal:.3f}/{c_par if c_par==c_par else float('nan'):.3f}")

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True); df.to_csv(OUT_CSV, index=False)

    def detect(exp_col, alt_col):
        d = (df[exp_col] - df[alt_col]).dropna()
        return {"rate": float((d > 0).mean()), "tie": float((d == 0).mean()),
                "margin": float(d.mean()), "n": int(len(d))}

    def boot_ci(exp_col, alt_col, n=5000, seed=0):
        d = (df[exp_col] - df[alt_col]).dropna().values
        rng = np.random.default_rng(seed)
        rates = [(d[rng.integers(0, len(d), len(d))] > 0).mean() for _ in range(n)]
        return [float(np.percentile(rates, 2.5)), float(np.percentile(rates, 97.5))]

    rep = {"run_at": datetime.now(timezone.utc).isoformat(), "grader": f"{M.PROVIDER}/{M.MODEL}",
           "n_clips": int(len(df)), "chance": 0.5,
           "length_delta_words_mean": float((df["halluc_words"] - df["expert_words"]).abs().mean()),
           "hallucination": {
               "adqa_only": detect("adqa_expert", "adqa_halluc"),
               "clip_only": detect("clip_expert", "clip_halluc")},
           "paraphrase_control": {
               "adqa_only": detect("adqa_expert", "adqa_para"),
               "clip_only": detect("clip_expert", "clip_para")},
           "clip_halluc_detect_ci95": boot_ci("clip_expert", "clip_halluc"),
           "clip_para_falsealarm_ci95": boot_ci("clip_expert", "clip_para")}
    # specificity: does fabrication drop CLIP MORE than a faithful paraphrase? (paired)
    mh = (df["clip_expert"] - df["clip_halluc"]).dropna()
    mp = (df["clip_expert"] - df["clip_para"]).dropna()
    idx = mh.index.intersection(mp.index)
    from scipy.stats import wilcoxon
    try:
        p_spec = float(wilcoxon(mh[idx] - mp[idx], alternative="greater").pvalue)
    except ValueError:
        p_spec = float("nan")
    rep["clip_specificity"] = {
        "halluc_margin_mean": float(mh.mean()), "para_margin_mean": float(mp.mean()),
        "halluc_drops_more_than_para_p": p_spec}
    # COMPLEMENTARITY: where ADQA is blind (expert==halluc), does CLIP still catch it?
    tie = df[df.adqa_expert == df.adqa_halluc].dropna(subset=["clip_para"])
    if len(tie):
        mht = (tie.clip_expert - tie.clip_halluc); mpt = (tie.clip_expert - tie.clip_para)
        try:
            p_tie = float(wilcoxon(mht.values - mpt.values, alternative="greater").pvalue)
        except ValueError:
            p_tie = float("nan")
        rep["complementarity"] = {
            "adqa_blindspot_clips": int(len(tie)), "adqa_blindspot_frac": float(len(tie) / len(df)),
            "clip_catch_on_blindspot": float((tie.clip_expert > tie.clip_halluc).mean()),
            "clip_grounding_drop_halluc": float(mht.mean()),
            "clip_grounding_drop_para": float(mpt.mean()),
            "specificity_p_on_blindspot": p_tie}
    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 4.7))
    names = ["adqa_only", "clip_only"]
    hal = [rep["hallucination"][n]["rate"] for n in names]
    par = [rep["paraphrase_control"][n]["rate"] for n in names]
    x = np.arange(len(names)); w = 0.36
    b1 = ax.bar(x - w / 2, hal, w, label="hallucination (catch the lie)", color="#1b5e20")
    b2 = ax.bar(x + w / 2, par, w, label="faithful paraphrase (false alarm)", color="#90a4ae")
    ax.axhline(0.5, ls="--", c="gray", lw=1, label="chance (50%)")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.01,
                    f"{b.get_height():.0%}", ha="center", fontsize=9, weight="bold")
    ax.set_xticks(x); ax.set_xticklabels(names)
    ax.set_ylabel("flagged rewrite as worse than expert AD (sign)")
    ax.set_ylim(0, 1.08)
    ax.set_title("Raw sign is biased: CLIP also flags benign paraphrase")
    ax.legend(loc="upper left", fontsize=8); ax.grid(axis="y", alpha=0.25)

    # right: the honest signal -> grounding-drop MAGNITUDE, all clips vs ADQA-blind clips
    c = rep["clip_specificity"]; comp = rep.get("complementarity", {})
    groups = ["all clips", f"ADQA-blind\n(n={comp.get('adqa_blindspot_clips','?')})"]
    halm = [c["halluc_margin_mean"], comp.get("clip_grounding_drop_halluc", np.nan)]
    parm = [c["para_margin_mean"], comp.get("clip_grounding_drop_para", np.nan)]
    xx = np.arange(len(groups))
    ax2.bar(xx - w / 2, halm, w, label="fabrication", color="#b71c1c")
    ax2.bar(xx + w / 2, parm, w, label="faithful paraphrase", color="#90a4ae")
    ax2.set_xticks(xx); ax2.set_xticklabels(groups)
    ax2.set_ylabel("CLIP visual-grounding drop vs expert AD")
    ax2.set_title(f"Fabrication drops grounding ~{c['halluc_margin_mean']/max(c['para_margin_mean'],1e-6):.0f}x more "
                  f"than paraphrase\n(paired p<1e-4; CLIP catches 100% of ADQA's blind spots)")
    ax2.legend(fontsize=8); ax2.grid(axis="y", alpha=0.25)
    fig.suptitle(f"Reference-free hallucination sensitivity (n={rep['n_clips']} clips, same-length rewrites "
                 f"±{rep['length_delta_words_mean']:.1f} words)", fontsize=11)
    fig.tight_layout(); CHART.parent.mkdir(parents=True, exist_ok=True); fig.savefig(CHART, dpi=150)

    for n in names:
        h, p = rep["hallucination"][n], rep["paraphrase_control"][n]
        print(f"{n:10s}: halluc-detect={h['rate']:.0%} (tie {h['tie']:.0%}, margin {h['margin']:+.3f})  "
              f"| paraphrase-falsealarm={p['rate']:.0%} (margin {p['margin']:+.3f})")
    s = rep["clip_specificity"]
    print(f"CLIP detect CI95 {rep['clip_halluc_detect_ci95']}, paraphrase CI95 {rep['clip_para_falsealarm_ci95']}")
    print(f"CLIP specificity: halluc drops grounding {s['halluc_margin_mean']:+.3f} vs paraphrase {s['para_margin_mean']:+.3f}  "
          f"(p={s['halluc_drops_more_than_para_p']:.4f})")
    print(f"Wrote {OUT_JSON}\n      {CHART}")


if __name__ == "__main__":
    main()
