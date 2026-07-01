"""Does TRIBE-guided AD actually ANSWER visual questions better than baseline?

Turns the gap-targeted controllability result (content coverage shifts to the
predicted type, p<1e-4) into a quality test: blind-grade the generated baseline
vs gap-targeted AD against each external clip's existing ADQA question set.

Per clip:
  - assemble the generated windows (top-2 need windows) into one description per
    condition (same windows for both -> fair paired comparison)
  - blind A/B grade against the clip's 5 ADQA questions (Claude Haiku judge,
    reusing tools/scenetwin_stage4_frame_grounded_adqa.grade_prompt)
  - ADQA score per condition = mean question score
Paired Wilcoxon across clips: gap_targeted > baseline?

NOTE: generated AD covers only the 2 highest-need windows, so absolute ADQA is
below a full pro AD; both conditions cover the SAME windows, so the paired delta
is the valid signal.
"""
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import scenetwin_stage4_frame_grounded_adqa as s4  # noqa: E402

CAND = ROOT / "cursor/research/output" / os.environ.get(
    "GAP_OUT", "tribe_gap_targeted_external_scores.csv")
QCSV = ROOT / "cursor/output/external_adqa/external_adqa_questions.csv"
OUT = ROOT / "cursor/research/output" / os.environ.get(
    "GAP_ADQA_OUT", "tribe_gap_targeted_adqa_scores.csv")
MODEL = "claude-haiku-4-5-20251001"


def load_dotenv():
    p = ROOT / ".env"
    for line in p.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def questions_for(qdf, vid):
    sub = qdf[qdf.video_id == vid].sort_values("q_idx")
    return [{"q_idx": int(r.q_idx), "question": r.question, "answer_key": r.answer_key,
             "required_visual_evidence": str(r.required_visual_evidence).split("; "),
             "importance": r.importance} for r in sub.itertuples()]


def main():
    load_dotenv()
    cand = pd.read_csv(CAND)
    qdf = pd.read_csv(QCSV)
    # assemble per-clip per-condition description from the generated windows
    rng = random.Random(0)
    rows = []
    vids = [v for v in cand.video_id.unique() if (qdf.video_id == v).any()]
    for i, vid in enumerate(vids):
        sub = cand[cand.video_id == vid].sort_values("window")
        desc = {}
        for c in ["baseline", "gap_targeted"]:
            texts = sub[sub.condition == c].ad_text.dropna().astype(str).tolist()
            desc[c] = " ".join(texts).strip()
        if not desc["baseline"] or not desc["gap_targeted"]:
            continue
        questions = questions_for(qdf, vid)
        if not questions:
            continue
        # blind A/B: shuffle mapping per clip
        conds = ["baseline", "gap_targeted"]
        rng.shuffle(conds)
        id_map = {"A": conds[0], "B": conds[1]}
        anon = [{"candidate_id": cid, "description": desc[id_map[cid]]} for cid in ["A", "B"]]
        try:
            parsed = s4.call_anthropic_text(s4.grade_prompt(questions, anon), MODEL)
        except Exception as e:
            print("  grade failed", vid, e); continue
        per = {"A": [], "B": []}
        for g in parsed.get("grades", []):
            cid = str(g.get("candidate_id", "")).strip()
            if cid in per:
                per[cid].append(min(1.0, max(0.0, float(g.get("score", 0) or 0))))
        for cid in ["A", "B"]:
            if per[cid]:
                rows.append({"video_id": vid, "condition": id_map[cid],
                             "adqa": float(np.mean(per[cid])), "n_q": len(per[cid])})
        if (i + 1) % 15 == 0:
            print(f"  {i+1}/{len(vids)} clips graded")
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    piv = df.pivot_table(index="video_id", columns="condition", values="adqa", aggfunc="first").dropna()
    d = piv["gap_targeted"] - piv["baseline"]
    p = wilcoxon(piv["gap_targeted"], piv["baseline"], alternative="greater").pvalue
    print(f"\n=== ADQA: gap-targeted vs baseline AD (blind Haiku judge, n={len(piv)} clips) ===")
    print(f"  baseline ADQA mean    : {piv['baseline'].mean():.4f}")
    print(f"  gap-targeted ADQA mean: {piv['gap_targeted'].mean():.4f}")
    print(f"  mean delta            : {d.mean():+.4f}")
    print(f"  wins/losses/ties      : {int((d>0).sum())}/{int((d<0).sum())}/{int((d==0).sum())}")
    print(f"  Wilcoxon (greater) p  : {p:.4f}")
    # bootstrap CI on the delta
    rngb = np.random.default_rng(0); dd = d.to_numpy()
    boot = [rngb.choice(dd, len(dd), replace=True).mean() for _ in range(5000)]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    print(f"  95% bootstrap CI delta: [{lo:+.4f}, {hi:+.4f}]")
    print(f"  wrote {OUT}")


if __name__ == "__main__":
    main()
