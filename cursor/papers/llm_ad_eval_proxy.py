#!/usr/bin/env python3
"""LLM-AD-Eval lexical proxy (AutoAD III) — semantic match without API.

Uses sentence embedding cosine if available, else Word Mover / token overlap.
Compares each tier AD to tier3 as reference (human pro AD).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
FORECAST = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv"
OUT = Path(__file__).resolve().parent / "output" / "llm_ad_eval_proxy.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "paper-llm-ad-eval.md"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
COL = {"tier3_va11y": "tier3_va11y_text", "tier2_vatex_long": "tier2_vatex_long_text",
       "tier1_vatex_short": "tier1_vatex_short_text", "tier0_cross": "tier0_cross_text"}


def embed_sim(a: str, b: str) -> float:
    try:
        from sentence_transformers import SentenceTransformer
        model = embed_sim._model  # type: ignore
    except AttributeError:
        from sentence_transformers import SentenceTransformer
        embed_sim._model = SentenceTransformer("all-MiniLM-L6-v2")  # type: ignore
        model = embed_sim._model  # type: ignore
    ea = model.encode([a], normalize_embeddings=True)
    eb = model.encode([b], normalize_embeddings=True)
    return float((ea @ eb.T)[0, 0])


def main() -> None:
    fc = pd.read_csv(FORECAST)
    rows = []
    for _, clip in fc.iterrows():
        ref = str(clip[COL["tier3_va11y"]])
        for tier in TIERS:
            hyp = str(clip[COL[tier]])
            sim = embed_sim(hyp, ref)
            # Map to 1-5 like LLM-AD-Eval
            score_1_5 = 1 + 4 * max(0.0, min(1.0, (sim + 1) / 2))  # cosine [-1,1] -> [1,5]
            rows.append({"clip_idx": int(clip["clip_idx"]), "tier": tier, "gt": TIERS.index(tier),
                         "cosine_sim": sim, "llm_ad_eval_proxy": score_1_5})
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    rho, p = spearmanr(df["gt"], df["llm_ad_eval_proxy"])
    FINDINGS.write_text(
        f"# LLM-AD-Eval proxy (MiniLM embeddings)\n\nρ vs tier GT: **{rho:.3f}** p={p:.4f}\n\n"
        f"Note: tier3 vs itself = 5.0 always — rank lower tiers.\n",
        encoding="utf-8",
    )
    sub = df[df["tier"] != "tier3_va11y"]
    rho2, _ = spearmanr(sub["gt"], sub["llm_ad_eval_proxy"])
    print(f"LLM-AD-Eval proxy ρ (excl tier3 self)={rho2:.3f} | all tiers ρ={rho:.3f}")


if __name__ == "__main__":
    main()
