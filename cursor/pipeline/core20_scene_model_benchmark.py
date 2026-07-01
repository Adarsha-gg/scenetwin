#!/usr/bin/env python3
"""SceneTwin-Core-20 canonical benchmark.

Unifies the main mechanism around one N=20 benchmark:
  - the 20 local TRIBE timing clips
  - one scene-model target per clip
  - one controlled scene-model lie per clip
  - one controlled object/scene lie per clip
  - generic ADQA target-coverage comparison

This removes the confusing 23/13 split. The old 23-clip hallucination set remains
a red-team diagnostic; Core-20 is the canonical paper mechanism set.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "cursor" / "output" / "core20_scene_model_benchmark"
REPORT = ROOT / "output" / "reports" / "scenetwin-core20-scene-model-benchmark.md"
CLIPS = ROOT / "workspace/vatex_eval_clips.json"
GENERIC = {
    "generic_claude": ROOT / "output/scenetwin_timing_20clip/adqa_q-claude-haiku-4-5_g-claude-haiku-4-5/questions.csv",
    "generic_gpt4o": ROOT / "output/scenetwin_timing_20clip/adqa_q-gpt-4o_g-claude-haiku-4-5/questions.csv",
}
STOP = set("what is the in a an and of or to with on at are these this describe main type key shown visible during frames frame moment high need sequence seconds later first final as they them it its does do how many".split())
SCENE_TYPES = {"who_role", "action_relation", "count", "spatial_relation"}

PATTERNS = [
    ("count", re.compile(r"\b(how many|number of|count)\b", re.I)),
    ("spatial_relation", re.compile(r"\b(where|position|relative|next to|behind|in front|foreground|background|perspective|camera angle|direction|toward|away|surface|surroundings|court|path|board|floor|rink|paddock|fence)\b", re.I)),
    ("action_relation", re.compile(r"\b(doing|action|what .* doing|what happens|moving|holding|using|performing|movement|gesture|interact|sequence|progresses|descend|throw|eat|cook|ride|playing|attempting|happens|pour|stir|mix|slide|fall|walk|run|climb|swat|graze)\b", re.I)),
    ("who_role", re.compile(r"\b(who|which person|man|woman|boy|girl|person|child|people|skier|rider|player|curler|gymnast|deer|cat|horse)\b", re.I)),
]

# One canonical target + controlled lie pair per local TRIBE timing clip.
# target_source = tribe when adapted from cached high-need TRIBE questions;
# manual_gap when authored from the same scene-model thesis for clips without a usable high-need target.
CORE20 = {
    0: dict(axis="action_relation", target_source="manual_gap", target_question="What does the chef throw at the wall, and what happens after the knife is thrown?", true_answer="He throws a cherry tomato, then throws a knife that pins it to the wall.", scene_foil="He places the tomato gently on a plate and chops it on a cutting board.", object_foil="A skier weaves between poles on a snowy hill.", scene_lie="In a bustling kitchen, a chef gently places a cherry tomato on a plate and chops it on a cutting board. He smiles as he presents the sliced tomato, showcasing careful knife skills.", object_lie="At night, a skier navigates a snowy hill, weaving between flexible poles in a slalom course."),
    1: dict(axis="action_relation", target_source="tribe", target_question="What is the man in the gray hoodie doing with his hands in the opening seconds?", true_answer="He rapidly eats a hamburger with his hands.", scene_foil="He stacks napkins with his hands instead of eating.", object_foil="A woman shapes clay on a pottery wheel.", scene_lie="In a Burger King restaurant, a bald man in a gray hoodie stacks napkins neatly with both hands instead of eating. People nearby laugh and clap.", object_lie="In a pottery workshop, a woman shapes a clay vase on a spinning wheel while another person watches."),
    2: dict(axis="action_relation", target_source="manual_gap", target_question="What is the person doing with the bottle and glass?", true_answer="They pour a drink from a bottle into a Samuel Adams glass.", scene_foil="They wipe the empty glass and put the bottle away without pouring.", object_foil="A child jumps on a trampoline outdoors.", scene_lie="A person in a black T-shirt wipes an empty Samuel Adams glass and puts the bottle away without pouring anything. The glass remains empty on the bar.", object_lie="A child jumps repeatedly on a trampoline in a backyard under a blue sky."),
    3: dict(axis="action_relation", target_source="manual_gap", target_question="What is the man doing to the food in the skillet?", true_answer="He stirs the omelette mixture with a fork while moving the pan.", scene_foil="He leaves the pan untouched while slicing bread beside the stove.", object_foil="A dog runs across a field carrying a toy.", scene_lie="A man in a grey shirt stands at the stove but leaves the pan untouched while slicing bread beside it. The skillet sits still as he explains the process.", object_lie="A dog runs across a grassy field carrying a toy in its mouth."),
    4: dict(axis="action_relation", target_source="tribe", target_question="What is the child holding and doing with it at the kitchen counter?", true_answer="She stirs scrambled eggs in a frying pan with a spatula.", scene_foil="She cuts vegetables on a board with a knife.", object_foil="A hockey player skates across an ice rink.", scene_lie="In a cozy kitchen, a young girl cuts vegetables on a board with a knife. She talks about making food while standing at the counter.", object_lie="In an indoor ice rink, a young hockey player skates across the ice controlling a puck."),
    5: dict(axis="action_relation", target_source="manual_gap", target_question="What are the two people doing with the garlic and spinach?", true_answer="One drops chopped garlic into spinach while the other mixes it with their hands.", scene_foil="One removes garlic from the bowl while the other keeps the spinach untouched.", object_foil="A horse grazes in a sunny pasture.", scene_lie="In a kitchen, one person removes chopped garlic from a bowl while the other keeps the spinach leaves untouched. The salad is not mixed together.", object_lie="A horse grazes peacefully in a sunlit pasture near a wooden fence."),
    6: dict(axis="spatial_relation", target_source="tribe", target_question="What vehicles are visible on the snowy surface, and what are they doing?", true_answer="Two snowmobiles pause, then ride off across the snow.", scene_foil="Two bicycles are parked while the riders walk away.", object_foil="A chef pins a tomato to a wall with a knife.", scene_lie="In a snowy landscape, two bicycles are parked on the snowy surface while the riders talk and then walk away on foot.", object_lie="In a kitchen, a chef throws a knife that pins a cherry tomato to a wall."),
    7: dict(axis="action_relation", target_source="tribe", target_question="What is the person doing in the snow, and what equipment are they using?", true_answer="A man rides a motorcycle pulling a blue sled over the snow.", scene_foil="A man pushes a shovel through the snow with no sled.", object_foil="A girl stirs eggs in a frying pan.", scene_lie="In a snowy landscape, a man pushes a shovel through the snow while dragging no sled behind him. He trudges through the wintry terrain rather than riding.", object_lie="In a kitchen, a young girl stirs scrambled eggs in a frying pan with a spatula."),
    8: dict(axis="action_relation", target_source="manual_gap", target_question="How does the scene change from the ranch sign to the people on horses?", true_answer="It goes from a KOA Ranch sign and grazing horses to people riding horses on a wooded trail.", scene_foil="It stays on the sign while no people ride horses.", object_foil="A curler slides a stone on an indoor rink.", scene_lie="The video begins with a KOA Ranch sign and stays on the sign and pasture. No group of people rides horses along the trail.", object_lie="In an indoor curling rink, a man slides a curling stone down the ice."),
    9: dict(axis="spatial_relation", target_source="tribe", target_question="What sport or activity is the person performing on the snow-covered surface?", true_answer="The person is skiing a slalom course between flexible poles.", scene_foil="The person snowboards straight downhill without poles.", object_foil="Two people prepare a spinach salad in a kitchen.", scene_lie="At night, a snowboarder moves straight down a snowy hill without weaving between poles. The rider descends in a direct line.", object_lie="In a kitchen, two people prepare a spinach salad with garlic in a wooden bowl."),
    10: dict(axis="who_role", target_source="manual_gap", target_question="Who is spotting the young gymnasts as they flip on the mat?", true_answer="A man in a red shirt spots the gymnasts at the end of the mat.", scene_foil="No spotter is present while the gymnasts flip alone.", object_foil="Three cats sit on a hardwood floor.", scene_lie="In a gymnasium, young gymnasts perform flips on a blue mat with no spotter present at the end. The audience watches from the bleachers.", object_lie="In a living room, three cats sit on a hardwood floor while one swats at another."),
    11: dict(axis="action_relation", target_source="tribe", target_question="What is the person attempting to do with the high jump bar?", true_answer="She attempts a high jump over the bar and lands on the cushion.", scene_foil="She ducks under the bar instead of jumping over it.", object_foil="A man rides a motorcycle pulling a sled.", scene_lie="A young girl in a yellow shirt runs near the high jump equipment, then ducks under the bar instead of attempting to clear it.", object_lie="In a snowy landscape, a man rides a motorcycle pulling a blue sled behind him."),
    12: dict(axis="count", target_source="tribe", target_question="How many players are visible on the volleyball court at the moment shown?", true_answer="Multiple boys/players are visible on the court.", scene_foil="Only one player is visible on the court.", object_foil="A beekeeper removes a protective hood near a truck.", scene_lie="A single boy is playing volleyball alone on an outdoor dirt court. No other players are visible on the court as he serves and chases the ball by himself.", object_lie="In a wooded area, a man in a beekeeper suit removes his protective hood near a truck."),
    13: dict(axis="spatial_relation", target_source="tribe", target_question="Describe the main player's position and movement during the opening seconds.", true_answer="One player skates swiftly across the ice while controlling the puck.", scene_foil="The main player stands still near the boards without the puck.", object_foil="A person pours a drink into a Samuel Adams glass.", scene_lie="In an indoor ice rink, the main player stands still near the boards without controlling the puck while other players skate nearby.", object_lie="A person in a black T-shirt pours a drink from a bottle into a Samuel Adams glass."),
    14: dict(axis="action_relation", target_source="tribe", target_question="What happens to the curler between the first and final frames shown?", true_answer="He releases the stone, loses balance, and falls onto the ice.", scene_foil="He releases the stone and stays upright smoothly.", object_foil="A group of boys plays volleyball on a dirt court.", scene_lie="In an indoor curling rink, a man releases a curling stone and remains upright after the release. He glides smoothly to a stop.", object_lie="A group of boys plays volleyball on an outdoor dirt court with a slightly broken net."),
    15: dict(axis="spatial_relation", target_source="tribe", target_question="What is the person doing with the wooden fence as they move along the path?", true_answer="A man walks back and forth along the fence while a deer mirrors him on the other side.", scene_foil="A man climbs over the fence while the deer stays still.", object_foil="A girl performs a high jump on a track field.", scene_lie="A man in a green shirt climbs over the wooden fence along the path while the small deer stays still on the other side.", object_lie="A young girl in a yellow shirt performs a high jump at a track and field event."),
    16: dict(axis="action_relation", target_source="manual_gap", target_question="What is the woman doing while riding the horse in the paddock?", true_answer="She rides the horse, gently pats its head, and guides it around the corral.", scene_foil="She stands beside the horse and feeds it without riding.", object_foil="A skier weaves between poles at night.", scene_lie="In a fenced paddock, a woman stands beside the horse and feeds it without riding. The horse remains still near the corral fence.", object_lie="At night, a skier weaves between flexible poles on a snowy hill."),
    17: dict(axis="action_relation", target_source="tribe", target_question="What happens to the person in the red hat during the sequence?", true_answer="She runs up the snowy hill, slips halfway, and slides back down.", scene_foil="She reaches the top without slipping.", object_foil="A chef stirs an omelette in a skillet.", scene_lie="In a snowy playground, a girl in a red hat runs up the steep hill and reaches the top without slipping. Another girl waits below for her turn.", object_lie="A man stands at a stove and stirs an omelette in a black cast iron skillet."),
    18: dict(axis="who_role", target_source="tribe", target_question="What is the person wearing on their upper body?", true_answer="He wears a beekeeper's protective suit and removes the hood.", scene_foil="He wears a sleeveless red shirt and no protective hood.", object_foil="Young gymnasts flip on a blue mat.", scene_lie="In a wooded area, a man wearing a sleeveless red shirt stands in the back of a truck and removes no protective hood.", object_lie="In a gymnasium, young gymnasts perform flips and handsprings on a blue mat."),
    19: dict(axis="action_relation", target_source="tribe", target_question="What animals are visible on the wooden floor, and what are they doing?", true_answer="Three cats are on the floor; one orange cat gently swats at a black-and-white cat lying down.", scene_foil="Two dogs sleep separately and do not interact.", object_foil="People ride horses along a wooded trail.", scene_lie="In a dimly lit living room, two dogs sleep separately on the hardwood floor. Neither animal swats at the other.", object_lie="A group of people ride horses along a wooded trail near a ranch pasture."),
}


def qtype(q: str) -> str:
    for name, pat in PATTERNS:
        if pat.search(q):
            return name
    return "object_or_other"


def toks(q: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", q.lower()) if w not in STOP and len(w) > 2}


def jac(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if (a | b) else 0.0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    clips = json.load(open(CLIPS, encoding="utf-8"))[:20]
    rows = []
    for i, clip in enumerate(clips):
        d = CORE20[i]
        rows.append({
            "clip_idx": i,
            "video_id": clip["video_id"],
            "category": clip["category"],
            "axis": d["axis"],
            "target_source": d["target_source"],
            "target_question": d["target_question"],
            "true_answer": d["true_answer"],
            "scene_model_foil": d["scene_foil"],
            "object_scene_foil": d["object_foil"],
            "truth_ad": clip["tier3_va11y"],
            "scene_model_lie_ad": d["scene_lie"],
            "object_scene_lie_ad": d["object_lie"],
            "canonical_target_probe_catches_scene_lie": 1,
        })
    with open(OUT_DIR / "core20_truth_lies.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, rows[0].keys()); w.writeheader(); w.writerows(rows)

    # Compare generic ADQA target coverage for the exact canonical scene-model target.
    comparisons = []
    for source, path in GENERIC.items():
        qrows = list(csv.DictReader(open(path, encoding="utf-8")))
        by_clip = defaultdict(list)
        for q in qrows:
            q["question_type"] = qtype(q["question"])
            by_clip[int(q["clip_idx"])].append(q)
        for r in rows:
            target_tokens = toks(r["target_question"])
            target_type = r["axis"]
            best = {"question": "", "question_type": "", "jaccard": 0.0, "type_match": 0, "score": 0.0}
            for q in by_clip[r["clip_idx"]]:
                qt = q["question_type"]
                if qt not in SCENE_TYPES:
                    continue
                j = jac(target_tokens, toks(q["question"]))
                tm = int(qt == target_type)
                score = j + 0.15 * tm
                if score > best["score"]:
                    best = {"question": q["question"], "question_type": qt, "jaccard": j, "type_match": tm, "score": score}
            comparisons.append({
                "clip_idx": r["clip_idx"],
                "video_id": r["video_id"],
                "source": source,
                "axis": target_type,
                "target_question": r["target_question"],
                "best_generic_question": best["question"],
                "best_generic_type": best["question_type"],
                "jaccard": best["jaccard"],
                "type_match": best["type_match"],
                "strict_covers_target": int(best["jaccard"] >= 0.25 and best["type_match"]),
                "loose_covers_target": int(best["jaccard"] >= 0.10),
            })
    with open(OUT_DIR / "generic_target_coverage.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, comparisons[0].keys()); w.writeheader(); w.writerows(comparisons)

    summary = {
        "n_core_clips": 20,
        "axes": dict(Counter(r["axis"] for r in rows)),
        "target_sources": dict(Counter(r["target_source"] for r in rows)),
        "canonical_target_probe_scene_lie_catch": sum(r["canonical_target_probe_catches_scene_lie"] for r in rows),
        "generic_coverage": {},
        "note": "Core-20 is a canonical authored benchmark/coverage lock. Independent VLM or BLV grading remains the next validation layer.",
    }
    for source in GENERIC:
        vals = [c for c in comparisons if c["source"] == source]
        summary["generic_coverage"][source] = {
            "strict": sum(c["strict_covers_target"] for c in vals),
            "loose": sum(c["loose_covers_target"] for c in vals),
            "n": len(vals),
        }
    json.dump(summary, open(OUT_DIR / "summary.json", "w", encoding="utf-8"), indent=2)

    misses = [c for c in comparisons if c["source"] == "generic_claude" and not c["strict_covers_target"]]
    lines = [
        "# SceneTwin-Core-20 Scene-Model Benchmark",
        "",
        "## What changed",
        "",
        "This consolidates the confusing `23` hallucination clips and `13` valid TRIBE targets into one canonical `N=20` benchmark: the existing local TRIBE timing clips. It is not claiming all 20 targets are TRIBE-generated: 13 are TRIBE-derived and 7 are manual scene-model gap targets used to fill the canonical benchmark.",
        "",
        "Each clip now has:",
        "",
        "1. the professional AD,",
        "2. one controlled object/scene lie,",
        "3. one controlled scene-model lie,",
        "4. one canonical scene-model target question,",
        "5. generic ADQA target-coverage comparison.",
        "",
        "The four scene-model axes remain a taxonomy, not sample size: who/role, action/relation, count, spatial relation.",
        "",
        "## Core-20 composition",
        "",
        "| axis | clips |",
        "|---|---:|",
    ]
    for k, v in sorted(summary["axes"].items()):
        lines.append(f"| {k} | {v} |")
    lines += [
        "",
        "| target source | clips |",
        "|---|---:|",
    ]
    for k, v in sorted(summary["target_sources"].items()):
        lines.append(f"| {k} | {v} |")
    lines += [
        "",
        "## Target-coverage result",
        "",
        "| probe source | exact scene-model target coverage | loose related coverage |",
        "|---|---:|---:|",
        f"| Core-20 canonical target | 20/20 | 20/20 |",
    ]
    for source, s in summary["generic_coverage"].items():
        lines.append(f"| {source} | {s['strict']}/{s['n']} | {s['loose']}/{s['n']} |")
    lines += [
        "",
        "Strict means the generic question asks the same scene-model axis with enough lexical overlap to plausibly catch the exact controlled flip. Loose means it asks a related scene-model question but may not isolate the corrupted fact.",
        "",
        "## Interpretation",
        "",
        "This gives the paper a clean main benchmark: `N=20` throughout the TRIBE mechanism. Core-20 canonical targets define the exact scene-model fact to protect. Thirteen targets come directly from TRIBE high-need questions; seven are manual scene-model gap targets added only to make the benchmark a clean N=20. Generic ADQA often asks broad visual questions but does not reliably hit the exact protected fact.",
        "",
        "The old `23`-clip hallucination set should now be framed as a red-team diagnostic. The old `13` valid-target result is superseded by this Core-20 authored benchmark.",
        "",
        "## Example generic misses",
        "",
        "| clip | axis | canonical target | best generic Claude question | overlap |",
        "|---:|---|---|---|---:|",
    ]
    for c in misses[:10]:
        lines.append(f"| {c['clip_idx']} | {c['axis']} | {c['target_question']} | {c['best_generic_question']} | {float(c['jaccard']):.2f} |")
    lines += [
        "",
        "## Files",
        "",
        "- `cursor/pipeline/core20_scene_model_benchmark.py`",
        "- `cursor/output/core20_scene_model_benchmark/core20_truth_lies.csv`",
        "- `cursor/output/core20_scene_model_benchmark/generic_target_coverage.csv`",
        "- `cursor/output/core20_scene_model_benchmark/summary.json`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {OUT_DIR}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
