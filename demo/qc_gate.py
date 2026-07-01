"""Local QC helpers for the SceneTwin demo.

This module is intentionally lightweight: it reads only cached CSV artifacts and
uses simple display heuristics. It does not call LLM APIs, TRIBE, YouTube, or any
external service. The QC gate is a review prompt, not a replacement score.
"""
from __future__ import annotations

import csv
import html
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
FORECAST_CSV = TIMING / "tribe_native" / "tribe_failure_forecast.csv"
ENSEMBLE_CSV = TIMING / "ensemble" / "adqa_clip_ensemble_scores.csv"
SUMMARY_CSV = TIMING / "tribe_native" / "tribe_failure_forecast_summary.csv"


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return default
        return out
    except Exception:
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _norm(value: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def gate_ensemble(ensemble: float, risk_score: float) -> float:
    """Display-only conservative score after a QC review penalty.

    ``risk_score`` is expected to be normalized 0..1 for cached clips. The
    returned value is only used in UI copy to say "review this before trusting
    the raw score"; it is not a paper metric.
    """
    ensemble = max(0.0, min(1.0, _float(ensemble)))
    risk = max(0.0, min(1.0, _float(risk_score)))
    penalty = 0.20 * risk
    return max(0.0, ensemble - penalty)


def _pro_ensemble_by_clip() -> dict[int, float]:
    out: dict[int, float] = {}
    for row in _read_csv(ENSEMBLE_CSV):
        if row.get("tier") != "tier3_va11y":
            continue
        cidx = _int(row.get("clip_idx"), -1)
        if cidx < 0:
            continue
        # Match the Gradio demo's displayed ensemble column.
        out[cidx] = _float(row.get("ensemble_mean_clip_mean"))
    return out


def _summary() -> dict[str, Any]:
    rows = _read_csv(SUMMARY_CSV)
    if not rows:
        return {
            "positives": 0,
            "review_budget_clips": 0,
            "recall_at_topk": 0.0,
            "p_value": None,
        }
    r = rows[0]
    return {
        "positives": _int(r.get("positives")),
        "review_budget_clips": _int(r.get("review_budget_clips")),
        "recall_at_topk": _float(r.get("recall_at_topk")),
        "p_value": _float(r.get("hypergeom_p_at_least"), default=float("nan")),
        "feature": r.get("feature") or "mean_standard_slot_score",
        "target": r.get("target") or "all4_fail",
    }


def _flag(flag_id: str, label: str, reason: str, *, value: float | None = None,
          norm: float | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"id": flag_id, "label": label, "reason": reason}
    if value is not None:
        out["value"] = float(value)
    if norm is not None:
        out["norm"] = float(max(0.0, min(1.0, norm)))
    return out


def load_qc_benchmark() -> dict[str, Any]:
    """Return cached benchmark QC flags for the API and Gradio demo."""
    rows = _read_csv(FORECAST_CSV)
    if not rows:
        return {
            "ok": False,
            "source": str(FORECAST_CSV.relative_to(ROOT)),
            "method": "cached local QC gate",
            "n": 0,
            "flagged_n": 0,
            "clips": [],
            "top_flagged": [],
            "summary": "No cached QC benchmark was found.",
        }

    summary = _summary()
    pro_ensemble = _pro_ensemble_by_clip()
    raw_risks = [_float(r.get("risk_score", r.get("mean_standard_slot_score"))) for r in rows]
    risk_lo = min(raw_risks) if raw_risks else 0.0
    risk_hi = max(raw_risks) if raw_risks else 1.0
    review_budget = max(1, _int(summary.get("review_budget_clips"), 2))

    clips: list[dict[str, Any]] = []
    for row in rows:
        cidx = _int(row.get("clip_idx"), -1)
        raw_risk = _float(row.get("risk_score", row.get("mean_standard_slot_score")))
        risk_norm = _norm(raw_risk, risk_lo, risk_hi)
        risk_rank = _int(row.get("risk_rank"), 999)
        target = bool(_int(row.get("target", row.get("all4_fail"))))
        margin = _float(row.get("all4_mean_tier3_margin"))
        tier2_vs_tier1 = _float(row.get("all4_mean_tier2_vs_tier1"))
        max_need = _float(row.get("max_need"))
        high_need_frac = _float(row.get("high_need_seconds_frac"))
        quality_risk = (row.get("quality_risk") or "").strip()

        flags: list[dict[str, Any]] = []
        if target:
            flags.append(_flag(
                "known_benchmark_failure",
                "Known full-order failure",
                "Cached ADQA/CLIP ensemble misordered at least one tier on this benchmark clip.",
                value=1.0,
                norm=1.0,
            ))
        if risk_rank <= review_budget:
            flags.append(_flag(
                "top_review_budget",
                "Top TRIBE review priority",
                f"Ranks #{risk_rank} in the cached TRIBE risk queue.",
                value=float(risk_rank),
                norm=1.0 - ((risk_rank - 1) / max(review_budget, 1)),
            ))
        if margin < 0.08:
            flags.append(_flag(
                "low_professional_margin",
                "Professional AD barely leads",
                "The professional-AD tier has a small or negative score margin.",
                value=margin,
                norm=1.0 - _norm(margin, 0.0, 0.35),
            ))
        if tier2_vs_tier1 < 0.02:
            flags.append(_flag(
                "tier_inversion",
                "Long caption does not beat short caption",
                "The long VATEX-style candidate fails to clearly beat the short one.",
                value=tier2_vs_tier1,
                norm=1.0 - _norm(tier2_vs_tier1, 0.0, 0.25),
            ))
        # High visual-access load is useful context, but by itself it is not a
        # scoring failure. Only the rank/margin/inversion checks above should
        # force a review badge.

        flagged = bool(flags)
        if flagged:
            summary_text = "Review before trusting the raw score: " + "; ".join(f["label"] for f in flags[:3]) + "."
        else:
            summary_text = "No cached QC flags; use the CLIP+ADQA score normally for this demo clip."

        ensemble_raw = pro_ensemble.get(cidx)
        clip = {
            "clip_idx": cidx,
            "video_id": row.get("video_id") or "",
            "category": row.get("category") or row.get("category_feature") or "",
            "risk_rank": risk_rank,
            "risk_score": risk_norm,
            "risk_score_raw": raw_risk,
            "flagged": flagged,
            "quality_risk": quality_risk,
            "summary": summary_text,
            "flags": flags,
            "signals": {
                "tribe_risk_raw": raw_risk,
                "tribe_risk_norm": risk_norm,
                "tier3_margin": margin,
                "tier2_vs_tier1": tier2_vs_tier1,
                "mean_need": _float(row.get("mean_need")),
                "max_need": max_need,
                "high_need_seconds_frac": high_need_frac,
                "mean_speech_density": _float(row.get("mean_speech_density")),
            },
            "ensemble_raw": ensemble_raw,
            "ensemble_gated": gate_ensemble(ensemble_raw, risk_norm) if ensemble_raw is not None else None,
        }
        clips.append(clip)

    clips.sort(key=lambda c: (c["risk_rank"], c["clip_idx"]))
    flagged = [c for c in clips if c["flagged"]]
    return {
        "ok": True,
        "source": str(FORECAST_CSV.relative_to(ROOT)),
        "method": "cached local QC gate; review prompt, not a validated replacement metric",
        "n": len(clips),
        "flagged_n": len(flagged),
        "review_budget_clips": review_budget,
        "recall_at_topk": summary.get("recall_at_topk"),
        "p_value": None if math.isnan(_float(summary.get("p_value"), float("nan"))) else summary.get("p_value"),
        "clips": clips,
        "top_flagged": flagged[:review_budget],
        "summary": (
            f"Cached QC marks {len(flagged)} of {len(clips)} clips for review. "
            "CLIP+ADQA remains the scorer; TRIBE/QC only tells presenters where to slow down."
        ),
    }


def assess_live(clip_top3: float, adqa_score: float, ad_text: str,
                duration_s: float = 30.0) -> dict[str, Any]:
    """Heuristic no-API QC for a live audit result."""
    clip_top3 = _float(clip_top3)
    adqa_score = _float(adqa_score)
    duration_s = max(1.0, _float(duration_s, 30.0))
    words = len((ad_text or "").split())
    wps = words / duration_s

    flags: list[dict[str, Any]] = []
    low_clip = max(0.0, min(1.0, (0.30 - clip_top3) / 0.30))
    low_adqa = max(0.0, min(1.0, (0.67 - adqa_score) / 0.67))
    density_risk = 0.0

    if clip_top3 < 0.25:
        flags.append(_flag(
            "low_clip_grounding",
            "Low CLIP grounding",
            "The AD text does not strongly match the sampled frames.",
            value=clip_top3,
            norm=low_clip,
        ))
    if adqa_score < 0.67:
        flags.append(_flag(
            "low_adqa",
            "ADQA misses visual questions",
            "Fewer than two of the three frame-grounded checks passed.",
            value=adqa_score,
            norm=low_adqa,
        ))
    if words < 15:
        density_risk = max(density_risk, 0.8)
        flags.append(_flag(
            "too_short",
            "Description is very short",
            "Short ADs often miss action/state details even when object words match.",
            value=float(words),
            norm=0.8,
        ))
    elif wps > 3.2:
        density_risk = max(density_risk, min(1.0, (wps - 3.2) / 2.0))
        flags.append(_flag(
            "too_dense",
            "Description may overload the viewer",
            "The generated text is dense for the clip duration; review timing/readability.",
            value=wps,
            norm=density_risk,
        ))

    risk = max(0.0, min(1.0, 0.42 * low_adqa + 0.38 * low_clip + 0.20 * density_risk))
    flagged = bool(flags) or risk >= 0.35
    ensemble_raw = max(0.0, min(1.0, 0.5 * adqa_score + 0.5 * _norm(clip_top3, 0.15, 0.40)))
    summary = (
        "Review before trusting this live score: " + "; ".join(f["label"] for f in flags[:3]) + "."
        if flagged else
        "No live QC flags from the local heuristics. Still treat live YouTube as a demo stress test, not benchmark evidence."
    )
    return {
        "risk_score": risk,
        "flagged": flagged,
        "summary": summary,
        "flags": flags,
        "signals": {
            "clip_top3": clip_top3,
            "adqa_score": adqa_score,
            "word_count": float(words),
            "words_per_second": wps,
        },
        "ensemble_raw": ensemble_raw,
        "ensemble_gated": gate_ensemble(ensemble_raw, risk),
    }


def render_qc_html(qc: dict[str, Any] | None) -> str:
    """Render a compact QC card for Gradio HTML slots."""
    if not qc:
        return "<i>QC data not loaded</i>"
    risk = _float(qc.get("risk_score"))
    flagged = bool(qc.get("flagged"))
    color = "#b73558" if flagged else "#0d7f83"
    title = "Review before trusting score" if flagged else "QC clear"
    summary = html.escape(str(qc.get("summary") or ""))
    flags = qc.get("flags") or []
    flag_html = ""
    if flags:
        items = []
        for f in flags[:5]:
            label = html.escape(str(f.get("label") or f.get("id") or "flag"))
            reason = html.escape(str(f.get("reason") or ""))
            items.append(f"<li><b>{label}</b> — {reason}</li>")
        flag_html = "<ul style='margin:0.5em 0 0 1.2em;padding:0'>" + "".join(items) + "</ul>"
    return (
        f"<div class='st-card' style='border:2px solid {color};margin-top:0.8em'>"
        f"<div style='font-weight:800;color:{color} !important'>{title}</div>"
        f"<div style='font-size:1.4em;font-weight:900;color:{color} !important;margin:0.2em 0'>"
        f"risk {risk:.2f}</div>"
        f"<div class='st-muted' style='font-size:0.9em'>{summary}</div>"
        f"{flag_html}"
        f"<div class='st-muted' style='font-size:0.82em;margin-top:0.55em'>"
        f"Local cached QC gate; CLIP+ADQA remains the score.</div>"
        f"</div>"
    )
