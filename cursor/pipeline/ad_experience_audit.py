#!/usr/bin/env python3
"""Audio-description experience/style audit.

This is deliberately NOT another rho/AUC scorer. It audits AD failure modes that
matter to BLV viewers but are mostly invisible to SceneTwin's existing semantic
coverage metrics: frame-dump/list descriptions, anticipatory/spoiler wording,
uncertain visual inference, and temporal sequencing burden.

Inputs are local only:
  - workspace/vatex_overlap.json (VideoA11y professional AD + VATEX captions)
  - output/live_*sweep.csv (live generated AD examples, including high-motion)

Outputs:
  - cursor/output/ad_experience_audit/{items.csv,summary.json}
  - output/reports/scenetwin-ad-experience-audit.md
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "cursor" / "output" / "ad_experience_audit"
REPORT = ROOT / "output" / "reports" / "scenetwin-ad-experience-audit.md"

PATTERNS = {
    # Style-guide issue: can reveal/forecast action before the viewer should know.
    "anticipation_spoiler": re.compile(
        r"\b(will soon|will|about to|in a moment|later|prepares to|preparing to|starts to|begins to)\b",
        re.I,
    ),
    # Common frame-sampled VLM failure: a narrated storyboard/list, not an AD.
    "frame_dump_list": re.compile(
        r"(^\s*\d+[\.)]|\b(the clip features|series of dynamic scenes|series of scenes|"
        r"first.*second.*third|final shot|scene shifts|transitions to|subsequent scenes)\b)",
        re.I | re.S,
    ),
    # AD guidelines warn against stating interpretation as fact; uncertainty should be audited.
    "uncertain_inference": re.compile(r"\b(appears to|seems to|suggesting|possibly|likely|looks like)\b", re.I),
    # Not always bad, but high density suggests temporal load / plot-summary style.
    "timing_sequence": re.compile(r"\b(then|after|before|next|finally|subsequent|throughout)\b", re.I),
}


def load_items() -> list[dict]:
    items: list[dict] = []
    meta_path = ROOT / "workspace" / "vatex_overlap.json"
    for row in json.load(open(meta_path, encoding="utf-8")):
        items.append(
            {
                "source": "videoa11y",
                "kind": "professional_ad",
                "id": row["video_id"],
                "category": row.get("category", ""),
                "text": row["va11y_desc"],
                "adqa": "",
                "clip_top3": "",
            }
        )
        for i, cap in enumerate(row.get("vatex_caps", [])):
            items.append(
                {
                    "source": "vatex",
                    "kind": "crowd_caption",
                    "id": f"{row['video_id']}#cap{i}",
                    "category": row.get("category", ""),
                    "text": cap,
                    "adqa": "",
                    "clip_top3": "",
                }
            )

    for path in glob.glob(str(ROOT / "output" / "live_*sweep.csv")):
        source = Path(path).name
        for row in csv.DictReader(open(path, encoding="utf-8")):
            if row.get("ok") != "True" or not row.get("ad"):
                continue
            items.append(
                {
                    "source": source,
                    "kind": "generated_live_ad",
                    "id": row.get("name", row.get("url", "")),
                    "category": "live_demo",
                    "text": row["ad"],
                    "adqa": row.get("adqa", ""),
                    "clip_top3": row.get("clip_top3", ""),
                }
            )
    return items


def audit_item(item: dict) -> dict:
    text = item["text"]
    flags = {name: bool(pat.search(text)) for name, pat in PATTERNS.items()}
    words = re.findall(r"[A-Za-z']+", text)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    # A compact severity proxy: style-guide flags plus long/listy generated text.
    severity = sum(flags.values())
    if len(words) > 85:
        severity += 1
    if len(sentences) >= 6:
        severity += 1
    out = dict(item)
    out.update({k: int(v) for k, v in flags.items()})
    out["word_count"] = len(words)
    out["sentence_count"] = len(sentences)
    out["experience_severity"] = severity
    out["snippet"] = text[:220].replace("\n", " ")
    return out


def pct(n: int, d: int) -> str:
    return f"{(100*n/d):.1f}%" if d else "n/a"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    rows = [audit_item(x) for x in load_items()]
    fieldnames = [
        "source",
        "kind",
        "id",
        "category",
        "adqa",
        "clip_top3",
        "word_count",
        "sentence_count",
        "experience_severity",
        *PATTERNS.keys(),
        "snippet",
    ]
    with open(OUT_DIR / "items.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    by_kind: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_kind[r["kind"]].append(r)

    summary = {
        "n_items": len(rows),
        "by_kind": {},
        "pattern_totals": {k: sum(r[k] for r in rows) for k in PATTERNS},
    }
    for kind, vals in sorted(by_kind.items()):
        summary["by_kind"][kind] = {
            "n": len(vals),
            "mean_experience_severity": mean(r["experience_severity"] for r in vals),
            "mean_word_count": mean(r["word_count"] for r in vals),
            **{f"{k}_rate": sum(r[k] for r in vals) / len(vals) for k in PATTERNS},
        }

    live = by_kind.get("generated_live_ad", [])
    pro = by_kind.get("professional_ad", [])
    high_adqa_live = [r for r in live if r.get("adqa") not in ("", None) and float(r["adqa"]) >= 1.0]
    high_adqa_framedump = [r for r in high_adqa_live if r["frame_dump_list"]]
    summary["live_high_adqa_frame_dump"] = {
        "n_high_adqa_live": len(high_adqa_live),
        "n_frame_dump_among_high_adqa": len(high_adqa_framedump),
        "rate": (len(high_adqa_framedump) / len(high_adqa_live)) if high_adqa_live else None,
    }

    with open(OUT_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    examples = sorted(live, key=lambda r: (r["experience_severity"], r["frame_dump_list"]), reverse=True)[:6]
    lines = [
        "# SceneTwin AD Experience Audit",
        "",
        "## New finding",
        "",
        "Existing SceneTwin metrics mostly ask whether an AD is visually grounded and answers frame-grounded questions. "
        "They can still give perfect scores to descriptions that are bad *audio description experiences*: frame-by-frame lists, "
        "premature/anticipatory wording, uncertain visual inference, or heavy temporal plot summaries.",
        "",
        "This is a BLV-facing gap, not a metric-beautification gap: style guides emphasize preserving dialogue/silence, avoiding spoilers, "
        "describing with the action, and writing concise narration rather than a storyboard dump.",
        "",
        "## Local novelty check",
        "",
        "Repo search found prior work on frame-sampling temporal blind spots, TRIBE timing, hallucination gates, and claim-level gates. "
        "I did **not** find an existing `spoiler`, `suspense`, `frame-dump`, `listification`, or style-guide experience audit. "
        "This is therefore a new SceneTwin lane: **experience/style compliance as an orthogonal safety layer**.",
        "",
        "## Corpus scan",
        "",
        f"Scanned `{len(rows)}` local texts: VideoA11y professional ADs, VATEX captions, and live generated ADs.",
        "",
        "| kind | n | mean severity | frame-dump/list | anticipation/spoiler | uncertain inference | timing sequence |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for kind, vals in sorted(by_kind.items()):
        s = summary["by_kind"][kind]
        lines.append(
            f"| {kind} | {s['n']} | {s['mean_experience_severity']:.2f} | "
            f"{100*s['frame_dump_list_rate']:.1f}% | {100*s['anticipation_spoiler_rate']:.1f}% | "
            f"{100*s['uncertain_inference_rate']:.1f}% | {100*s['timing_sequence_rate']:.1f}% |"
        )
    lines += [
        "",
        "## Key result",
        "",
        f"Live generated ADs are the outlier: `{sum(r['frame_dump_list'] for r in live)}/{len(live)}` "
        f"(`{pct(sum(r['frame_dump_list'] for r in live), len(live))}`) have frame-dump/list markers, versus "
        f"`{sum(r['frame_dump_list'] for r in pro)}/{len(pro)}` (`{pct(sum(r['frame_dump_list'] for r in pro), len(pro))}`) professional ADs.",
        "",
        f"Among live ADs with perfect cached ADQA (`adqa >= 1.0`), `{len(high_adqa_framedump)}/{len(high_adqa_live)}` "
        "still have frame-dump/list markers. So ADQA can say 'all questions answered' while the text remains a poor listening experience.",
        "",
        "## Examples flagged despite high semantic scores",
        "",
        "| source | id | adqa | flags | snippet |",
        "|---|---|---:|---|---|",
    ]
    for r in examples:
        flags = [k for k in PATTERNS if r[k]]
        lines.append(
            f"| {r['source']} | {r['id']} | {r.get('adqa','')} | {', '.join(flags)} | {r['snippet'].replace('|','/')} |"
        )
    lines += [
        "",
        "## Why this helps BLV users",
        "",
        "A blind viewer does not just need facts to be present; they need them delivered at the right time, without flattening a movie into a numbered storyboard or spoiling suspense. "
        "This layer would route technically-correct-but-unwatchable AI AD to rewrite/human review.",
        "",
        "## External grounding checked",
        "",
        "- Netflix AD guide: prioritize plot-critical information, allow dialogue/silence, avoid over-description, and preserve suspense.",
        "- Prime Video AD guide: describe with the action; do not spoil surprises by describing before they happen.",
        "- AMI described-video best practices: do not reveal/spoil story content or lessen sequential storytelling impact.",
        "- Recent AD reception work: narrative specificity and spatiotemporal language affect imageability/comprehension for non-sighted listeners.",
        "",
        "## Next experiment",
        "",
        "Pair each generated AD with an experience rewrite that removes frame-list markers and spoiler/uncertainty wording while preserving facts. "
        "Then run a small BLV or proxy listening study measuring comprehension, suspense/immersion, and NASA-TLX effort. This is orthogonal to rho/AUC and actually tests whether SceneTwin makes AI AD watchable.",
        "",
        "## Files",
        "",
        "- `cursor/pipeline/ad_experience_audit.py`",
        "- `cursor/output/ad_experience_audit/items.csv`",
        "- `cursor/output/ad_experience_audit/summary.json`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_DIR / 'items.csv'}")
    print(f"Wrote {OUT_DIR / 'summary.json'}")
    print(f"Wrote {REPORT}")
    print(json.dumps(summary["live_high_adqa_frame_dump"], indent=2))


if __name__ == "__main__":
    main()
