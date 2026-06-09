"""Live pipeline stages for the SceneTwin demo.

Each stage is fault tolerant: it returns (ok: bool, message: str, payload).
Imports are deferred so a missing optional dep disables only the affected
stage. Nothing in here is supposed to raise to the caller.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "demo" / "live_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
TRIBE_PKG = ROOT / "workspace" / "tribev2"


def _slug(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


def _youtube_start_seconds(url: str) -> float:
    """Return a YouTube start offset from t/start query params, if present."""
    try:
        qs = parse_qs(urlparse(url).query)
    except Exception:
        return 0.0
    raw = (qs.get("t") or qs.get("start") or ["0"])[0]
    if raw is None:
        return 0.0
    raw = str(raw).strip().lower()
    if raw.isdigit():
        return float(raw)
    # YouTube accepts forms like 1h2m3s, 2m10s, 45s.
    m = re.fullmatch(
        r"(?:(?P<h>\d+(?:\.\d+)?)h)?(?:(?P<m>\d+(?:\.\d+)?)m)?(?:(?P<s>\d+(?:\.\d+)?)s?)?",
        raw,
    )
    if not m:
        return 0.0
    h = float(m.group("h") or 0)
    minutes = float(m.group("m") or 0)
    seconds = float(m.group("s") or 0)
    return h * 3600 + minutes * 60 + seconds


def _read_env_file() -> dict[str, str]:
    env_path = ROOT / ".env"
    out: dict[str, str] = {}
    if not env_path.exists():
        return out
    try:
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return out


def get_api_key(provider: str) -> str | None:
    """Return an API key for the given provider, or None."""
    env = _read_env_file()
    if provider == "openai":
        return os.environ.get("OPENAI_API_KEY") or env.get("OPENAI_API_KEY")
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_API_KEY")
    return None


# Stage 1, download.
def stage_download(url: str, max_seconds: int = 30) -> tuple[bool, str, dict[str, Any]]:
    """Download a YouTube video, trim to first max_seconds, return local path."""
    if not url or not url.strip():
        return False, "no URL provided", {}
    url = url.strip()
    start_at = _youtube_start_seconds(url)
    slug = _slug(url)
    work = CACHE_DIR / slug
    work.mkdir(parents=True, exist_ok=True)
    trimmed = work / "clip.mp4"
    if trimmed.exists() and trimmed.stat().st_size > 1024:
        start_msg = f", start {start_at:.0f}s" if start_at else ""
        return True, f"cached at {trimmed}{start_msg}", {
            "video": str(trimmed), "slug": slug, "start_at": start_at}

    try:
        import yt_dlp  # noqa
    except Exception as e:
        return False, f"yt_dlp not installed ({e}). Run: pip install yt-dlp", {}

    raw = work / "raw.%(ext)s"
    # Detect browsers for cookie fallback.
    home = Path.home()
    browser_choices: list[tuple[str, ...]] = []
    if (home / "Library/Application Support/BraveSoftware/Brave-Browser").exists():
        browser_choices.append(("brave",))
    if (home / "Library/Application Support/Google/Chrome").exists():
        browser_choices.append(("chrome",))
    if (home / "Library/Application Support/Firefox/Profiles").exists():
        browser_choices.append(("firefox",))

    base_opts: dict[str, Any] = {
        "format": "mp4[height<=480]/best[height<=480]/best",
        "outtmpl": str(raw),
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
        "retries": 2,
        "fragment_retries": 2,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    # Try several player clients first, then fall back to browser cookies.
    attempts: list[dict[str, Any]] = [
        {**base_opts, "extractor_args": {
            "youtube": {"player_client": ["tv_embedded", "ios", "mweb"]}}},
        {**base_opts, "extractor_args": {
            "youtube": {"player_client": ["android", "web_embedded"]}}},
    ]
    for bc in browser_choices:
        attempts.append({**base_opts, "cookiesfrombrowser": bc,
                         "extractor_args": {
                             "youtube": {"player_client": ["web", "ios"]}}})

    last_err = "no attempt run"
    info = None
    for opt in attempts:
        # Clear partial downloads from prior attempts so we do not pick stale.
        for stale in work.glob("raw.*"):
            try: stale.unlink()
            except Exception: pass
        try:
            with yt_dlp.YoutubeDL(opt) as ydl:
                info = ydl.extract_info(url, download=True)
            break
        except Exception as e:
            last_err = str(e).splitlines()[-1][:160]
            continue
    if info is None:
        return False, f"yt_dlp tried {len(attempts)} client combos: {last_err}", {}

    title = info.get("title", "untitled")
    duration = info.get("duration", 0)
    candidates = list(work.glob("raw.*"))
    if not candidates:
        return False, "download produced no file", {}
    src = candidates[0]

    # Trim with ffmpeg
    if not shutil.which("ffmpeg"):
        # Fallback: just use the original if ffmpeg missing
        shutil.copy(src, trimmed)
        return True, f"got '{title}' (no trim, ffmpeg missing)", {
            "video": str(trimmed), "slug": slug, "title": title,
            "duration": duration, "trimmed_to": None}

    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", f"{start_at:.3f}",
            "-i", str(src),
            "-t", str(max_seconds),
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac",
            "-loglevel", "error",
            str(trimmed),
        ], check=True, timeout=120)
    except Exception as e:
        # Fall back to copy
        shutil.copy(src, trimmed)
        return True, f"got '{title}' (trim failed, using full)", {
            "video": str(trimmed), "slug": slug, "title": title,
            "duration": duration, "trimmed_to": None}
    start_msg = f" from {start_at:.0f}s" if start_at else ""
    return True, f"got '{title}', trimmed to {max_seconds}s{start_msg}", {
        "video": str(trimmed), "slug": slug, "title": title,
        "duration": duration, "trimmed_to": max_seconds,
        "start_at": start_at}


# Stage 2, frame extraction.
def stage_frames(video_path: str, slug: str, n: int = 8) -> tuple[bool, str, dict[str, Any]]:
    if not video_path or not Path(video_path).exists():
        return False, "no video to read", {}
    out_dir = CACHE_DIR / slug / "frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    cached = sorted(out_dir.glob("frame_*.jpg"))
    if len(cached) >= n:
        return True, f"using cached frames", {"frames": [str(p) for p in cached[:n]]}

    try:
        import cv2
    except Exception as e:
        return False, f"cv2 missing: {e}", {}

    try:
        cap = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        idxs = [int(round(i * (total - 1) / max(n - 1, 1))) for i in range(n)]
        paths: list[str] = []
        for i, fi in enumerate(idxs):
            cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
            ok, frame = cap.read()
            if not ok:
                continue
            p = out_dir / f"frame_{i:02d}.jpg"
            cv2.imwrite(str(p), frame)
            paths.append(str(p))
        cap.release()
    except Exception as e:
        return False, f"frame extraction failed: {e}", {}
    if not paths:
        return False, "no frames extracted", {}
    return True, f"extracted {len(paths)} frames", {"frames": paths}


# Stage 3, generate a candidate AD with an LLM (optional).
_AD_SYSTEM = (
    "You write audio descriptions for blind and low vision viewers. "
    "Describe only what is visually present in the frames. Be concrete, "
    "concise, and avoid speculation. Output one paragraph, 35 to 60 words."
)


def stage_generate_ad(frames: list[str]) -> tuple[bool, str, dict[str, Any]]:
    if not frames:
        return False, "no frames to describe", {}
    key = get_api_key("openai")
    if key:
        return _generate_ad_openai(frames, key)
    key = get_api_key("anthropic")
    if key:
        return _generate_ad_anthropic(frames, key)
    return False, "no OPENAI_API_KEY or ANTHROPIC_API_KEY available", {}


def _b64_image(path: str) -> str | None:
    try:
        import base64
        return base64.b64encode(Path(path).read_bytes()).decode()
    except Exception:
        return None


def _generate_ad_openai(frames: list[str], key: str) -> tuple[bool, str, dict[str, Any]]:
    try:
        from openai import OpenAI
    except Exception as e:
        return False, f"openai sdk missing: {e}", {}
    client = OpenAI(api_key=key)
    content: list[dict[str, Any]] = [
        {"type": "text", "text": "Write the audio description for this clip."}
    ]
    for fp in frames[:6]:
        b64 = _b64_image(fp)
        if not b64:
            continue
        content.append({"type": "image_url", "image_url": {
            "url": f"data:image/jpeg;base64,{b64}"}})
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _AD_SYSTEM},
                {"role": "user", "content": content},
            ],
            max_tokens=200,
            temperature=0.4,
        )
        text = resp.choices[0].message.content.strip()
    except Exception as e:
        return False, f"openai call failed: {e}", {}
    return True, "generated via gpt-4o-mini", {"ad": text}


def _generate_ad_anthropic(frames: list[str], key: str) -> tuple[bool, str, dict[str, Any]]:
    try:
        import anthropic
    except Exception as e:
        return False, f"anthropic sdk missing: {e}", {}
    client = anthropic.Anthropic(api_key=key)
    content: list[dict[str, Any]] = []
    for fp in frames[:6]:
        b64 = _b64_image(fp)
        if not b64:
            continue
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg", "data": b64}})
    content.append({"type": "text",
                    "text": "Write the audio description for this clip."})
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=_AD_SYSTEM,
            messages=[{"role": "user", "content": content}],
        )
        text = "".join(b.text for b in resp.content if hasattr(b, "text")).strip()
    except Exception as e:
        return False, f"anthropic call failed: {e}", {}
    return True, "generated via claude-haiku-4-5", {"ad": text}


# Stage 4, CLIP visual grounding.
_CLIP_MODEL: Any = None
_CLIP_PREPROCESS: Any = None
_CLIP_TOKENIZER: Any = None


def _load_clip() -> tuple[bool, str]:
    global _CLIP_MODEL, _CLIP_PREPROCESS, _CLIP_TOKENIZER
    if _CLIP_MODEL is not None:
        return True, "cached"
    try:
        import open_clip
        import torch
    except Exception as e:
        return False, f"open_clip / torch missing: {e}"
    try:
        device = "cuda" if __import__("torch").cuda.is_available() else (
            "mps" if getattr(__import__("torch").backends, "mps", None)
            and __import__("torch").backends.mps.is_available() else "cpu")
        model, _, preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="laion2b_s34b_b79k"
        )
        model.to(device).eval()
        _CLIP_MODEL = (model, device)
        _CLIP_PREPROCESS = preprocess
        _CLIP_TOKENIZER = open_clip.get_tokenizer("ViT-B-32")
    except Exception as e:
        return False, f"CLIP load failed: {e}"
    return True, "loaded"


def stage_clip_grounding(frames: list[str], ad: str) -> tuple[bool, str, dict[str, Any]]:
    if not frames or not ad:
        return False, "need frames and AD", {}
    ok, msg = _load_clip()
    if not ok:
        return False, msg, {}
    try:
        from PIL import Image
        import torch
        model, device = _CLIP_MODEL
        imgs = []
        for fp in frames:
            try:
                img = Image.open(fp).convert("RGB")
                imgs.append(_CLIP_PREPROCESS(img))
            except Exception:
                continue
        if not imgs:
            return False, "no frames decoded", {}
        batch = torch.stack(imgs).to(device)
        tokens = _CLIP_TOKENIZER([ad]).to(device)
        with torch.no_grad():
            img_feat = model.encode_image(batch)
            txt_feat = model.encode_text(tokens)
            img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
            txt_feat = txt_feat / txt_feat.norm(dim=-1, keepdim=True)
            sims = (img_feat @ txt_feat.T).squeeze(-1).cpu().numpy()
    except Exception as e:
        return False, f"CLIP scoring failed: {e}", {}
    per_frame = [float(s) for s in sims]
    return True, "scored", {
        "per_frame": per_frame,
        "mean": float(np.mean(per_frame)),
        "top3": float(np.mean(sorted(per_frame, reverse=True)[:3])),
    }


# Stage 5, ADQA question generation + grading.
_ADQA_Q_SYS = (
    "You are designing reading comprehension questions for blind viewers "
    "evaluating audio descriptions. Look at the frames and write exactly 3 "
    "short yes/no questions that probe whether the description captures "
    "visually salient content. For each question, list the specific visual "
    "evidence a correct AD would need to mention. Return JSON: "
    '{"questions": [{"q": "...", "evidence": "..."}, ...]}'
)
_ADQA_G_SYS = (
    "You are grading audio descriptions for blind viewers. Given the frames, "
    "the AD text, and a question with the required visual evidence, decide "
    "if the AD adequately covers it. Return JSON: "
    '{"score": 0 or 1, "rationale": "...", "evidence_quote": "..."}'
)


def stage_adqa(frames: list[str], ad: str) -> tuple[bool, str, dict[str, Any]]:
    """Cross model ADQA. Prefers Claude for grading (independent from the
    OpenAI based AD generator). Falls back to OpenAI if no Anthropic key."""
    if not frames or not ad:
        return False, "need frames and AD", {}
    a_key = get_api_key("anthropic")
    if a_key:
        return _adqa_anthropic(frames, ad, a_key)
    o_key = get_api_key("openai")
    if o_key:
        return _adqa_openai(frames, ad, o_key)
    return False, "no ANTHROPIC_API_KEY or OPENAI_API_KEY", {}


def _parse_json_loose(text: str) -> dict | None:
    """Pull JSON out of a potentially fenced or noisy response."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


def _adqa_anthropic(frames: list[str], ad: str, key: str
                    ) -> tuple[bool, str, dict[str, Any]]:
    try:
        import anthropic
    except Exception as e:
        return False, f"anthropic sdk missing: {e}", {}
    client = anthropic.Anthropic(api_key=key)
    img_content: list[dict[str, Any]] = []
    for fp in frames[:6]:
        b64 = _b64_image(fp)
        if not b64:
            continue
        img_content.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg", "data": b64}})
    if not img_content:
        return False, "no frames to send", {}

    model_id = "claude-haiku-4-5-20251001"
    try:
        q_resp = client.messages.create(
            model=model_id,
            max_tokens=600,
            system=_ADQA_Q_SYS + ' Respond with ONLY the JSON object.',
            messages=[{"role": "user",
                       "content": img_content + [{"type": "text",
                       "text": "Write the 3 questions now. JSON only."}]}],
        )
        q_text = "".join(b.text for b in q_resp.content if hasattr(b, "text"))
        q_json = _parse_json_loose(q_text) or {}
        questions = q_json.get("questions", [])[:3]
        if not questions:
            return False, "Claude returned no questions", {}
    except Exception as e:
        return False, f"Claude question gen failed: {e}", {}

    graded: list[dict[str, Any]] = []
    try:
        for q in questions:
            qtext = q.get("q", "") or q.get("question", "")
            ev = q.get("evidence", "") or q.get("required_evidence", "")
            g_resp = client.messages.create(
                model=model_id,
                max_tokens=400,
                system=_ADQA_G_SYS + ' Respond with ONLY the JSON object.',
                messages=[{"role": "user", "content": img_content + [{
                    "type": "text",
                    "text": (f"AD: {ad}\n\nQuestion: {qtext}\n"
                             f"Required evidence: {ev}\n\nGrade now. JSON only.")
                }]}],
            )
            g_text = "".join(b.text for b in g_resp.content
                             if hasattr(b, "text"))
            gj = _parse_json_loose(g_text) or {}
            graded.append({
                "question": qtext,
                "evidence": ev,
                "score": int(gj.get("score", 0)),
                "rationale": gj.get("rationale", ""),
                "evidence_quote": gj.get("evidence_quote", ""),
            })
    except Exception as e:
        return False, f"Claude grading failed mid-way: {e}", {"graded": graded}

    yes = sum(g["score"] for g in graded)
    return True, f"{yes} of {len(graded)} yes (Claude grader)", {
        "graded": graded,
        "score": yes / max(len(graded), 1),
    }


def _adqa_openai(frames: list[str], ad: str, key: str
                 ) -> tuple[bool, str, dict[str, Any]]:
    try:
        from openai import OpenAI
    except Exception as e:
        return False, f"openai sdk missing: {e}", {}
    client = OpenAI(api_key=key)
    img_content = []
    for fp in frames[:6]:
        b64 = _b64_image(fp)
        if not b64:
            continue
        img_content.append({"type": "image_url", "image_url": {
            "url": f"data:image/jpeg;base64,{b64}"}})
    if not img_content:
        return False, "no frames to send", {}
    try:
        q_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _ADQA_Q_SYS},
                {"role": "user", "content": img_content + [
                    {"type": "text", "text": "Write the 3 questions now."}]},
            ],
            max_tokens=500, temperature=0.2,
        )
        q_json = json.loads(q_resp.choices[0].message.content)
        questions = q_json.get("questions", [])[:3]
        if not questions:
            return False, "model returned no questions", {}
    except Exception as e:
        return False, f"question gen failed: {e}", {}
    graded: list[dict[str, Any]] = []
    try:
        for q in questions:
            qtext = q.get("q", "")
            ev = q.get("evidence", "")
            g_resp = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": _ADQA_G_SYS},
                    {"role": "user", "content": img_content + [{
                        "type": "text",
                        "text": (f"AD: {ad}\n\nQuestion: {qtext}\n"
                                 f"Required evidence: {ev}\n\nGrade now.")
                    }]},
                ],
                max_tokens=300, temperature=0.0,
            )
            gj = json.loads(g_resp.choices[0].message.content)
            graded.append({
                "question": qtext,
                "evidence": ev,
                "score": int(gj.get("score", 0)),
                "rationale": gj.get("rationale", ""),
                "evidence_quote": gj.get("evidence_quote", ""),
            })
    except Exception as e:
        return False, f"grading failed mid-way: {e}", {"graded": graded}
    yes = sum(g["score"] for g in graded)
    return True, f"{yes} of {len(graded)} yes (GPT-4o grader, same model risk)", {
        "graded": graded,
        "score": yes / max(len(graded), 1),
    }


# Stage 6, TRIBE encoder self-consistency proxy.
_TRIBE_MODEL: Any = None


def _load_tribe() -> tuple[bool, str]:
    global _TRIBE_MODEL
    if _TRIBE_MODEL is not None:
        return True, "cached"
    if not TRIBE_PKG.exists():
        return False, f"tribev2 package not found at {TRIBE_PKG}"
    import sys
    if str(TRIBE_PKG) not in sys.path:
        sys.path.insert(0, str(TRIBE_PKG))
    try:
        from tribev2 import TribeModel
    except Exception as e:
        return False, f"tribev2 import failed: {e}"
    try:
        _TRIBE_MODEL = TribeModel.from_pretrained(
            "facebook/tribev2",
            config_update={
                "data.text_feature.device": "cpu",
                "data.audio_feature.device": "cpu",
                "data.video_feature.image.device": "cpu",
            },
        )
    except Exception as e:
        return False, f"TRIBE load failed: {e}"
    return True, "loaded"


def _tribe_predict_events(model: Any, events: pd.DataFrame) -> np.ndarray | None:
    try:
        preds, _ = model.predict(events)
        return np.asarray(preds)
    except Exception:
        return None


def _tribe_from_path(model: Any, *, video_path: str | None = None, audio_path: str | None = None, text_path: str | None = None) -> np.ndarray | None:
    try:
        events = model.get_events_dataframe(
            video_path=video_path,
            audio_path=audio_path,
            text_path=text_path,
        )
        return _tribe_predict_events(model, events)
    except Exception:
        return None


def _extract_audio_for_tribe(video_path: str) -> str | None:
    """Extract mono audio track for TRIBE audio-only counterfactual."""
    slug = _slug(video_path)
    out = CACHE_DIR / f"{slug}_tribe_audio.wav"
    if out.exists() and out.stat().st_size > 0:
        return str(out)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000", str(out)],
            check=True,
            capture_output=True,
            timeout=120,
        )
        return str(out) if out.exists() else None
    except Exception:
        return None


def _tribe_cos(a: np.ndarray, b: np.ndarray) -> float:
    a = a.mean(axis=0).flatten().astype(float)
    b = b.mean(axis=0).flatten().astype(float)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def stage_tribe_proxy(video_path: str, ad: str) -> tuple[bool, str, dict[str, Any]]:
    """TRIBE counterfactual proxy (paper-aligned).

    P_AV  = full video
    P_A   = audio-only (extracted wav)
    P_AD  = AD text-only (.txt → TTS pipeline inside TRIBE)

    Reports accessibility_gap = 1 - cos(P_AV, P_A) and
    description_gain = cos(P_AV, P_AD) - cos(P_AV, P_A).
    """
    if not video_path or not Path(video_path).exists():
        return False, "no video for TRIBE", {}
    ok, msg = _load_tribe()
    if not ok:
        return False, msg, {}
    model = _TRIBE_MODEL

    p_av = _tribe_from_path(model, video_path=video_path)
    if p_av is None:
        return False, "P_AV prediction failed", {}

    audio_path = _extract_audio_for_tribe(video_path)
    p_a = _tribe_from_path(model, audio_path=audio_path) if audio_path else None
    audio_only_ok = p_a is not None
    if p_a is None:
        p_a = p_av

    accessibility_gap = 1.0 - _tribe_cos(p_av, p_a)

    description_gain = 0.0
    align_va = 0.0
    p_av_ad = None
    ad_txt: Path | None = None
    if ad.strip():
        ad_txt = CACHE_DIR / f"{_slug(video_path)}_ad.txt"
        ad_txt.write_text(ad.strip(), encoding="utf-8")
        p_ad = _tribe_from_path(model, text_path=str(ad_txt))
        if p_ad is not None:
            description_gain = _tribe_cos(p_av, p_ad) - _tribe_cos(p_av, p_a)
        # Legacy: video + AD text overlay (approximate integrated narration)
        try:
            events = model.get_events_dataframe(video_path=video_path)
            if "text" in events.columns:
                events = events.copy()
                events["text"] = ad.strip()
                p_av_ad = _tribe_predict_events(model, events)
                if p_av_ad is not None:
                    align_va = _tribe_cos(p_av, p_av_ad)
        except Exception:
            pass

    # Optional tensor-save side effect. Set TRIBE_TENSOR_DIR=/path/to/dir
    # in the environment to dump P_AV, P_A, P_AD, P_AV_AD as .npz per clip.
    # Off by default so the Gradio demo / API don't bloat memory or disk.
    tensor_dir = os.environ.get("TRIBE_TENSOR_DIR")
    if tensor_dir:
        try:
            td = Path(tensor_dir)
            td.mkdir(parents=True, exist_ok=True)
            npz_path = td / f"{_slug(video_path)}.npz"
            if not npz_path.exists():
                np.savez_compressed(
                    npz_path,
                    P_AV=p_av.astype(np.float32),
                    P_A=p_a.astype(np.float32),
                    P_AD=(p_ad if 'p_ad' in dir() and p_ad is not None else np.zeros_like(p_av)).astype(np.float32),
                    P_AV_AD=(p_av_ad if p_av_ad is not None else np.zeros_like(p_av)).astype(np.float32),
                )
        except Exception:
            pass

    av_mean = p_av.mean(axis=0)
    va_mean = p_av_ad.mean(axis=0) if p_av_ad is not None else av_mean
    parts = [f"gap {accessibility_gap:.3f}", f"DG {description_gain:.3f}"]
    if not audio_only_ok:
        parts.append("audio-only fallback")
    return True, ", ".join(parts), {
        "alignment_cosine": align_va,
        "accessibility_gap": accessibility_gap,
        "description_gain": description_gain,
        "audio_only_ok": audio_only_ok,
        "video_mean_lh": float(av_mean[:10242].mean()),
        "video_mean_rh": float(av_mean[10242:].mean()),
        "video_ad_mean_lh": float(va_mean[:10242].mean()),
        "video_ad_mean_rh": float(va_mean[10242:].mean()),
    }
