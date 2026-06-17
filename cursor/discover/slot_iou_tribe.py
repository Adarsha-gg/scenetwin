#!/usr/bin/env python3
"""CA3D-style slot IoU (arxiv 2412.10002): TRIBE need windows vs generated AD slots.

No ρ. Reports precision/recall/F1 of temporal placement alignment.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
NEED = ROOT / "output" / "scenetwin_timing_20clip" / "need" / "coarse_need_windows.csv"
GEN = Path(__file__).resolve().parents[1] / "methods" / "output" / "generated_ad"
OUT = Path(__file__).resolve().parent / "output" / "slot_iou.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "discover-slot-iou.md"
IOU_THRESH = 0.1


def iou(a0: float, a1: float, b0: float, b1: float) -> float:
    inter = max(0.0, min(a1, b1) - max(a0, b0))
    union = max(a1, b1) - min(a0, b0)
    return inter / union if union > 0 else 0.0


def load_slots(clip_idx: int) -> list[tuple[float, float]]:
    p = GEN / f"clip_{clip_idx:02d}_slots.jsonl"
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        out.append((float(o["start_s"]), float(o["end_s"])))
    return out


def main() -> None:
    need = pd.read_csv(NEED)
    need_slots = need[need["recommendation"] != "low_ad_need"]
    rows = []
    for cidx in sorted(need["clip_idx"].unique()):
        gt = [(float(r.start_s), float(r.end_s)) for r in need_slots[need_slots["clip_idx"] == cidx].itertuples()]
        pred = load_slots(int(cidx))
        if not gt:
            continue
        matched_gt = set()
        matched_pred = set()
        for pi, (p0, p1) in enumerate(pred):
            best_i, best_iou = -1, 0.0
            for gi, (g0, g1) in enumerate(gt):
                v = iou(p0, p1, g0, g1)
                if v > best_iou:
                    best_iou, best_i = v, gi
            if best_iou >= IOU_THRESH:
                matched_pred.add(pi)
                matched_gt.add(best_i)
        prec = len(matched_pred) / max(len(pred), 1)
        rec = len(matched_gt) / max(len(gt), 1)
        f1 = 2 * prec * rec / max(prec + rec, 1e-9)
        rows.append({"clip_idx": int(cidx), "n_gt": len(gt), "n_pred": len(pred), "precision": prec, "recall": rec, "f1": f1})

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    mean_f1 = df["f1"].mean()
    FINDINGS.write_text(
        f"# Slot IoU: TRIBE windows vs GenAD slots (CA3D metric)\n\n"
        f"Mean F1 @ IoU≥{IOU_THRESH}: **{mean_f1:.3f}**\n\n"
        f"Worst clips:\n{df.nsmallest(5,'f1').to_string(index=False)}\n\n"
        f"**Use case:** tune slot generator before LLM fill — placement is a first-class metric.\n",
        encoding="utf-8",
    )
    print(df.describe())
    print(f"Mean F1={mean_f1:.3f} → {OUT}")


if __name__ == "__main__":
    main()
