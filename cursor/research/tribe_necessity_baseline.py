"""NECESSITY TEST: is TRIBE's targeting signal better than a VLM's own
"what visual info is missing" signal?

Holds generator + judge constant (gpt-4o) and varies ONLY the source of the
emphasis instruction:
  baseline : no emphasis ("describe the scene")
  tribe    : emphasize TRIBE's clip-dominant ROI content type (from tensors)
  vlm      : emphasize the type a gpt-4o VISION pass picks as most-missing-from-audio

All three generated from the same visual context (tier3 text) + word budget, then
blind-graded against each clip's ADQA questions. If vlm matches tribe on the
TRIBE-flagged (matched) questions, the brain encoder is not necessary.
"""
import base64
import glob
import json
import os
import random
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from scenetwin_roi_content_profile import lexical_profile  # noqa: E402

EXT = ROOT / "cursor" / "data" / "external_clips"
QCSV = ROOT / "cursor/output/external_adqa/external_adqa_questions.csv"
TRIBE_CAND = ROOT / "cursor/research/output/tribe_gap_targeted_external_full_scores.csv"
CLIPS = ROOT / "cursor/research/output/matched_clip_list_44.json"
OUT = ROOT / "cursor/research/output/tribe_necessity_perq.csv"
MODEL = "gpt-4o"
PRESC = ["motion_action", "scene_spatial", "face_character", "object_body", "visual_form"]
EMPH = {"motion_action": "what moves, who acts, the trajectory and result of action",
        "scene_spatial": "the place, layout, and spatial arrangement of objects/people",
        "face_character": "visible characters, expression, gaze, social cues",
        "object_body": "the salient object or body posture and how it is used",
        "visual_form": "shape, color, framing, lighting, or visual state"}


def load_dotenv():
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def jload(t):
    t = re.sub(r"^```(?:json)?|```$", "", t.strip()).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.S)
        return json.loads(m.group(0)) if m else {}


def b64(p):
    return base64.b64encode(open(p, "rb").read()).decode()


def vlm_need_type(client, frames):
    content = [{"type": "text", "text":
        "A blind listener hears only this clip's audio. Of these content types: "
        + ", ".join(PRESC) + " -- which ONE is the most important VISUAL information "
        "they would MISS (present in the video, not conveyed by audio)? "
        'Reply JSON only: {"type":"<one type>"}'}]
    for p in frames[:8]:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64(p)}"}})
    r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": content}], max_tokens=60)
    t = jload(r.choices[0].message.content).get("type", "")
    return t if t in PRESC else None


def gen_ad(client, visual_ctx, emphasis):
    instr = (f"Emphasize {emphasis} ({EMPH[emphasis]}) first." if emphasis
             else "Describe the scene for a blind listener.")
    p = (f"You are writing an audio description for blind/low-vision listeners.\n"
         f"Visual context (source of truth): {visual_ctx}\n"
         f"{instr}\nUse only details supported by the visual context; invent nothing. "
         f"~40 words.\nOutput JSON only: {{\"ad_text\": \"...\"}}")
    r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": p}], max_tokens=300)
    return jload(r.choices[0].message.content).get("ad_text", "")


def grade(client, questions, anon):
    import scenetwin_stage4_frame_grounded_adqa as s4
    r = client.chat.completions.create(model=MODEL,
        messages=[{"role": "user", "content": s4.grade_prompt(questions, anon)}], max_tokens=2000)
    return jload(r.choices[0].message.content)


def q_type(q, ev):
    prof = {k: lexical_profile(f"{q} {ev}").get(k, 0.0) for k in PRESC}
    return max(prof, key=prof.get) if max(prof.values()) > 0 else None


def main():
    load_dotenv()
    from openai import OpenAI
    client = OpenAI()
    qdf = pd.read_csv(QCSV)
    tcand = pd.read_csv(TRIBE_CAND)
    clips = json.load(open(CLIPS))
    if os.environ.get("NEC_LIMIT"):
        clips = clips[:int(os.environ["NEC_LIMIT"])]
    reg = {m["video_id"]: m for m in
           (json.loads(l) for l in (EXT / "registry.jsonl").read_text().splitlines() if l.strip())}
    rng = random.Random(0)
    rows, agree = [], []
    for i, vid in enumerate(clips):
        meta = reg.get(vid)
        frames = sorted(glob.glob(str(EXT / "frames" / vid / "frame_*.jpg")))
        qs = qdf[qdf.video_id == vid].sort_values("q_idx")
        tsub = tcand[tcand.video_id == vid]
        if not meta or not frames or qs.empty or tsub.empty:
            continue
        tribe_type = Counter(tsub.dominant_type).most_common(1)[0][0]
        try:
            vt = vlm_need_type(client, frames)
        except Exception as e:
            print("  vlm fail", vid, e); continue
        if not vt:
            continue
        agree.append(int(vt == tribe_type))
        vctx = meta.get("tier3_va11y", "")[:600]
        try:
            ad = {"baseline": gen_ad(client, vctx, None),
                  "tribe": gen_ad(client, vctx, tribe_type),
                  "vlm": gen_ad(client, vctx, vt)}
        except Exception as e:
            print("  gen fail", vid, e); continue
        questions = [{"q_idx": int(r.q_idx), "question": r.question, "answer_key": r.answer_key,
                      "required_visual_evidence": str(r.required_visual_evidence).split("; "),
                      "importance": r.importance} for r in qs.itertuples()]
        qt = {int(r.q_idx): q_type(r.question, str(r.required_visual_evidence)) for r in qs.itertuples()}
        ids = ["A", "B", "C"]; conds = ["baseline", "tribe", "vlm"]; rng.shuffle(conds)
        idmap = dict(zip(ids, conds))
        anon = [{"candidate_id": k, "description": ad[idmap[k]]} for k in ids]
        try:
            g = grade(client, questions, anon)
        except Exception as e:
            print("  grade fail", vid, e); continue
        for gr in g.get("grades", []):
            cid = str(gr.get("candidate_id", "")).strip()
            if cid not in idmap:
                continue
            qi = int(gr.get("q_idx", -1))
            rows.append({"video_id": vid, "q_idx": qi, "condition": idmap[cid],
                         "score": min(1.0, max(0.0, float(gr.get("score", 0) or 0))),
                         "matched": int(qt.get(qi) == tribe_type),
                         "tribe_type": tribe_type, "vlm_type": vt})
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(clips)}  (TRIBE-VLM agree so far: {np.mean(agree):.0%})")
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print(f"\n=== NECESSITY: TRIBE vs VLM targeting (gpt-4o gen+judge), {df.video_id.nunique()} clips ===")
    print(f"TRIBE & VLM picked SAME dominant type on {np.mean(agree):.0%} of clips (n={len(agree)})")
    for subset, mask in [("ALL questions", df.matched >= 0), ("TRIBE-MATCHED only", df.matched == 1)]:
        d = df[mask]
        piv = d.pivot_table(index=["video_id", "q_idx"], columns="condition", values="score", aggfunc="mean").dropna()
        print(f"\n  {subset} (n={len(piv)} q):")
        for c in ["baseline", "tribe", "vlm"]:
            if c in piv:
                print(f"    {c:9s} mean ADQA = {piv[c].mean():.3f}")
        if {"tribe", "vlm"}.issubset(piv.columns):
            dd = piv["tribe"] - piv["vlm"]
            try:
                p = wilcoxon(piv["tribe"], piv["vlm"], alternative="greater").pvalue
            except ValueError:
                p = float("nan")
            print(f"    tribe - vlm = {dd.mean():+.3f}  ({int((dd>0).sum())}W/{int((dd<0).sum())}L)  "
                  f"Wilcoxon(tribe>vlm) p={p:.4f}")
    print(f"\n  wrote {OUT}")


if __name__ == "__main__":
    main()
