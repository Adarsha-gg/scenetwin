#!/usr/bin/env python3
"""CoAD repetition metrics (arxiv 2510.25440) — penalize redundant AD sequences.

Tests whether tier3 pro AD is more redundant than VATEX tiers (wastes narration time).
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FORECAST = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv"
OUT = Path(__file__).resolve().parent / "output" / "coad_repetition.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "paper-coad-repetition.md"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
COL = {"tier3_va11y": "tier3_va11y_text", "tier2_vatex_long": "tier2_vatex_long_text",
       "tier1_vatex_short": "tier1_vatex_short_text", "tier0_cross": "tier0_cross_text"}


def sentences(text: str) -> list[str]:
    return [s.strip().lower() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 8]


def repetition_rate(text: str) -> dict:
    sents = sentences(text)
    if len(sents) < 2:
        return {"n_sentences": len(sents), "repeated_bigram_rate": 0.0, "self_similarity": 0.0}
    bigrams = []
    for s in sents:
        words = re.findall(r"[a-z]+", s)
        bigrams.extend(zip(words, words[1:]))
    if not bigrams:
        return {"n_sentences": len(sents), "repeated_bigram_rate": 0.0, "self_similarity": 0.0}
    from collections import Counter
    c = Counter(bigrams)
    rep = sum(v - 1 for v in c.values() if v > 1) / len(bigrams)
    # cross-sentence Jaccard redundancy
    sims = []
    for i in range(len(sents)):
        wi = set(re.findall(r"[a-z]{4,}", sents[i]))
        for j in range(i + 1, len(sents)):
            wj = set(re.findall(r"[a-z]{4,}", sents[j]))
            if wi and wj:
                sims.append(len(wi & wj) / len(wi | wj))
    return {
        "n_sentences": len(sents),
        "repeated_bigram_rate": rep,
        "self_similarity": float(sum(sims) / len(sims)) if sims else 0.0,
    }


def main() -> None:
    fc = pd.read_csv(FORECAST)
    rows = []
    for _, clip in fc.iterrows():
        for tier in TIERS:
            m = repetition_rate(str(clip[COL[tier]]))
            rows.append({"clip_idx": int(clip["clip_idx"]), "category": clip["category"],
                         "tier": tier, "gt": TIERS.index(tier), **m})
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    means = df.groupby("tier")[["repeated_bigram_rate", "self_similarity"]].mean()
    # CoAD hypothesis: longer pro AD may be MORE redundant — bad for BLV
    t3_rep = means.loc["tier3_va11y", "self_similarity"]
    t1_rep = means.loc["tier1_vatex_short", "self_similarity"]
    FINDINGS.write_text(
        f"# CoAD repetition (2510.25440)\n\n"
        f"Pro AD self-similarity: **{t3_rep:.3f}** vs short VATEX: **{t1_rep:.3f}**\n\n"
        f"{means.to_string()}\n\n"
        f"If pro > short: longer AD repeats itself — CoAD repetition metric flags this.\n",
        encoding="utf-8",
    )
    print(means)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
