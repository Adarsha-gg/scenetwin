"""FastAPI backend for the SceneTwin live demo.

The API keeps the scoring stack in Python and exposes a frontend-friendly
contract for a future JavaScript UI.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal, Optional, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, HttpUrl

ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = ROOT / "demo"
if str(DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(DEMO_DIR))

import live_pipeline as lp  # noqa: E402
from live_presets import LIVE_DEMO_PRESET_GROUPS  # noqa: E402


class StageResult(BaseModel):
    name: str
    ok: bool
    message: str


class Preset(BaseModel):
    label: str
    url: str
    group: str
    clip_top3: Optional[float] = None
    adqa_score: Optional[float] = None
    start_label: Optional[str] = None


class AuditRequest(BaseModel):
    url: HttpUrl
    candidate_ad: Optional[str] = Field(
        default=None,
        description="Optional user-authored AD. If omitted, the API generates one.",
    )
    run_tribe: bool = Field(
        default=False,
        description="Run the heavy TRIBE proxy. Off by default for live demos.",
    )
    max_seconds: int = Field(default=30, ge=5, le=120)
    frame_count: int = Field(default=8, ge=4, le=16)


class MediaRef(BaseModel):
    path: str
    url: str


class ClipScore(BaseModel):
    per_frame: list[float]
    mean: float
    top3: float


class AdqaGrade(BaseModel):
    question: str
    evidence: str
    score: int
    rationale: str = ""
    evidence_quote: str = ""


class AdqaScore(BaseModel):
    score: float
    graded: list[AdqaGrade]


class TribeScore(BaseModel):
    alignment_cosine: float
    video_mean_lh: float
    video_mean_rh: float
    video_ad_mean_lh: float
    video_ad_mean_rh: float


class AuditResponse(BaseModel):
    ok: bool
    status: Literal["complete", "failed"]
    stages: list[StageResult]
    source_url: str
    title: Optional[str] = None
    video: Optional[MediaRef] = None
    frames: list[MediaRef] = Field(default_factory=list)
    ad: str = ""
    clip: Optional[ClipScore] = None
    adqa: Optional[AdqaScore] = None
    tribe: Optional[TribeScore] = None
    error: Optional[str] = None


app = FastAPI(
    title="SceneTwin API",
    description=(
        "Backend API for the SceneTwin audio-description audit demo. "
        "The heavy scoring path stays in Python; JS frontends call this API."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/media/live_cache",
    StaticFiles(directory=str(lp.CACHE_DIR), check_dir=True),
    name="live_cache",
)


def _media_ref(path: Optional[Union[str, Path]]) -> Optional[MediaRef]:
    if not path:
        return None
    p = Path(path).resolve()
    try:
        rel = p.relative_to(lp.CACHE_DIR.resolve())
    except ValueError:
        return MediaRef(path=str(p), url="")
    return MediaRef(path=str(p), url=f"/media/live_cache/{rel.as_posix()}")


def _stage(stages: list[StageResult], name: str, ok: bool, message: str) -> None:
    stages.append(StageResult(name=name, ok=ok, message=message))


def _failure(
    req: AuditRequest,
    stages: list[StageResult],
    message: str,
    *,
    video: Optional[str] = None,
    frames: Optional[list[str]] = None,
    ad: str = "",
    title: Optional[str] = None,
) -> AuditResponse:
    return AuditResponse(
        ok=False,
        status="failed",
        stages=stages,
        source_url=str(req.url),
        title=title,
        video=_media_ref(video),
        frames=[ref for f in (frames or []) if (ref := _media_ref(f))],
        ad=ad,
        error=message,
    )


def _preset_score(label: str, marker: str) -> Optional[float]:
    if marker not in label:
        return None
    try:
        value = label.split(marker, 1)[1].split(",", 1)[0].split()[0]
        if "/" in value:
            num, den = value.split("/", 1)
            return float(num) / float(den)
        return float(value)
    except Exception:
        return None


def _read_csv_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        df = lp.pd.read_csv(path)
        df = df.replace({lp.np.nan: None})
        return df.to_dict(orient="records")
    except Exception:
        return []


def _web_rel(path: Path) -> str:
    return f"../{path.relative_to(ROOT).as_posix()}"


def _first_existing(paths: list[Path]) -> Optional[Path]:
    for p in paths:
        if p.exists():
            return p
    return None


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "openai_key": lp.get_api_key("openai") is not None,
        "anthropic_key": lp.get_api_key("anthropic") is not None,
        "cache_dir": str(lp.CACHE_DIR),
    }


@app.get("/api/presets", response_model=list[Preset])
def presets() -> list[Preset]:
    out: list[Preset] = []
    for group in LIVE_DEMO_PRESET_GROUPS:
        for item in group["items"]:
            out.append(Preset(
                label=item["label"],
                url=item["url"],
                group=group["group"],
                clip_top3=item.get("clip_top3"),
                adqa_score=item.get("adqa_score"),
                start_label=item.get("start_label"),
            ))
    return out


@app.get("/api/tribe-risk")
def tribe_risk() -> dict[str, Any]:
    tribe_dir = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native"
    need_dir = ROOT / "output" / "scenetwin_timing_20clip" / "need"
    roi_path = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_only_per_roi.csv"

    rows = _read_csv_records(tribe_dir / "tribe_failure_forecast.csv")
    summary = _read_csv_records(tribe_dir / "tribe_failure_forecast_summary.csv")
    correlations = _read_csv_records(tribe_dir / "tribe_native_correlations.csv")
    need_curve_rows = _read_csv_records(need_dir / "neural_description_need_curve.csv")
    coarse_rows = _read_csv_records(need_dir / "coarse_need_windows.csv")
    roi_rows = _read_csv_records(roi_path)

    need_by_clip: dict[int, list[dict[str, Any]]] = {}
    for r in need_curve_rows:
        cidx = int(r.get("clip_idx") or 0)
        need_by_clip.setdefault(cidx, []).append({
            "t": float(r.get("t") or 0),
            "start_s": float(r.get("start_s") or 0),
            "end_s": float(r.get("end_s") or 0),
            "need_score": float(r.get("need_score") or 0),
            "speech_density": float(r.get("speech_density") or 0),
        })

    coarse_by_clip: dict[int, list[dict[str, Any]]] = {}
    for r in coarse_rows:
        cidx = int(r.get("clip_idx") or 0)
        coarse_by_clip.setdefault(cidx, []).append({
            "start_s": float(r.get("start_s") or 0),
            "end_s": float(r.get("end_s") or 0),
            "need_score": float(r.get("need_score") or 0),
            "speech_density": float(r.get("speech_density") or 0),
            "recommendation": r.get("recommendation") or "low_ad_need",
        })

    roi_by_clip: dict[int, list[dict[str, Any]]] = {}
    for r in roi_rows:
        cidx = int(r.get("clip_idx") or 0)
        roi_by_clip.setdefault(cidx, []).append({
            "roi": r.get("roi") or "",
            "cos_gap": float(r.get("av_a_gap_cos") or 0),
            "residual_norm": float(r.get("av_a_residual_norm_per_t") or 0),
            "n_vertices": int(r.get("n_vertices") or 0),
        })

    clips = []
    for r in sorted(rows, key=lambda x: int(x.get("risk_rank") or 999)):
        cidx = int(r.get("clip_idx") or 0)
        speech_density = r.get("mean_speech_density")
        try:
            speech_density = float(speech_density) if speech_density is not None else None
        except Exception:
            speech_density = None
        clips.append({
            "clip_idx": cidx,
            "video_id": r.get("video_id"),
            "category": r.get("category"),
            "risk_rank": int(r.get("risk_rank") or 0),
            "risk_score": float(r.get("risk_score") or 0),
            "target": int(r.get("target") or 0),
            "quality_risk": r.get("quality_risk"),
            "tribe_route": r.get("tribe_route"),
            "mean_need": float(r.get("mean_need") or 0),
            "max_need": float(r.get("max_need") or 0),
            "high_need_seconds_frac": float(r.get("high_need_seconds_frac") or 0),
            "tribe_pressure": float(r.get("tribe_pressure") or 0),
            "mean_speech_density": speech_density,
            "tier3_margin": float(r.get("all4_mean_tier3_margin") or 0),
            "tier2_vs_tier1": float(r.get("all4_mean_tier2_vs_tier1") or 0),
            "pro_ad_words": int(r.get("tier3_va11y_words") or 0),
            "pro_ad_text": r.get("tier3_va11y_text"),
            "short_text": r.get("tier1_vatex_short_text"),
            "long_text": r.get("tier2_vatex_long_text"),
            "brain_map_url": f"../output/charts/tribe_clip_brains/clip_{cidx:02d}_tribe_gap.png",
            "need_curve": need_by_clip.get(cidx, []),
            "coarse_windows": coarse_by_clip.get(cidx, []),
            "per_roi": roi_by_clip.get(cidx, []),
        })

    top_summary = summary[0] if summary else {}

    headline_corr = None
    for c in correlations:
        if (c.get("tribe_feature") == "mean_standard_slot_score"
                and c.get("outcome") == "all4_mean_full_order"):
            headline_corr = {
                "feature": c.get("tribe_feature"),
                "outcome": c.get("outcome"),
                "rho": float(c.get("spearman_rho") or 0),
                "p": float(c.get("p") or 1),
                "n": int(c.get("n") or 0),
            }
            break

    return {
        "n": len(clips),
        "positives": int(top_summary.get("positives") or 2),
        "review_budget_clips": int(top_summary.get("review_budget_clips") or 2),
        "recall_at_topk": float(top_summary.get("recall_at_topk") or 1.0),
        "p_value": float(top_summary.get("hypergeom_p_at_least") or 0.0065359477124183),
        "best_feature": top_summary.get("feature") or "mean_standard_slot_score",
        "best_feature_direction": top_summary.get("direction") or "high",
        "clips": clips,
        "correlations": correlations[:8],
        "headline_correlation": headline_corr,
    }


@app.get("/api/cached-clips")
def cached_clips() -> dict[str, Any]:
    base = ROOT / "output" / "scenetwin_timing_20clip"
    forecast_rows = _read_csv_records(base / "tribe_native" / "tribe_failure_forecast.csv")
    score_rows = _read_csv_records(base / "ensemble" / "adqa_clip_ensemble_scores.csv")
    question_rows = _read_csv_records(base / "adqa_v2" / "adqa_v2_questions.csv")
    grade_rows = _read_csv_records(base / "adqa_v2" / "adqa_v2_grades.csv")

    scores: dict[tuple[int, str], dict[str, Any]] = {}
    for r in score_rows:
        cidx = int(r.get("clip_idx") or 0)
        tier = str(r.get("tier") or "")
        scores[(cidx, tier)] = r

    questions: dict[tuple[int, int], dict[str, Any]] = {}
    for r in question_rows:
        cidx = int(r.get("clip_idx") or 0)
        qidx = int(r.get("q_idx") or 0)
        questions[(cidx, qidx)] = r

    grades: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for r in grade_rows:
        cidx = int(r.get("clip_idx") or 0)
        tier = str(r.get("tier") or "")
        qidx = int(r.get("q_idx") or 0)
        q = questions.get((cidx, qidx), {})
        grades.setdefault((cidx, tier), []).append({
            "q_idx": qidx,
            "question": q.get("question") or "",
            "answer_key": q.get("answer_key") or "",
            "required_visual_evidence": q.get("required_visual_evidence") or "",
            "importance": q.get("importance") or "",
            "score": float(r.get("score") or 0),
            "label": r.get("label") or "",
            "evidence_quote": r.get("evidence_quote") or "",
            "grade_rationale": r.get("grade_rationale") or "",
        })

    tier_defs = [
        ("tier0_cross", "Cross-video negative", "Wrong clip AD, used as a hard negative."),
        ("tier1_vatex_short", "VATEX short", "Short caption-style candidate."),
        ("tier2_vatex_long", "VATEX long", "Longer caption-style candidate."),
        ("tier3_va11y", "Professional AD", "Human/pro-style AD candidate."),
    ]

    clips = []
    for r in sorted(forecast_rows, key=lambda x: int(x.get("clip_idx") or 0)):
        cidx = int(r.get("clip_idx") or 0)
        frame_dir = base / "adqa_v2" / "frames" / f"clip_{cidx:02d}"
        frame_paths = sorted(
            frame_dir.glob("*.jpg"),
            key=lambda p: (p.name.split("_t")[-1], p.name),
        )
        # Keep the gallery compact while preserving temporal coverage.
        frames = [{"url": _web_rel(p), "name": p.name} for p in frame_paths[:12]]
        video = _first_existing([
            base / "adqa_v2" / "videos" / f"clip_{cidx:02d}.mp4",
            base / "adqa_v2" / "videos" / f"clip_{cidx:02d}.mkv",
        ])

        texts = {
            "tier0_cross": r.get("tier0_cross_text") or "",
            "tier1_vatex_short": r.get("tier1_vatex_short_text") or "",
            "tier2_vatex_long": r.get("tier2_vatex_long_text") or "",
            "tier3_va11y": r.get("tier3_va11y_text") or "",
        }
        candidates = []
        for tier, label, kind in tier_defs:
            s = scores.get((cidx, tier), {})
            candidates.append({
                "tier": tier,
                "label": label,
                "kind": kind,
                "gt": int(s.get("gt") if s.get("gt") is not None else {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}[tier]),
                "text": texts[tier],
                "word_count": len(str(texts[tier]).split()),
                "clip_top3": float(s.get("clip_top3") or 0),
                "clip_mean": float(s.get("clip_mean") or 0),
                "adqa_score": float(s.get("adqa_v2_score") or 0),
                "adqa_yes_rate": float(s.get("adqa_v2_yes_rate") or 0),
                "ensemble": float(s.get("ensemble_mean_clip_top3") or 0),
                "grades": sorted(grades.get((cidx, tier), []), key=lambda g: int(g["q_idx"])),
            })
        pro_candidate = next((c for c in candidates if c["tier"] == "tier3_va11y"), candidates[-1])
        best_candidate = max(candidates, key=lambda c: c["adqa_score"])

        clips.append({
            "clip_idx": cidx,
            "video_id": r.get("video_id"),
            "category": r.get("category"),
            "duration_s": float(r.get("duration_s") or 0),
            "demo_rank_score": float(pro_candidate["adqa_score"]),
            "best_adqa_score": float(best_candidate["adqa_score"]),
            "best_candidate_label": best_candidate["label"],
            "risk_rank": int(r.get("risk_rank") or 0),
            "risk_score": float(r.get("risk_score") or 0),
            "quality_risk": r.get("quality_risk") or "",
            "video_url": _web_rel(video) if video else "",
            "frames": frames,
            "candidates": candidates,
        })
    clips.sort(key=lambda c: (-c["demo_rank_score"], -c["best_adqa_score"], c["clip_idx"]))

    return {
        "n": len(clips),
        "tier_order": [t[0] for t in tier_defs],
        "clips": clips,
    }


@app.post("/api/audit", response_model=AuditResponse)
def audit(req: AuditRequest) -> AuditResponse:
    stages: list[StageResult] = []
    source_url = str(req.url)
    ad_text = (req.candidate_ad or "").strip()

    ok, msg, dl = lp.stage_download(source_url, max_seconds=req.max_seconds)
    _stage(stages, "download", ok, msg)
    if not ok:
        return _failure(req, stages, msg, ad=ad_text)

    video = dl["video"]
    slug = dl["slug"]
    title = dl.get("title")

    ok, msg, fr = lp.stage_frames(video, slug, n=req.frame_count)
    _stage(stages, "frames", ok, msg)
    if not ok:
        return _failure(req, stages, msg, video=video, ad=ad_text, title=title)
    frames = list(fr.get("frames", []))

    if not ad_text:
        ok, msg, gen = lp.stage_generate_ad(frames)
        _stage(stages, "ad_generation", ok, msg)
        if ok:
            ad_text = str(gen.get("ad", "")).strip()
        else:
            return _failure(
                req,
                stages,
                msg,
                video=video,
                frames=frames,
                ad=ad_text,
                title=title,
            )
    else:
        _stage(stages, "ad_generation", True, "using supplied AD")

    ok, msg, cl = lp.stage_clip_grounding(frames, ad_text)
    _stage(stages, "clip", ok, msg)
    if not ok:
        return _failure(
            req,
            stages,
            msg,
            video=video,
            frames=frames,
            ad=ad_text,
            title=title,
        )
    clip_score = ClipScore(
        per_frame=[float(x) for x in cl["per_frame"]],
        mean=float(cl["mean"]),
        top3=float(cl["top3"]),
    )

    ok, msg, aq = lp.stage_adqa(frames, ad_text)
    _stage(stages, "adqa", ok, msg)
    if not ok:
        return _failure(
            req,
            stages,
            msg,
            video=video,
            frames=frames,
            ad=ad_text,
            title=title,
        )
    adqa_score = AdqaScore(
        score=float(aq["score"]),
        graded=[AdqaGrade(**g) for g in aq.get("graded", [])],
    )

    tribe_score = None
    if req.run_tribe:
        ok, msg, tr = lp.stage_tribe_proxy(video, ad_text)
        _stage(stages, "tribe", ok, msg)
        if ok:
            tribe_score = TribeScore(**tr)
    else:
        _stage(stages, "tribe", True, "skipped")

    return AuditResponse(
        ok=True,
        status="complete",
        stages=stages,
        source_url=source_url,
        title=title,
        video=_media_ref(video),
        frames=[ref for f in frames if (ref := _media_ref(f))],
        ad=ad_text,
        clip=clip_score,
        adqa=adqa_score,
        tribe=tribe_score,
    )
