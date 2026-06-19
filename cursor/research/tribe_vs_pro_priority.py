"""Does TRIBE predict what PROFESSIONAL human describers chose to describe,
better than a VLM does?

TRIBE models a human brain's response, so its claimed edge is PERCEPTUAL
PRIORITY, not semantic content (where VLMs win, see necessity rematch). The
professional AD (tier3) is human ground truth for "what visual content matters
enough to narrate." Test per clip:

  pro_profile  = content-type distribution of the tier3 professional AD (lexical)
  tribe_profile= content-type need distribution from TRIBE ROI gaps (tensors)
  vlm_profile  = gpt-4o (frames+transcript) distribution over the same types

Compare cosine(tribe, pro) vs cosine(vlm, pro) across clips. If TRIBE aligns
with professional human choices better than the VLM, that is a capability that
plays to the brain grounding and that a VLM approximates worse.
"""
import base64
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from scenetwin_roi_content_profile import ROI_TO_CONTENT, lexical_profile  # noqa: E402
sys.path.insert(0, str(ROOT / "cursor/research"))
import tribe_necessity_rematch as NR  # reuse transcript cache + dotenv

EXT = ROOT / "cursor/data/external_clips"
ROI_CSV = ROOT / "cursor/research/output/tribe_roi_gap_per_clip.csv"
MAN = ROOT / "cursor/research/output/tribe_tensors/manifest.csv"
OUT = ROOT / "cursor/research/output/tribe_vs_pro_priority.csv"
TYPES = ["motion_action", "scene_spatial", "face_character", "object_body", "visual_form"]
MODEL = "gpt-4o"


def norm(v):
    v = np.array([max(x, 0.0) for x in v], float)
    s = v.sum()
    return v / s if s > 0 else np.ones(len(v)) / len(v)


def cos(a, b):
    a, b = norm(a), norm(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def tribe_profile(roi_row):
    """Map per-ROI gaps to the 5 content types and sum."""
    agg = {t: 0.0 for t in TYPES}
    for roi, ct in ROI_TO_CONTENT.items():
        if ct in agg and roi in roi_row:
            agg[ct] += max(float(roi_row[roi]), 0.0)
    return [agg[t] for t in TYPES]


def text_profile(text):
    p = lexical_profile(text)
    return [p.get(t, 0.0) for t in TYPES]


def vlm_profile(client, frames, transcript):
    aud = transcript if transcript.strip() else "[no speech / ambient only]"
    content = [{"type": "text", "text":
        f"A blind listener hears only this audio:\n\"{aud}\"\n\n"
        "For a blind/low-vision listener, rate how IMPORTANT it is to describe each "
        "of these visual content types for THIS clip (0-10 each): " + ", ".join(TYPES) +
        '. Reply JSON only: {"motion_action":n,"scene_spatial":n,"face_character":n,'
        '"object_body":n,"visual_form":n}'}]
    for p in frames[:8]:
        content.append({"type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(open(p,'rb').read()).decode()}"}})
    r = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": content}], max_tokens=120)
    d = NR.jload(r.choices[0].message.content)
    return [float(d.get(t, 0) or 0) for t in TYPES]


def main():
    NR.load_dotenv()
    from openai import OpenAI
    client = OpenAI()
    roi = pd.read_csv(ROI_CSV)
    man = pd.read_csv(MAN)[["clip_key", "video_id"]]
    roi = roi.merge(man, on="clip_key", how="left")
    roi = roi[roi.corpus == "external"]
    reg = {m["video_id"]: m for m in
           (json.loads(l) for l in (EXT / "registry.jsonl").read_text().splitlines() if l.strip())}

    rows = []
    for i, (_, r) in enumerate(roi.iterrows()):
        vid = r.video_id
        meta = reg.get(vid)
        frames = sorted(glob.glob(str(EXT / "frames" / vid / "frame_*.jpg")))
        if not meta or not frames:
            continue
        pro = text_profile(meta.get("tier3_va11y", ""))
        if sum(pro) == 0:
            continue
        tri = tribe_profile(r)
        tx = NR.transcript_for(client, vid)
        try:
            vlm = vlm_profile(client, frames, tx)
        except Exception as e:
            print("  vlm fail", vid, e); continue
        rows.append({"video_id": vid,
                     "tribe_vs_pro": cos(tri, pro),
                     "vlm_vs_pro": cos(vlm, pro),
                     "uniform_vs_pro": cos([1] * 5, pro),
                     "tribe_top": TYPES[int(np.argmax(tri))],
                     "vlm_top": TYPES[int(np.argmax(vlm))],
                     "pro_top": TYPES[int(np.argmax(pro))]})
        if (i + 1) % 15 == 0:
            print(f"  {i+1} clips")
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    n = len(df)
    print(f"\n=== Alignment with PROFESSIONAL human AD content priority (n={n} clips) ===")
    print(f"  cosine(TRIBE need, pro AD)   = {df.tribe_vs_pro.mean():.3f}")
    print(f"  cosine(VLM rating, pro AD)   = {df.vlm_vs_pro.mean():.3f}")
    print(f"  cosine(uniform, pro AD)      = {df.uniform_vs_pro.mean():.3f}  (chance baseline)")
    d = df.tribe_vs_pro - df.vlm_vs_pro
    p = wilcoxon(df.tribe_vs_pro, df.vlm_vs_pro).pvalue
    print(f"  TRIBE - VLM = {d.mean():+.3f}  ({int((d>0).sum())}W/{int((d<0).sum())}L)  Wilcoxon p={p:.4f}")
    print(f"\n  top-type EXACT match to pro: TRIBE {(df.tribe_top==df.pro_top).mean()*100:.0f}%  "
          f"VLM {(df.vlm_top==df.pro_top).mean()*100:.0f}%  (chance 20%)")
    print(f"  wrote {OUT}")


if __name__ == "__main__":
    main()
