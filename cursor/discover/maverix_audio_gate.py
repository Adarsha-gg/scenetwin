#!/usr/bin/env python3
"""MAVERIX-inspired audio-gated ADQA (AAAI 2026): questions where audio context matters.

Proxy: ADQA questions mentioning speech/sound/music/dialogue vs silent-visual questions.
Score tiers by whether AD text covers audio-relevant evidence when clip is speech-heavy.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
Q = TIMING / "adqa_v4" / "adqa_v4_questions.csv"
GRADES = TIMING / "adqa_v4" / "adqa_v4_grades.csv"
NEED = TIMING / "need" / "coarse_need_windows.csv"
OUT = Path(__file__).resolve().parent / "output" / "maverix_audio_gate.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "discover-maverix-gate.md"

AUDIO_TERMS = re.compile(
    r"\b(?:speech|dialogue|dialog|music|sound|audio|speak|talk|say|voice|laugh|clap|sing)\b",
    re.I,
)


def main() -> None:
    q = pd.read_csv(Q)
    g = pd.read_csv(GRADES)
    need = pd.read_csv(NEED)
    speech = need.groupby("clip_idx")["speech_density"].mean()

    q["audio_gated"] = q["question"].str.contains(AUDIO_TERMS) | q["required_visual_evidence"].str.contains(AUDIO_TERMS, na=False)
    merged = g.merge(q[["clip_idx", "q_idx", "audio_gated", "importance"]], on=["clip_idx", "q_idx"])

    rows = []
    for (cidx, tier), sub in merged.groupby(["clip_idx", "tier"]):
        for gate, label in [(True, "audio_gated"), (False, "visual_only")]:
            s = sub[sub["audio_gated"] == gate]
            if s.empty:
                continue
            rows.append({
                "clip_idx": cidx,
                "tier": tier,
                "gate": label,
                "accuracy": float((s["label"] == "yes").mean()),
                "n": len(s),
                "speech_density": float(speech.get(cidx, 0)),
            })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    # NEW: on speech-heavy clips, does tier3 win MORE on visual-only than audio-gated?
    t3 = df[df["tier"] == "tier3_va11y"]
    heavy = t3[t3["speech_density"] >= 0.7]
    insight = []
    for gate in ["visual_only", "audio_gated"]:
        m = heavy[heavy["gate"] == gate]["accuracy"].mean()
        insight.append(f"{gate}: tier3 mean acc on speech-heavy clips = {m:.3f}")

    # Compare tier3 vs tier1 margin per gate
    margins = []
    for gate in ["visual_only", "audio_gated"]:
        t3a = df[(df["tier"] == "tier3_va11y") & (df["gate"] == gate)].set_index("clip_idx")["accuracy"]
        t1a = df[(df["tier"] == "tier1_vatex_short") & (df["gate"] == gate)].set_index("clip_idx")["accuracy"]
        common = t3a.index.intersection(t1a.index)
        margin = (t3a[common] - t1a[common]).mean()
        margins.append((gate, margin))

    FINDINGS.write_text(
        "# MAVERIX audio-gated ADQA\n\n"
        + "\n".join(f"- {x}" for x in insight)
        + "\n\n## tier3−tier1 margin by gate\n"
        + "\n".join(f"- {g}: {m:.3f}" for g, m in margins)
        + "\n\n**If audio-gated margin is lower:** AD eval must use AV integration, not text-only ADQA.\n",
        encoding="utf-8",
    )
    print("\n".join(insight))
    for g, m in margins:
        print(f"margin {g}: {m:.3f}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
