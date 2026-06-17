#!/usr/bin/env python3
"""OUTCOME test: used as a re-ranker, does SceneTwin pick a BETTER audio description?

Not a correlation — a deployment outcome. For each clip we generate N candidate ADs
(same instruction, temperature for natural diversity), score each with SceneTwin
(ADQA + CLIP), and pick the top-1. We then ask whether the picked AD is actually
better, measured by an INDEPENDENT signal SceneTwin never sees: semantic similarity to
the human EXPERT AD (all-MiniLM-L6-v2). Selection signal (frame questions + visual
grounding) != evaluation signal (text similarity to expert), so it is not circular.

Outcome reported as effect, not just p:
  - sim(top-1) vs sim(random pick = mean candidate) vs sim(oracle = best candidate)
  - win-rate: fraction of clips where top-1 beats a random pick
  - how much of the oracle gap the re-ranker captures

BUILT-IN RED TEAM (verbosity is the recurring trap):
  - is top-1 just the LONGEST candidate? report selection-vs-length correlation
  - does the gain survive when the baseline is the LENGTH-MATCHED candidate (not random)?
  - candidate spread (no spread => nothing to rerank)
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
from scipy.stats import spearmanr, wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parent))
import machine_ad_tier as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
EXT_DIR = CURSOR / "data" / "external_clips"
QUESTIONS_CSV = CURSOR / "output" / "external_adqa" / "external_adqa_questions.csv"
CACHE = CURSOR / "output" / "best_of_n" / "cache"
OUT_JSON = CURSOR / "output" / "best_of_n_rerank.json"
OUT_CSV = CURSOR / "output" / "best_of_n" / "best_of_n_candidates.csv"
CHART = ROOT / "output" / "charts" / "scenetwin_best_of_n.png"
FINDINGS = CURSOR / "findings" / "best-of-n-rerank.md"

GEN_PROMPT = """You are an automated audio-description system for blind and low-vision viewers.
Look only at the attached video frames from a ~10s clip. Write ONE audio description of
35-55 words covering the main subject, key action, setting, and important objects. Be
factual; describe only what is visible. Do not address the viewer or mention frames.
Return JSON only: {"ad": "your description"}"""


def gen_candidate(cl, vid, imgs, k, refresh):
    payload = {"kind": "bon_cand_v1", "model": M.MODEL, "vid": vid, "k": k}

    def call():
        from google.genai import types
        cfg = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.95)
        try:
            r = cl.models.generate_content(model=M.MODEL, contents=[GEN_PROMPT, *imgs], config=cfg)
            return M.parse_json(r.text)
        except Exception:
            return {}

    M.CACHE = CACHE
    r = M.cache_json(f"cand{k}", payload, call, refresh)
    return str((r or {}).get("ad", "")).strip()


def grade_candidates(cl, vid, questions, cand_map, refresh):
    """ADQA-grade N candidates (A..) against frame questions in one call."""
    qs = [{"q_idx": int(q["q_idx"]), "question": q["question"], "answer_key": q["answer_key"]}
          for q in questions]
    ids = [chr(65 + i) for i in range(len(cand_map))]
    keys = list(cand_map)
    id_to_key = dict(zip(ids, keys))
    cands = [{"candidate_id": cid, "description": cand_map[id_to_key[cid]]} for cid in ids]
    payload = {"kind": "bon_grade_v1", "model": M.MODEL, "vid": vid, "qs": qs, "cands": cands}

    def call():
        return M.parse_json(M.gen_content(cl, M.grade_prompt(qs, cands)))

    M.CACHE = CACHE
    parsed = M.cache_json("bon_grade", payload, call, refresh)
    grades = parsed.get("grades", []) if isinstance(parsed, dict) else (parsed if isinstance(parsed, list) else [])
    out = {k: [] for k in keys}
    for g in grades:
        if isinstance(g, dict) and str(g.get("candidate_id", "")).strip() in id_to_key:
            out[id_to_key[str(g["candidate_id"]).strip()]].append(
                min(1.0, max(0.0, float(g.get("score", 0) or 0))))
    return {k: (float(np.mean(v)) if v else 0.0) for k, v in out.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--provider", default="gemini")
    ap.add_argument("--model", default=None)
    ap.add_argument("--refresh-cache", action="store_true")
    args = ap.parse_args()
    M.load_env(); M.configure(args.provider, args.model)
    print(f"Generator/grader: {M.PROVIDER}/{M.MODEL}  N={args.n}")
    cl = M.client()

    import open_clip, torch
    from sentence_transformers import SentenceTransformer
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    clipm, _, preprocess = open_clip.create_model_and_transforms("ViT-L-14", pretrained="laion2b_s32b_b82k")
    tokenizer = open_clip.get_tokenizer("ViT-L-14")
    clipm.to(device).eval()
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    qdf = pd.read_csv(QUESTIONS_CSV)
    vids = [v for v in qdf.video_id.unique() if (EXT_DIR / v / "metadata.json").exists()][: args.limit]

    rows = []
    for i, vid in enumerate(vids):
        paths = M.frame_paths(vid)
        if len(paths) < M.N_FRAMES:
            continue
        meta = json.loads((EXT_DIR / vid / "metadata.json").read_text())
        expert = meta.get("tier3_va11y", "")
        imgs = [Image.open(p).convert("RGB") for p in paths]
        cands = {}
        for k in range(args.n):
            ad = gen_candidate(cl, vid, imgs, k, args.refresh_cache)
            if len(ad.split()) >= 8:
                cands[f"c{k}"] = ad
        if len(cands) < 2:
            print(f"[{i+1}/{len(vids)}] {vid}: <2 candidates, skip"); continue
        adqa = grade_candidates(cl, vid, qdf[qdf.video_id == vid].to_dict("records"), cands, args.refresh_cache)
        # independent expert-similarity
        texts = list(cands.values())
        emb = embedder.encode([expert] + texts, normalize_embeddings=True)
        sims = (emb[1:] @ emb[0])
        for (k, ad), s in zip(cands.items(), sims):
            cl3 = M.clip_top3(clipm, preprocess, tokenizer, device, paths, ad)
            rows.append({"video_id": vid, "cand": k, "ad": ad, "n_words": len(ad.split()),
                         "adqa": adqa.get(k, 0.0), "clip": cl3, "expert_sim": float(s)})
        print(f"[{i+1}/{len(vids)}] {vid}: {len(cands)} cands, expert_sim spread "
              f"{sims.min():.2f}-{sims.max():.2f}")

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True); df.to_csv(OUT_CSV, index=False)

    # within-clip normalize + ensemble selection score
    g = df.groupby("video_id", group_keys=False)
    df["adqa_n"] = g["adqa"].apply(lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else s * 0 + 0.5)
    df["clip_n"] = g["clip"].apply(lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else s * 0 + 0.5)
    df["ens"] = 0.5 * df["adqa_n"] + 0.5 * df["clip_n"]

    def outcome(score_col):
        top, rnd, orc, bot, lenmatch, sel_words, n = [], [], [], [], [], [], 0
        wins = 0
        for vid, c in df.groupby("video_id"):
            c = c.reset_index(drop=True)
            if len(c) < 2:
                continue
            n += 1
            ti = c[score_col].idxmax()
            top.append(c.loc[ti, "expert_sim"])
            bot.append(c.loc[c[score_col].idxmin(), "expert_sim"])
            rnd.append(c["expert_sim"].mean())          # expected random pick
            orc.append(c["expert_sim"].max())           # oracle
            sel_words.append(c.loc[ti, "n_words"])
            # length-matched baseline: candidate whose length is closest to the picked one,
            # excluding the picked one -> isolates "did we pick a better AD, not just longer"
            others = c.drop(index=ti)
            lm = (others["n_words"] - c.loc[ti, "n_words"]).abs().idxmin()
            lenmatch.append(others.loc[lm, "expert_sim"])
            wins += int(c.loc[ti, "expert_sim"] > c["expert_sim"].mean())
        top, rnd, orc, bot, lenmatch = map(np.array, (top, rnd, orc, bot, lenmatch))
        gap = orc - rnd
        captured = float(np.mean((top - rnd) / np.where(gap > 1e-9, gap, np.nan)))
        try:
            p_rnd = float(wilcoxon(top - rnd, alternative="greater").pvalue)
        except ValueError:
            p_rnd = float("nan")
        return {
            "n_clips": n,
            "sim_top1": float(top.mean()), "sim_random": float(rnd.mean()),
            "sim_oracle": float(orc.mean()), "sim_bottom1": float(bot.mean()),
            "sim_length_matched_baseline": float(lenmatch.mean()),
            "gain_over_random": float((top - rnd).mean()),
            "gain_over_length_matched": float((top - lenmatch).mean()),
            "oracle_gap_captured_frac": captured,
            "win_rate_vs_random": wins / n,
            "p_vs_random": p_rnd,
            "selection_vs_length_rho": float(spearmanr(df[score_col], df["n_words"])[0]),
            "mean_selected_words": float(np.mean(sel_words)),
        }

    rep = {"run_at": datetime.now(timezone.utc).isoformat(), "grader": f"{M.PROVIDER}/{M.MODEL}",
           "n_candidates_per_clip": args.n,
           "ensemble": outcome("ens"), "adqa_only": outcome("adqa_n"),
           "clip_only": outcome("clip_n"),
           "mean_candidate_sim_spread": float(df.groupby("video_id")["expert_sim"].agg(lambda s: s.max() - s.min()).mean())}
    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    e = rep["ensemble"]
    bars = {"bottom-1\n(worst pick)": e["sim_bottom1"], "random\npick": e["sim_random"],
            "length-matched\nbaseline": e["sim_length_matched_baseline"],
            "SceneTwin\ntop-1": e["sim_top1"], "oracle\n(best pick)": e["sim_oracle"]}
    colors = ["#c62828", "#90a4ae", "#ff9800", "#1b5e20", "#000000"]
    ax.bar(range(len(bars)), list(bars.values()), color=colors)
    ax.set_xticks(range(len(bars))); ax.set_xticklabels(list(bars), fontsize=8)
    ax.set_ylabel("similarity to expert AD (independent eval)")
    lo = min(bars.values()); ax.set_ylim(lo - 0.03, max(bars.values()) + 0.02)
    ax.set_title(f"Best-of-{args.n} re-ranking outcome (n={e['n_clips']} clips)\n"
                 f"top-1 beats random by {e['gain_over_random']:+.3f}, "
                 f"length-matched by {e['gain_over_length_matched']:+.3f}, win-rate {e['win_rate_vs_random']:.0%}")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(); CHART.parent.mkdir(parents=True, exist_ok=True); fig.savefig(CHART, dpi=150)

    for name in ("ensemble", "adqa_only", "clip_only"):
        r = rep[name]
        print(f"\n{name}: top1={r['sim_top1']:.3f} random={r['sim_random']:.3f} "
              f"lenmatch={r['sim_length_matched_baseline']:.3f} oracle={r['sim_oracle']:.3f}")
        print(f"   gain/random={r['gain_over_random']:+.3f} gain/lenmatch={r['gain_over_length_matched']:+.3f} "
              f"win={r['win_rate_vs_random']:.0%} captured={r['oracle_gap_captured_frac']:.0%} "
              f"sel-len-rho={r['selection_vs_length_rho']:.2f} p={r['p_vs_random']:.3f}")
    print(f"\ncandidate sim spread (mean max-min per clip): {rep['mean_candidate_sim_spread']:.3f}")
    print(f"Wrote {OUT_JSON}\n      {CHART}")


if __name__ == "__main__":
    main()
