"""Cross-judge hardening: re-grade the full-clip gap-targeted vs baseline ADs
with GPT-5 (different model family from the Claude-Haiku generator), to kill the
same-family-bias critique. Reports BOTH the overall ADQA delta and the surgical
matched/unmatched split under the new judge.
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
from scenetwin_roi_content_profile import lexical_profile  # noqa: E402

CAND = ROOT / "cursor/research/output" / os.environ.get(
    "GAP_OUT", "tribe_gap_targeted_external_full_scores.csv")
QCSV = ROOT / "cursor/output/external_adqa/external_adqa_questions.csv"
OUT = ROOT / "cursor/research/output" / os.environ.get(
    "CJ_OUT", "tribe_crossjudge_gpt5_perq.csv")
PRESC = ["motion_action", "scene_spatial", "face_character", "object_body", "visual_form"]


def load_dotenv():
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def gpt5_grade(prompt):
    from openai import OpenAI
    c = OpenAI()
    r = c.chat.completions.create(model="gpt-5",
        messages=[{"role": "user", "content": prompt}], max_completion_tokens=6000)
    t = r.choices[0].message.content.strip()
    import re
    t = re.sub(r"^```(?:json)?|```$", "", t.strip()).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.S)
        return json.loads(m.group(0)) if m else {"grades": []}


def q_type(question, evidence):
    prof = lexical_profile(f"{question} {evidence}")
    presc = {k: prof.get(k, 0.0) for k in PRESC}
    return max(presc, key=presc.get) if max(presc.values()) > 0 else None


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
        qs = qdf[qdf.video_id == vid].sort_values("q_idx")
        questions = [{"q_idx": int(r.q_idx), "question": r.question, "answer_key": r.answer_key,
                      "required_visual_evidence": str(r.required_visual_evidence).split("; "),
                      "importance": r.importance} for r in qs.itertuples()]
        if not questions:
            continue
        tribe_type = Counter(sub.dominant_type).most_common(1)[0][0]
        qt = {int(r.q_idx): q_type(r.question, str(r.required_visual_evidence)) for r in qs.itertuples()}
        conds = ["baseline", "gap_targeted"]; rng.shuffle(conds)
        idmap = {"A": conds[0], "B": conds[1]}
        anon = [{"candidate_id": c, "description": desc[idmap[c]]} for c in ["A", "B"]]
        try:
            parsed = gpt5_grade(s4.grade_prompt(questions, anon))
        except Exception as e:
            print("  fail", vid, e); continue
        for g in parsed.get("grades", []):
            cid = str(g.get("candidate_id", "")).strip()
            if cid not in idmap:
                continue
            qi = int(g.get("q_idx", -1))
            rows.append({"video_id": vid, "q_idx": qi, "condition": idmap[cid],
                         "score": min(1.0, max(0.0, float(g.get("score", 0) or 0))),
                         "matched": int(qt.get(qi) == tribe_type)})
        if (i + 1) % 15 == 0:
            print(f"  {i+1}/{len(vids)}")
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    # overall clip-level delta
    clip = df.groupby(["video_id", "condition"]).score.mean().reset_index()
    cp = clip.pivot_table(index="video_id", columns="condition", values="score").dropna()
    d = cp["gap_targeted"] - cp["baseline"]
    pp = wilcoxon(cp["gap_targeted"], cp["baseline"], alternative="greater").pvalue
    print(f"\n=== GPT-5 JUDGE (cross-family), {df.video_id.nunique()} clips ===")
    print(f"  OVERALL: base={cp['baseline'].mean():.3f} gap={cp['gap_targeted'].mean():.3f} "
          f"delta={d.mean():+.3f} d={d.mean()/d.std():.2f} {int((d>0).sum())}W/{int((d<0).sum())}L p={pp:.4f}")
    # surgical split
    pq = df.pivot_table(index=["video_id", "q_idx", "matched"], columns="condition",
                        values="score").dropna().reset_index()
    pq["lift"] = pq["gap_targeted"] - pq["baseline"]
    for lab, m in [("MATCHED", 1), ("unmatched", 0)]:
        s = pq[pq.matched == m]; dl = s["lift"]
        coh = dl.mean() / dl.std() if dl.std() > 0 else float("nan")
        p = wilcoxon(s["gap_targeted"], s["baseline"], alternative="greater").pvalue if len(s) else float("nan")
        print(f"  {lab:10s} n={len(s):3d} lift={dl.mean():+.3f} d={coh:.2f} p={p:.4f}")
    a, b = pq[pq.matched == 1]["lift"], pq[pq.matched == 0]["lift"]
    print(f"  matched>unmatched MW p={mannwhitneyu(a, b, alternative='greater').pvalue:.4f}")
    print(f"\n  (Haiku judge was: overall +0.080 d=0.47; matched +0.167 d=0.55; unmatched +0.051)")
    print(f"  wrote {OUT}")


if __name__ == "__main__":
    main()
