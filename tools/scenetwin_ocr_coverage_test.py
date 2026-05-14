#!/usr/bin/env python3
"""Need/event-weighted OCR coverage for SceneTwin.

This tests a separate accessibility failure mode: visible text on screen.
TRIBE's accessibility gap and visual-only event score tell us *when* to inspect;
OCR tells us whether the description actually covers readable text that appears
at those important moments.
"""

from __future__ import annotations

import csv
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr


ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
FRAME_ROOT = ROOT / "output" / "scenetwin_need_validation"
TEXT_DIR = DG_DIR / "texts"
NEED_CSV = DG_DIR / "neural_description_need_curve.csv"
EVENT_CSV = DG_DIR / "neural_event_test_results.csv"
OUT_CSV = DG_DIR / "ocr_coverage_test_results.csv"
OUT_SUMMARY = DG_DIR / "ocr_coverage_test_summary.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-ocr-coverage-test.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-ocr-coverage-test.md"

TIER_KEYS = ["tier3_va11y", "tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]
GT = {"tier3_va11y": 3, "tier2_vatex_long": 2, "tier1_vatex_short": 1, "tier0_cross": 0}
COMPS = ["tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]
MIN_CONF = 20.0
MIN_TOKEN_LEN = 4


def normalize_token(token: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "", token.lower())
    if len(token) > 4 and token.endswith("ing"):
        token = token[:-3]
    elif len(token) > 3 and token.endswith("es"):
        token = token[:-2]
    elif len(token) > 3 and token.endswith("s"):
        token = token[:-1]
    return token


def text_tokens(text: str) -> list[str]:
    return [t for t in (normalize_token(tok) for tok in re.findall(r"[A-Za-z0-9']+", text)) if t]


def has_ordered_phrase(phrase: list[str], haystack: list[str]) -> bool:
    if not phrase or len(phrase) > len(haystack):
        return False
    for i in range(len(haystack) - len(phrase) + 1):
        if haystack[i : i + len(phrase)] == phrase:
            return True
    return False


def run_tesseract_tsv(image_path: Path) -> list[dict[str, str]]:
    result = subprocess.run(
        ["tesseract", str(image_path), "stdout", "--psm", "6", "tsv"],
        check=True,
        capture_output=True,
        text=True,
    )
    return list(csv.DictReader(result.stdout.splitlines(), delimiter="\t"))


def ocr_frame(image_path: Path) -> dict[str, object]:
    rows = run_tesseract_tsv(image_path)
    words = []
    line_words: dict[tuple[str, str, str], list[tuple[int, str]]] = defaultdict(list)
    for row in rows:
        raw = row.get("text", "")
        raw_alnum = re.sub(r"[^a-z0-9]+", "", raw.lower())
        norm = normalize_token(raw)
        if len(raw_alnum) < MIN_TOKEN_LEN or not norm:
            continue
        try:
            conf = float(row.get("conf", "-1"))
        except ValueError:
            conf = -1.0
        if conf < MIN_CONF:
            continue
        word = {
            "token": norm,
            "raw": raw,
            "conf": conf,
            "left": int(float(row.get("left", 0) or 0)),
            "top": int(float(row.get("top", 0) or 0)),
            "width": int(float(row.get("width", 0) or 0)),
            "height": int(float(row.get("height", 0) or 0)),
        }
        words.append(word)
        key = (row.get("block_num", "0"), row.get("par_num", "0"), row.get("line_num", "0"))
        line_words[key].append((word["left"], norm))

    ordered = [w["token"] for w in sorted(words, key=lambda w: (w["top"], w["left"]))]
    lines = []
    for vals in line_words.values():
        tokens = [token for _, token in sorted(vals)]
        if tokens:
            lines.append(tokens)
    frame_phrase = ordered if len(ordered) >= 2 else []
    phrases = lines + ([frame_phrase] if frame_phrase and frame_phrase not in lines else [])
    return {
        "tokens": sorted(set(ordered)),
        "ordered_tokens": ordered,
        "phrases": phrases,
        "raw_text": " ".join(w["raw"] for w in sorted(words, key=lambda w: (w["top"], w["left"]))),
    }


def weighted_average(values: np.ndarray, weights: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    mask = np.isfinite(values) & np.isfinite(weights)
    if not mask.any():
        return float("nan")
    values = values[mask]
    weights = weights[mask]
    if weights.sum() <= 1e-9:
        return float(values.mean())
    return float(np.dot(values, weights) / weights.sum())


def score_description(ocr: dict[str, object], desc: str) -> dict[str, float]:
    tokens = ocr["tokens"]
    phrases = ocr["phrases"]
    if not tokens:
        return {"token_coverage": float("nan"), "phrase_coverage": float("nan"), "ocr_score": float("nan")}

    desc_tokens = text_tokens(desc)
    desc_set = set(desc_tokens)
    token_coverage = sum(1 for token in tokens if token in desc_set) / len(tokens)

    phrase_scores = []
    for phrase in phrases:
        if len(phrase) >= 2:
            phrase_scores.append(float(has_ordered_phrase(phrase, desc_tokens)))
    phrase_coverage = max(phrase_scores) if phrase_scores else token_coverage

    # Token coverage catches paraphrases. Phrase coverage rewards actually reading
    # visible text, not merely mentioning related concepts elsewhere.
    ocr_score = 0.4 * token_coverage + 0.6 * phrase_coverage
    return {
        "token_coverage": float(token_coverage),
        "phrase_coverage": float(phrase_coverage),
        "ocr_score": float(ocr_score),
    }


def evaluate(df: pd.DataFrame, metric: str) -> dict[str, object]:
    valid = df[np.isfinite(df[metric])]
    rho, p_rho = spearmanr(valid["gt"], valid[metric], nan_policy="omit")
    tau, p_tau = kendalltau(valid["gt"], valid[metric], nan_policy="omit")
    out: dict[str, object] = {
        "metric": metric,
        "spearman_rho": float(rho),
        "spearman_p": float(p_rho),
        "kendall_tau": float(tau),
        "kendall_p": float(p_tau),
    }
    wins_total = 0
    pair_total = 0
    for comp in COMPS:
        wins = 0
        total = 0
        for _, group in valid.groupby("clip_idx"):
            t3 = group[group["tier"] == "tier3_va11y"][metric]
            tx = group[group["tier"] == comp][metric]
            if len(t3) and len(tx):
                total += 1
                wins += int(float(t3.iloc[0]) > float(tx.iloc[0]))
        out[f"tier3_gt_{comp}_wins"] = wins
        out[f"tier3_gt_{comp}_total"] = total
        wins_total += wins
        pair_total += total
    out["pairwise_wins"] = wins_total
    out["pairwise_total"] = pair_total
    return out


def main() -> None:
    need = pd.read_csv(NEED_CSV)
    events = pd.read_csv(EVENT_CSV)
    weights = need.merge(
        events[["clip_idx", "t", "visual_event_score", "visual_event_need"]],
        on=["clip_idx", "t"],
        how="left",
    )
    weights["critical_weight"] = np.maximum(weights["need_score"], weights["visual_event_score"].fillna(0))

    ocr_rows = []
    desc_rows = []
    for row in weights.sort_values(["clip_idx", "t"]).itertuples(index=False):
        frame_path = FRAME_ROOT / f"clip_{int(row.clip_idx):02d}_frames" / f"t{int(row.t):02d}.jpg"
        ocr = ocr_frame(frame_path)
        ocr_rows.append(
            {
                "clip_idx": int(row.clip_idx),
                "t": int(row.t),
                "start_s": float(row.start_s),
                "end_s": float(row.end_s),
                "critical_weight": float(row.critical_weight),
                "ocr_tokens": " ".join(ocr["tokens"]),
                "ocr_raw_text": ocr["raw_text"],
            }
        )
        # Treat one-token OCR hits as weak unless a later model confirms them.
        # They are often logos/noise and are less clearly an AD requirement.
        if len(ocr["tokens"]) < 2:
            continue
        for tier in TIER_KEYS:
            desc = (TEXT_DIR / f"clip_{int(row.clip_idx):02d}_{tier}.txt").read_text(encoding="utf-8")
            scores = score_description(ocr, desc)
            desc_rows.append(
                {
                    "clip_idx": int(row.clip_idx),
                    "t": int(row.t),
                    "tier": tier,
                    "gt": GT[tier],
                    "critical_weight": float(row.critical_weight),
                    **scores,
                }
            )

    frame_ocr = pd.DataFrame(ocr_rows)
    scored = pd.DataFrame(desc_rows)
    rows = []
    for clip_idx in sorted(weights["clip_idx"].unique()):
        clip_scored = scored[scored["clip_idx"] == clip_idx]
        for tier in TIER_KEYS:
            tier_scored = clip_scored[clip_scored["tier"] == tier]
            if tier_scored.empty:
                rows.append(
                    {
                        "clip_idx": int(clip_idx),
                        "tier": tier,
                        "gt": GT[tier],
                        "ocr_windows": 0,
                        "weighted_ocr_score": float("nan"),
                        "weighted_token_coverage": float("nan"),
                        "weighted_phrase_coverage": float("nan"),
                    }
                )
                continue
            rows.append(
                {
                    "clip_idx": int(clip_idx),
                    "tier": tier,
                    "gt": GT[tier],
                    "ocr_windows": int(tier_scored["t"].nunique()),
                    "weighted_ocr_score": weighted_average(
                        tier_scored["ocr_score"].to_numpy(), tier_scored["critical_weight"].to_numpy()
                    ),
                    "weighted_token_coverage": weighted_average(
                        tier_scored["token_coverage"].to_numpy(), tier_scored["critical_weight"].to_numpy()
                    ),
                    "weighted_phrase_coverage": weighted_average(
                        tier_scored["phrase_coverage"].to_numpy(), tier_scored["critical_weight"].to_numpy()
                    ),
                }
            )

    out = pd.DataFrame(rows)
    summary = pd.DataFrame(
        [
            evaluate(out, "weighted_ocr_score"),
            evaluate(out, "weighted_token_coverage"),
            evaluate(out, "weighted_phrase_coverage"),
        ]
    ).sort_values(["pairwise_wins", "spearman_rho"], ascending=False)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)

    ocr_windows = frame_ocr[frame_ocr["ocr_tokens"] != ""]
    report = f"""---
title: "SceneTwin OCR Coverage Test"
category: research
tags: [SceneTwin, OCR, TRIBE, audio-description, text-on-screen]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/scenetwin_description_gain/ocr_coverage_test_results.csv
  - output/scenetwin_description_gain/ocr_coverage_test_summary.csv
  - output/scenetwin_description_gain/neural_event_test_results.csv
---

# SceneTwin OCR Coverage Test

## Question

Can SceneTwin catch a failure mode that CLIP/TRIBE alone can miss: readable text appearing on screen?

## Method

1. Use TRIBE `critical_weight = max(AccessibilityGap, VisualOnlyEvent)` to identify important windows.
2. Run Tesseract OCR on the validation frame for each window.
3. Score each description by coverage of OCR tokens and whether the visible phrase appears in-order.

```text
OCRScore = 0.4 * token coverage + 0.6 * ordered phrase coverage
Need/EventWeightedOCR = weighted average over OCR-positive windows
```

## OCR-Positive Windows

{ocr_windows[["clip_idx", "t", "start_s", "end_s", "critical_weight", "ocr_tokens", "ocr_raw_text"]].to_markdown(index=False)}

## Results

{out.to_markdown(index=False)}

## Summary

{summary.to_markdown(index=False)}

## Verdict

This is useful as a specialized content layer, not as a universal description metric. It detects the clip 01 title-card requirement that the neural need curve underweighted: the best description explicitly contains `BURGER EATING`, while shorter same-scene captions only mention eating/burgers generally.

Final stack after this test:

- TRIBE AccessibilityGap: when the viewer needs visual information.
- TRIBE VisualOnlyEvent: secondary trigger for visual transitions/title cards.
- Need-weighted CLIP/PAC-S/SigLIP: whether the description matches important frames.
- OCR coverage: whether visible text is read or paraphrased.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")

    print(out)
    print()
    print(summary)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
