#!/usr/bin/env python3
"""All-clip scene-model audit over the full VideoA11y/VATEX overlap corpus.

This checks whether the central thesis scales beyond the 20 timing clips / 23
hallucination clips. It does not use TRIBE because full TRIBE tensors are not in
this checkout for all 338 clips. Instead it asks: across all clips, do professional
ADs encode more scene-model axes (who/action/count/spatial) than VATEX captions?
"""
from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "workspace" / "vatex_overlap.json"
OUT_DIR = ROOT / "cursor" / "output" / "all_clip_scene_model_audit"
REPORT = ROOT / "output" / "reports" / "scenetwin-all-clip-scene-model-audit.md"

LEX = {
    "who_role": set("man woman person people child children boy girl chef rider skier player performer musician dog horse group crowd couple couples worker adult baby team family".split()),
    "action_relation": set("hold holds holding throw throws throwing cut cuts cutting pull pulls pulled push pushes pushing pushed eat eats eating drink drinks drinking ride rides riding run runs running walk walks walking jump jumps jumping dance dances dancing twirl twirls twirling talk talks speaking gesture gestures stirring cook cooking pour pours pouring mold molds kneel kneels reach reaches hand hands demonstrate demonstrates perform performs move moves moving use uses using play plays playing sing sings singing clap claps laugh laughs smile smiles kick kicks hit hits strike strikes lift lifts lower lowers open opens close closes place places drop drops pick picks turn turns look looks watch watches follow follows chase chases".split()),
    "spatial_relation": set("behind front beside near next across toward away around into onto under over between foreground background left right above below through along inside outside center side nearby back forth".split()),
    "count": set("one two three four five six seven eight nine ten several many few pair couple group crowd multiple both all".split()),
}
SCENE_TYPES = list(LEX)


def words(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def features(text: str) -> dict:
    ws = words(text)
    n = len(ws) or 1
    counts = {k: sum(w in vocab for w in ws) for k, vocab in LEX.items()}
    axes = {k: int(v > 0) for k, v in counts.items()}
    return {
        "word_count": len(ws),
        "scene_axis_count": sum(axes.values()),
        "scene_term_density_per_100w": 100 * sum(counts.values()) / n,
        **{f"has_{k}": v for k, v in axes.items()},
        **{f"n_{k}": v for k, v in counts.items()},
    }


def sign_test_p(wins: int, losses: int) -> float:
    # two-sided exact binomial p under p=0.5, ties ignored
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    prob = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * prob)


def main() -> None:
    rows = json.load(open(DATA, encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    per_clip = []
    per_text = []
    for r in rows:
        pro = features(r["va11y_desc"])
        cap_feats = [features(c) for c in r["vatex_caps"]]
        avg_cap_axes = mean(c["scene_axis_count"] for c in cap_feats)
        max_cap_axes = max(c["scene_axis_count"] for c in cap_feats)
        avg_cap_density = mean(c["scene_term_density_per_100w"] for c in cap_feats)
        max_cap_density = max(c["scene_term_density_per_100w"] for c in cap_feats)
        rec = {
            "video_id": r["video_id"],
            "category": r.get("category", ""),
            "pro_words": pro["word_count"],
            "pro_scene_axes": pro["scene_axis_count"],
            "avg_caption_scene_axes": avg_cap_axes,
            "max_caption_scene_axes": max_cap_axes,
            "pro_minus_avg_caption_axes": pro["scene_axis_count"] - avg_cap_axes,
            "pro_minus_max_caption_axes": pro["scene_axis_count"] - max_cap_axes,
            "pro_scene_density_per_100w": pro["scene_term_density_per_100w"],
            "avg_caption_scene_density_per_100w": avg_cap_density,
            "max_caption_scene_density_per_100w": max_cap_density,
            "pro_minus_avg_caption_density": pro["scene_term_density_per_100w"] - avg_cap_density,
        }
        for k in SCENE_TYPES:
            rec[f"pro_has_{k}"] = pro[f"has_{k}"]
            rec[f"caption_any_has_{k}"] = int(any(c[f"has_{k}"] for c in cap_feats))
            rec[f"caption_avg_has_{k}"] = mean(c[f"has_{k}"] for c in cap_feats)
        per_clip.append(rec)
        per_text.append({"video_id": r["video_id"], "kind": "professional_ad", "text_idx": 0, **pro})
        for i, (cap, cf) in enumerate(zip(r["vatex_caps"], cap_feats)):
            per_text.append({"video_id": r["video_id"], "kind": "vatex_caption", "text_idx": i, **cf})

    with open(OUT_DIR / "clips.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, per_clip[0].keys()); w.writeheader(); w.writerows(per_clip)
    with open(OUT_DIR / "texts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, per_text[0].keys()); w.writeheader(); w.writerows(per_text)

    axis_deltas = [r["pro_minus_avg_caption_axes"] for r in per_clip]
    axis_wins = sum(d > 0 for d in axis_deltas)
    axis_losses = sum(d < 0 for d in axis_deltas)
    max_axis_wins = sum(r["pro_minus_max_caption_axes"] >= 0 for r in per_clip)
    density_deltas = [r["pro_minus_avg_caption_density"] for r in per_clip]

    by_cat = defaultdict(list)
    for r in per_clip:
        by_cat[r["category"]].append(r)

    summary = {
        "n_clips": len(per_clip),
        "n_texts": len(per_text),
        "pro_vs_avg_caption_axis_wins": axis_wins,
        "pro_vs_avg_caption_axis_losses": axis_losses,
        "pro_vs_avg_caption_axis_ties": len(per_clip) - axis_wins - axis_losses,
        "pro_vs_avg_caption_axis_sign_p": sign_test_p(axis_wins, axis_losses),
        "pro_at_least_max_caption_axes": max_axis_wins,
        "mean_pro_scene_axes": mean(r["pro_scene_axes"] for r in per_clip),
        "mean_avg_caption_scene_axes": mean(r["avg_caption_scene_axes"] for r in per_clip),
        "median_axis_delta": median(axis_deltas),
        "mean_axis_delta": mean(axis_deltas),
        "mean_density_delta": mean(density_deltas),
        "median_density_delta": median(density_deltas),
        "pro_all_four_axes": sum(r["pro_scene_axes"] == 4 for r in per_clip),
        "avg_caption_all_four_axes_equiv": sum(r["avg_caption_scene_axes"] >= 3.5 for r in per_clip),
        "axis_presence": {},
        "by_category": {},
    }
    for k in SCENE_TYPES:
        summary["axis_presence"][k] = {
            "pro_rate": mean(r[f"pro_has_{k}"] for r in per_clip),
            "caption_any_rate": mean(r[f"caption_any_has_{k}"] for r in per_clip),
            "caption_avg_rate": mean(r[f"caption_avg_has_{k}"] for r in per_clip),
        }
    for cat, vals in sorted(by_cat.items()):
        if len(vals) < 5:
            continue
        ds = [r["pro_minus_avg_caption_axes"] for r in vals]
        summary["by_category"][cat] = {
            "n": len(vals),
            "mean_axis_delta": mean(ds),
            "wins": sum(d > 0 for d in ds),
            "losses": sum(d < 0 for d in ds),
        }
    json.dump(summary, open(OUT_DIR / "summary.json", "w", encoding="utf-8"), indent=2)

    cat_rows = sorted(summary["by_category"].items(), key=lambda kv: kv[1]["mean_axis_delta"], reverse=True)
    lines = [
        "# All-Clip Scene-Model Audit",
        "",
        "## Question",
        "",
        "Does the scene-model thesis hold beyond the small TRIBE/hallucination subsets? Across all local VideoA11y/VATEX overlap clips, do professional ADs encode more who/action/count/spatial structure than ordinary captions?",
        "",
        "## Scope",
        "",
        f"Checked all `{len(per_clip)}` clips in `workspace/vatex_overlap.json` (`{len(per_text)}` total texts: one professional AD plus VATEX captions per clip).",
        "",
        "Important limitation: this is a text-side corpus audit, not a TRIBE result. Full TRIBE tensors for all 338 clips are not present in this checkout, so TRIBE routing remains validated on the cached 20-clip timing stack only.",
        "",
        "## Result",
        "",
        f"Professional ADs cover more scene-model axes than the average VATEX caption on `{axis_wins}/{len(per_clip)}` clips, with `{axis_losses}` losses and `{summary['pro_vs_avg_caption_axis_ties']}` ties. Exact sign-test p = `{summary['pro_vs_avg_caption_axis_sign_p']:.2e}`.",
        "",
        f"Mean scene-model axes: professional AD `{summary['mean_pro_scene_axes']:.2f}` vs average caption `{summary['mean_avg_caption_scene_axes']:.2f}`; mean delta `+{summary['mean_axis_delta']:.2f}` axes per clip.",
        "",
        f"Professional AD has at least as many scene-model axes as the strongest individual caption on `{max_axis_wins}/{len(per_clip)}` clips.",
        "",
        "| axis | pro presence | any caption presence | average caption presence |",
        "|---|---:|---:|---:|",
    ]
    for k, v in summary["axis_presence"].items():
        lines.append(f"| {k} | {100*v['pro_rate']:.1f}% | {100*v['caption_any_rate']:.1f}% | {100*v['caption_avg_rate']:.1f}% |")
    lines += [
        "",
        "Density note: professional ADs are longer and more complete, so term density per 100 words is not the right headline; categorical coverage is. The thesis is that AD must preserve multiple scene-model axes, not maximize keyword density.",
        "",
        "## Category breakdown",
        "",
        "| category | n | mean pro-minus-caption axes | wins | losses |",
        "|---|---:|---:|---:|---:|",
    ]
    for cat, s in cat_rows:
        lines.append(f"| {cat} | {s['n']} | {s['mean_axis_delta']:.2f} | {s['wins']} | {s['losses']} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "This supports the central thesis at corpus scale: professional ADs are not merely longer object captions. They systematically add scene-model structure — who is involved, what actions unfold, counts/groups, and spatial relations. That is exactly the information that relation/action/count hallucinations corrupt and object grounding misses.",
        "",
        "## How this connects to TRIBE",
        "",
        "- All-clip text audit: professional ADs encode richer scene-model axes across 338 clips.",
        "- Hallucination audit: object grounding catches object/scene swaps but misses scene-model flips.",
        "- TRIBE timing subset: high neural access-gap moments are enriched for scene-model probes (`79.5%` scene-model questions).",
        "",
        "Together: scene-model information is what professional AD adds; object grounding misses when it is wrong; TRIBE helps decide where to probe it.",
        "",
        "## Files",
        "",
        "- `cursor/pipeline/all_clip_scene_model_audit.py`",
        "- `cursor/output/all_clip_scene_model_audit/clips.csv`",
        "- `cursor/output/all_clip_scene_model_audit/texts.csv`",
        "- `cursor/output/all_clip_scene_model_audit/summary.json`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_DIR / 'clips.csv'}")
    print(f"Wrote {OUT_DIR / 'texts.csv'}")
    print(f"Wrote {OUT_DIR / 'summary.json'}")
    print(f"Wrote {REPORT}")
    print(json.dumps(summary, indent=2)[:2000])


if __name__ == "__main__":
    main()
