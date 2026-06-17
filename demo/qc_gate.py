"""Generalizable QC risk score — calibrated on external YouTube clips only.

Not a list of bad benchmark clips. Same formula everywhere:
  need−speech, peak/words, CLIP(t3−t1), read time → sigmoid blend → risk 0–1
Flag = top 20% by external calibration (p80 ≈ 0.55).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from textwrap import dedent

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
CALIB_PATH = ROOT / "cursor" / "data" / "qc_calibration.json"
DATA_JSON = ROOT / "cursor" / "data" / "qc_gate.json"
WPM = 200


def _load_calib() -> dict:
    if CALIB_PATH.exists():
        return json.loads(CALIB_PATH.read_text(encoding="utf-8"))
    # fallback if calibration not run yet
    from pathlib import Path as P
    script = ROOT / "cursor" / "metrics" / "qc_generalization_eval.py"
    if script.exists():
        import subprocess
        subprocess.run(["python3", str(script)], cwd=str(ROOT), check=False)
    return json.loads(CALIB_PATH.read_text(encoding="utf-8"))


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]{3,}", str(text).lower())


def _need_peak_from_windows(need: pd.DataFrame, clip_idx: int) -> float:
    grp = need[need["clip_idx"] == clip_idx].sort_values("start_s")
    if grp.empty:
        return 0.5
    scores = grp["need_score"].astype(float).values
    t = grp["start_s"].astype(float).values
    if scores.sum() <= 0:
        return 0.5
    com = float(np.average(t, weights=scores + 1e-6))
    dur = float(grp["end_s"].max() - grp["start_s"].min() + 1e-6)
    return com / dur


def risk_from_signals(signals: dict, cal: dict | None = None) -> float:
    cal = cal or _load_calib()
    parts = []
    for sig, w in cal["weights"].items():
        if sig not in signals:
            continue
        meta = cal["signals"][sig]
        z = (float(signals[sig]) - meta["mean"]) / meta["std"]
        if meta["direction"] == "low_bad":
            z = -z
        parts.append(w * (1 / (1 + np.exp(-z))))
    return float(np.sum(parts)) if parts else 0.0


def _flag_reasons(signals: dict, cal: dict) -> list[dict]:
    reasons = []
    labels = {
        "need_speech_gap": ("Need vs speech", "Visual need high relative to speech density"),
        "peak_over_words": ("Late need / verbose", "Need peaks late vs word count"),
        "clip_t3_minus_t1": ("CLIP tier gain", "Pro AD CLIP not beating short caption"),
        "read_seconds": ("Read time", "Long AD read time vs external norm"),
    }
    for sig, (label, reason) in labels.items():
        if sig not in signals:
            continue
        meta = cal["signals"][sig]
        val = float(signals[sig])
        hot = val >= meta["p80"] if meta["direction"] == "high_bad" else val <= meta["p50"]
        if hot:
            reasons.append({"id": sig, "label": label, "value": round(val, 4), "reason": reason})
    return reasons


def build_benchmark_qc() -> list[dict]:
    cal = _load_calib()
    fc = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    need = pd.read_csv(TIMING / "need" / "coarse_need_windows.csv")
    ens = pd.read_csv(TIMING / "ensemble" / "adqa_clip_ensemble_scores.csv")
    need_agg = need.groupby("clip_idx").agg(
        need_mean=("need_score", "mean"),
        speech_mean=("speech_density", "mean"),
    )

    clips = []
    for cidx in sorted(fc["clip_idx"].unique()):
        tr = fc[fc["clip_idx"] == cidx].iloc[0]
        words = int(tr.get("tier3_va11y_words_feature", tr.get("tier3_va11y_words", 40)))
        read_s = max(words, 1) / (WPM / 60.0)
        na = need_agg.loc[cidx] if cidx in need_agg.index else None
        t3 = ens[(ens["clip_idx"] == cidx) & (ens["tier"] == "tier3_va11y")]
        t1 = ens[(ens["clip_idx"] == cidx) & (ens["tier"] == "tier1_vatex_short")]
        clip_t3 = float(t3.iloc[0]["clip_top3"]) if not t3.empty else 0.0
        clip_t1 = float(t1.iloc[0]["clip_top3"]) if not t1.empty else 0.0
        ens_raw = float(t3.iloc[0]["ensemble_mean_clip_top3"]) if not t3.empty else 0.0

        signals = {
            "need_speech_gap": float(na["need_mean"] - na["speech_mean"]) if na is not None else 0.0,
            "peak_over_words": _need_peak_from_windows(need, int(cidx)) / (words + 1),
            "clip_t3_minus_t1": clip_t3 - clip_t1,
            "read_seconds": read_s,
        }
        risk = risk_from_signals(signals, cal)
        flagged = risk >= cal["risk_p80"]
        flags = _flag_reasons(signals, cal)
        clips.append({
            "clip_idx": int(cidx),
            "category": str(tr.get("category", "")),
            "risk_score": round(risk, 4),
            "flagged": flagged,
            "signals": {k: round(v, 4) for k, v in signals.items()},
            "flags": flags,
            "ensemble_raw": round(ens_raw, 4),
            "ensemble_gated": round(ens_raw * (1 - 0.35 * risk), 4),
            "summary": (
                "High generalization risk — pro CLIP gain weak or timing/load mismatch vs external norm."
                if flagged else
                "Within external-calibrated norm — ensemble rank more trustworthy."
            ),
            "calibration": "external_58_clips",
        })
    return clips


def export_qc_json(path: Path | None = None) -> dict:
    path = path or DATA_JSON
    cal = _load_calib()
    clips = build_benchmark_qc()
    payload = {
        "n": len(clips),
        "calibration_source": cal.get("source"),
        "n_external_calibration": cal.get("n_external"),
        "flag_rule": cal.get("flag_rule"),
        "risk_p80": cal.get("risk_p80"),
        "external_auc": cal.get("external_auc"),
        "clips": clips,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def load_qc_benchmark() -> dict:
    if DATA_JSON.exists():
        try:
            return json.loads(DATA_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return export_qc_json()


def qc_for_clip(clip_idx: int) -> dict | None:
    data = load_qc_benchmark()
    for c in data.get("clips", []):
        if int(c["clip_idx"]) == int(clip_idx):
            return c
    return None


def gate_ensemble(raw: float, risk: float) -> float:
    return float(raw) * (1 - 0.35 * float(risk))


def assess_live(
    clip_top3: float,
    adqa_score: float,
    ad_text: str,
    duration_s: float = 10.0,
    clip_short_ref: float | None = None,
) -> dict:
    """Live audit: only signals available without benchmark ADQA."""
    cal = _load_calib()
    words = max(len(ad_text.split()), 1)
    read_s = words / (WPM / 60.0)
    signals = {"read_seconds": read_s}
    if clip_short_ref is not None:
        signals["clip_t3_minus_t1"] = clip_top3 - clip_short_ref
    risk = risk_from_signals(signals, cal)
    # live: no need curve → cap risk using CLIP/ADQA gap as diagnostic only
    fgg = clip_top3 - adqa_score
    flags = _flag_reasons(signals, cal)
    if fgg > 0.2:
        flags.append({
            "id": "false_grounding_gap",
            "label": "CLIP vs ADQA",
            "reason": "CLIP exceeds ADQA — possible false grounding (live diagnostic).",
        })
        risk = min(1.0, risk + 0.1)
    flagged = risk >= cal["risk_p80"]
    return {
        "risk_score": round(risk, 4),
        "flagged": flagged,
        "flags": flags,
        "summary": (
            "Elevated risk vs external-calibrated norm (read time / CLIP gain)."
            if flagged else
            "No elevated risk on available live signals."
        ),
        "signals": {
            "read_seconds": round(read_s, 2),
            "false_grounding_gap": round(fgg, 4),
            **({k: round(v, 4) for k, v in signals.items()}),
        },
        "calibration": "external_58_clips",
    }


def render_qc_html(qc: dict) -> str:
    if not qc:
        return ""
    flagged = qc.get("flagged", False)
    color = "#b73558" if flagged else "#0d7f83"
    title = "Elevated generalization risk" if flagged else "Within external norm"
    flags = qc.get("flags") or []
    flag_lines = "".join(
        f"<li><b>{f.get('label', f.get('id'))}</b>: {f.get('reason', '')}</li>"
        for f in flags
    )
    cal_note = qc.get("calibration", "external")
    sig = qc.get("signals") or {}
    sig_lines = " · ".join(f"{k.replace('_', ' ')}: <b>{v}</b>" for k, v in sig.items())
    ens_block = ""
    if "ensemble_raw" in qc and "ensemble_gated" in qc:
        ens_block = dedent(f"""
        <div style="margin-top:0.5em;font-size:0.9em">
          Suggested down-weight: <b>{qc['ensemble_raw']:.2f}</b> → <b style="color:{color}">{qc['ensemble_gated']:.2f}</b>
        </div>
        """)
    return dedent(f"""
    <div class="st-card" style="border:2px solid {color}">
      <div style="font-weight:800;color:{color} !important;font-size:1.05em">{title}</div>
      <div style="font-size:1.4em;font-weight:900;color:{color} !important">
        risk {qc.get('risk_score', 0):.2f}
      </div>
      <div class="st-muted" style="font-size:0.85em">Calibrated on {cal_note} — not benchmark clip IDs</div>
      <div class="st-muted" style="font-size:0.9em;margin:0.4em 0">{qc.get('summary', '')}</div>
      {f'<ul style="margin:0.3em 0 0 1em;font-size:0.85em">{flag_lines}</ul>' if flag_lines else ''}
      {f'<div class="st-muted" style="font-size:0.8em;margin-top:0.5em">{sig_lines}</div>' if sig_lines else ''}
      {ens_block}
    </div>
    """)


if __name__ == "__main__":
    _load_calib()
    out = export_qc_json()
    n = sum(1 for c in out["clips"] if c["flagged"])
    print(f"Wrote {DATA_JSON} — {n}/{out['n']} flagged (external p80 rule)")
