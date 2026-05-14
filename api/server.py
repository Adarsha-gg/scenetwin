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
from live_presets import LIVE_DEMO_PRESETS  # noqa: E402


class StageResult(BaseModel):
    name: str
    ok: bool
    message: str


class Preset(BaseModel):
    label: str
    url: str
    clip_top3: Optional[float] = None
    adqa_score: Optional[float] = None


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
    return [
        Preset(
            label=label,
            url=url,
            clip_top3=_preset_score(label, "CLIP "),
            adqa_score=_preset_score(label, "ADQA "),
        )
        for label, url in LIVE_DEMO_PRESETS.items()
    ]


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
