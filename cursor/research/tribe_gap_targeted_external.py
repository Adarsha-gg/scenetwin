"""Scale the gap-targeted AD A/B test to the external corpus (60 clips).

Phase 1 on 2 in-bench clips showed the TRIBE ROI profile steers an LLM:
dominant_keyword_coverage +1.29, Wilcoxon p=0.0026 (21 windows). It was stuck at
2 clips because per-window per-ROI typing needed per-timestep tensors. The
tribe_tensors_all78 dump unblocks all 60 external clips (which carry 4-tier
texts in the registry).

For each external clip's top-need 3s windows:
  - compute per-content-type gap from tensors (ROI mask + ROI_TO_CONTENT)
  - build a gap-targeted prompt (ROI profile + dominant/second instruction) and a
    matched baseline prompt (same visual context, no profile)
  - generate AD with Claude Haiku for both
  - score with the existing lexical scorer (profile_alignment,
    dominant_keyword_coverage) and paired Wilcoxon

Same scorer + same paired design as tools/scenetwin_phase1_score_ad.py.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from scenetwin_roi_content_profile import (  # noqa: E402
    CONTENT_TYPES, ROI_TO_CONTENT, cosine_dict, lexical_counts, lexical_profile)

import tribe_tensors_load as T  # noqa: E402

EXT = ROOT / "cursor" / "data" / "external_clips"
MASK = ROOT / "output" / "scenetwin_description_gain" / "glasser_roi_mask.csv"
OUT = ROOT / "cursor" / "research" / "output" / os.environ.get(
    "GAP_OUT", "tribe_gap_targeted_external_scores.csv")
WINDOW_S = 3.0
MAX_WIN_PER_CLIP = int(os.environ.get("GAP_MAX_WIN", "2"))
PRESCRIPTIVE = ["motion_action", "scene_spatial", "face_character", "object_body", "visual_form"]
EMPHASIS = {
    "motion_action": "describe what moves, who acts, the trajectory and result of action",
    "scene_spatial": "describe the place, layout, and spatial arrangement of objects/people",
    "face_character": "describe visible characters, expression, gaze, attention, social cues",
    "object_body": "describe the salient object or body posture and how it is being used",
    "visual_form": "describe shape, color, framing, lighting, or visual state",
}


def load_dotenv():
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def roi_groups():
    m = pd.read_csv(MASK)
    g = {}
    for roi, sub in m[m.roi != "_unassigned_padding"].groupby("roi"):
        ct = ROI_TO_CONTENT.get(roi)
        if ct:
            g.setdefault(ct, []).append(sub.vertex.to_numpy())
    return {ct: np.concatenate(v) for ct, v in g.items()}


def content_gap(pav, pa, verts):
    a, b = pav[verts].astype(float), pa[verts].astype(float)
    return 1.0 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)


def build_windows(pav, pa, ctv):
    n = min(pav.shape[0], pa.shape[0])
    pav, pa = pav[:n], pa[:n]
    step = 1.5  # ~TR; window assignment by TR index since external duration ~10s
    win = (np.arange(n) * step // WINDOW_S).astype(int)
    rows = []
    for w in np.unique(win):
        mask = win == w
        av_m, a_m = pav[mask].mean(0), pa[mask].mean(0)
        prof = {ct: float(content_gap(av_m, a_m, v)) for ct, v in ctv.items()}
        full = 1.0 - np.dot(av_m, a_m) / (np.linalg.norm(av_m) * np.linalg.norm(a_m) + 1e-9)
        rows.append({"window": int(w),
                     "start_s": round(float(np.where(mask)[0][0] * step), 1),
                     "end_s": round(float((np.where(mask)[0][-1] + 1) * step), 1),
                     "need": float(full), "profile": prof})
    return rows


def make_prompts(win, visual_ctx):
    prof = {ct: win["profile"].get(ct, 0.0) for ct in CONTENT_TYPES}
    presc = sorted(PRESCRIPTIVE, key=lambda c: prof.get(c, 0), reverse=True)
    dom, sec = presc[0], presc[1]
    dur = max(win["end_s"] - win["start_s"], 0.1)
    budget = max(4, int(round(dur * 2.5)))
    total = sum(max(v, 0) for v in prof.values()) or 1
    plines = "\n".join(f"  {ct:<18} score={prof[ct]:.2f} share={max(prof[ct],0)/total:.0%}"
                       for ct in CONTENT_TYPES)
    common = (f"You are generating an audio description for blind/low-vision listeners.\n"
              f"Window: {win['start_s']:.1f}-{win['end_s']:.1f}s (duration {dur:.1f}s)\n"
              f"Audio context (what listener already hears): [silent]\n"
              f"Visual context available to you: {visual_ctx}\n")
    rules = (f"- Do NOT restate audible content.\n- Only use details supported by the visual context; "
             f"invent nothing.\n- Word budget: {budget}.\n"
             f'- Output JSON ONLY: {{"ad_text": str, "word_count": int}}. No prose outside JSON.\n')
    baseline = common + "\nDescribe the scene for a blind listener.\nInstructions:\n" + rules
    gap = (common + "\nA brain-encoding model (TRIBE) predicts the listener's cortical response is "
           "missing visual signal from the soundtrack. The missing signal decomposes by cortical "
           f"content type:\n\n{plines}\n\nDominant gap: {dom} (score {prof[dom]:.2f}). "
           f"Second: {sec} (score {prof[sec]:.2f}).\n\nInstructions:\n"
           f"- Emphasize {dom} content first ({EMPHASIS[dom]}). If words remain, cover {sec} "
           f"({EMPHASIS[sec]}).\n" + rules)
    return baseline, gap, dom, sec, prof, budget


GEN_MODEL = os.environ.get("GAP_GEN_MODEL", "claude-haiku-4-5-20251001")


def call_haiku(client, text):
    msg = client.messages.create(model=GEN_MODEL, max_tokens=400, timeout=90,
                                 messages=[{"role": "user", "content": text}])
    t = msg.content[0].text.strip()
    t = re.sub(r"^```(?:json)?|```$", "", t).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.S)
        return json.loads(m.group(0)) if m else {"ad_text": t, "word_count": len(t.split())}


def score(text, prof, dom, sec, budget):
    p = lexical_profile(text)
    c = lexical_counts(text)
    return {"profile_alignment": cosine_dict({k: prof.get(k, 0.0) for k in CONTENT_TYPES}, p),
            "dominant_keyword_coverage": c.get(dom, 0.0),
            "weighted_keyword_coverage": sum(prof.get(k, 0) * c.get(k, 0) for k in CONTENT_TYPES),
            "specificity_score": c["unique_keywords"] / max(c["word_count"], 1.0),
            "word_count": int(len(text.split()))}


def main():
    load_dotenv()
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    ctv = roi_groups()
    reg = {m["video_id"]: m for m in
           (json.loads(l) for l in (EXT / "registry.jsonl").read_text().splitlines() if l.strip())}
    man = T.load_manifest(); man = man[man.corpus == "external"]
    clip_list_path = os.environ.get("GAP_CLIP_LIST")
    if clip_list_path:
        keep = set(json.load(open(clip_list_path)))
        man = man[man.video_id.isin(keep)]
        print(f"filtered to {len(man)} clips from {clip_list_path}")

    rows = []
    for i, (_, r) in enumerate(man.iterrows()):
        meta = reg.get(r.video_id)
        if not meta:
            continue
        tens, _ = T.load_clip(r.clip_key)
        wins = build_windows(tens["P_AV"], tens["P_A"], ctv)
        wins = sorted(wins, key=lambda w: w["need"], reverse=True)[:MAX_WIN_PER_CLIP]
        vctx = meta.get("tier3_va11y", "")[:600]
        for w in wins:
            base_p, gap_p, dom, sec, prof, budget = make_prompts(w, vctx)
            for cond, ptext in [("baseline", base_p), ("gap_targeted", gap_p)]:
                try:
                    out = call_haiku(client, ptext)
                except Exception as e:
                    print("  call failed:", e); continue
                s = score(out.get("ad_text", ""), prof, dom, sec, budget)
                rows.append({"video_id": r.video_id, "window": w["window"], "condition": cond,
                             "dominant_type": dom, "second_type": sec, "ad_text": out.get("ad_text", ""), **s})
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(man)} clips, {len(rows)} candidates")
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    print(f"\n=== external gap-targeted A/B (Claude Haiku), {df.video_id.nunique()} clips ===")
    for metric in ["dominant_keyword_coverage", "profile_alignment",
                   "weighted_keyword_coverage", "specificity_score"]:
        piv = df.pivot_table(index=["video_id", "window"], columns="condition",
                             values=metric, aggfunc="first").dropna()
        if not {"baseline", "gap_targeted"}.issubset(piv.columns):
            continue
        d = piv["gap_targeted"] - piv["baseline"]
        try:
            p = wilcoxon(piv["gap_targeted"], piv["baseline"], alternative="greater").pvalue
        except ValueError:
            p = float("nan")
        print(f"  {metric:26s} base={piv['baseline'].mean():.3f} gap={piv['gap_targeted'].mean():.3f} "
              f"delta={d.mean():+.3f}  {int((d>0).sum())}W/{int((d<0).sum())}L  p={p:.4f}")
    print(f"\n  (2-clip in-bench was: dominant_kw +1.29 p=0.0026, profile_align +0.12 p=0.105)")
    print(f"  wrote {OUT}")


if __name__ == "__main__":
    main()
