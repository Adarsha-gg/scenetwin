"""Is the gap-targeted ADQA lift SURGICAL?

Hypothesis: TRIBE-guided AD improves ADQA specifically on questions about the
visual content TRIBE flagged as high-need for that clip, and barely elsewhere.
If so, the clip-wide +0.080 average is diluting a much larger effect on the
matched subset -> "TRIBE predicts which visual facts the AD will miss and
targeting recovers exactly those."

Re-grades the full-clip ADs (tribe_gap_targeted_external_full_scores.csv) blind,
SAVING PER-QUESTION scores, classifies each question's content type via the
content lexicon, and compares the gap-targeted lift on TRIBE-matched vs
unmatched questions.
"""
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import scenetwin_stage4_frame_grounded_adqa as s4  # noqa: E402
from scenetwin_roi_content_profile import CONTENT_TYPES, lexical_profile  # noqa: E402

CAND = ROOT / "cursor/research/output/tribe_gap_targeted_external_full_scores.csv"
QCSV = ROOT / "cursor/output/external_adqa/external_adqa_questions.csv"
OUT = ROOT / "cursor/research/output/tribe_surgical_adqa_perq.csv"
MODEL = "claude-haiku-4-5-20251001"
PRESC = ["motion_action", "scene_spatial", "face_character", "object_body", "visual_form"]


def load_dotenv():
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def q_content_type(question, evidence):
    """Classify what visual content a question asks about (not its answer)."""
    prof = lexical_profile(f"{question} {evidence}")
    presc = {k: prof.get(k, 0.0) for k in PRESC}
    if max(presc.values()) <= 0:
        return None
    return max(presc, key=presc.get)


def clip_tribe_type(sub):
    """The clip's dominant TRIBE need type = modal dominant_type across windows."""
    return Counter(sub.dominant_type).most_common(1)[0][0]


def main():
    load_dotenv()
    cand = pd.read_csv(CAND)
    qdf = pd.read_csv(QCSV)
    rng = random.Random(0)
    rows = []
    vids = [v for v in cand.video_id.unique() if (qdf.video_id == v).any()]
    for i, vid in enumerate(vids):
        sub = cand[cand.video_id == vid]
        desc = {c: " ".join(sub[sub.condition == c].sort_values("window").ad_text.dropna().astype(str))
                for c in ["baseline", "gap_targeted"]}
        if not desc["baseline"].strip() or not desc["gap_targeted"].strip():
            continue
        qsub = qdf[qdf.video_id == vid].sort_values("q_idx")
        questions = [{"q_idx": int(r.q_idx), "question": r.question, "answer_key": r.answer_key,
                      "required_visual_evidence": str(r.required_visual_evidence).split("; "),
                      "importance": r.importance} for r in qsub.itertuples()]
        if not questions:
            continue
        tribe_type = clip_tribe_type(sub)
        qtype = {int(r.q_idx): q_content_type(r.question, str(r.required_visual_evidence))
                 for r in qsub.itertuples()}
        conds = ["baseline", "gap_targeted"]; rng.shuffle(conds)
        idmap = {"A": conds[0], "B": conds[1]}
        anon = [{"candidate_id": c, "description": desc[idmap[c]]} for c in ["A", "B"]]
        try:
            parsed = s4.call_anthropic_text(s4.grade_prompt(questions, anon), MODEL)
        except Exception as e:
            print("  fail", vid, e); continue
        for g in parsed.get("grades", []):
            cid = str(g.get("candidate_id", "")).strip()
            if cid not in idmap:
                continue
            qi = int(g.get("q_idx", -1))
            rows.append({"video_id": vid, "q_idx": qi, "condition": idmap[cid],
                         "score": min(1.0, max(0.0, float(g.get("score", 0) or 0))),
                         "tribe_type": tribe_type, "q_type": qtype.get(qi),
                         "matched": int(qtype.get(qi) == tribe_type)})
        if (i + 1) % 15 == 0:
            print(f"  {i+1}/{len(vids)}")
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    # per-question paired lift
    piv = df.pivot_table(index=["video_id", "q_idx", "matched"], columns="condition",
                         values="score", aggfunc="first").dropna().reset_index()
    piv["lift"] = piv["gap_targeted"] - piv["baseline"]
    print(f"\n=== SURGICAL: per-question lift, {df.video_id.nunique()} clips, {len(piv)} questions ===")
    for label, m in [("TRIBE-MATCHED questions", 1), ("unmatched questions", 0)]:
        s = piv[piv.matched == m]
        d = s["lift"]
        coh = d.mean() / d.std() if d.std() > 0 else float("nan")
        try:
            p = wilcoxon(s["gap_targeted"], s["baseline"], alternative="greater").pvalue
        except ValueError:
            p = float("nan")
        print(f"  {label:26s} n={len(s):3d}  base={s['baseline'].mean():.3f} "
              f"gap={s['gap_targeted'].mean():.3f}  lift={d.mean():+.3f}  d={coh:.2f}  p={p:.4f}")
    # matched vs unmatched lift difference
    a = piv[piv.matched == 1]["lift"]; b = piv[piv.matched == 0]["lift"]
    u, pmw = mannwhitneyu(a, b, alternative="greater")
    print(f"\n  matched lift > unmatched lift?  Mann-Whitney p={pmw:.4f}  "
          f"(matched {a.mean():+.3f} vs unmatched {b.mean():+.3f})")
    print(f"  wrote {OUT}")


if __name__ == "__main__":
    main()
