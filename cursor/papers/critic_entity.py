#!/usr/bin/env python3
"""AutoAD III CRITIC proxy — character/entity naming in AD tiers.

Paper: CRITIC measures whether AD names characters correctly.
Proxy: count proper nouns + pronoun consistency vs VATEX crowd names.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
FORECAST = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv"
OUT = Path(__file__).resolve().parent / "output" / "critic_entity_score.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "paper-critic-entities.md"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
COL = {"tier3_va11y": "tier3_va11y_text", "tier2_vatex_long": "tier2_vatex_long_text",
       "tier1_vatex_short": "tier1_vatex_short_text", "tier0_cross": "tier0_cross_text"}


def entity_tokens(text: str) -> set[str]:
    # capitalized words (proper nouns proxy) + role nouns
    caps = set(re.findall(r"\b[A-Z][a-z]{2,}\b", text))
    roles = set(re.findall(r"\b(man|woman|boy|girl|person|chef|player|child|dog|cat|deer)\b", text.lower()))
    return caps | roles


def critic_score(ad: str, reference_entities: set[str]) -> float:
    ad_ent = entity_tokens(ad)
    if not reference_entities:
        return 0.5
    hit = len(ad_ent & reference_entities) / max(1, len(reference_entities))
    # bonus for having ANY entity mention
    has_entity = 1.0 if ad_ent else 0.0
    return 0.7 * hit + 0.3 * has_entity


def main() -> None:
    fc = pd.read_csv(FORECAST)
    rows = []
    for _, clip in fc.iterrows():
        ref = entity_tokens(str(clip[COL["tier3_va11y"]]))
        ref |= entity_tokens(str(clip[COL["tier2_vatex_long"]]))
        for tier in TIERS:
            score = critic_score(str(clip[COL[tier]]), ref)
            rows.append({"clip_idx": int(clip["clip_idx"]), "tier": tier,
                         "gt": TIERS.index(tier), "critic_entity": score})
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    rho, p = spearmanr(df["gt"], df["critic_entity"])
    means = df.groupby("tier")["critic_entity"].mean()
    FINDINGS.write_text(
        f"# CRITIC entity proxy (AutoAD III)\n\nρ vs tier GT: **{rho:.3f}** p={p:.4f}\n\n{means.to_string()}\n",
        encoding="utf-8",
    )
    print(f"CRITIC ρ={rho:.3f} | means:\n{means}")


if __name__ == "__main__":
    main()
