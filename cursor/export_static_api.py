#!/usr/bin/env python3
"""Export SceneTwin cached API payloads for the static web frontend.

This script is deliberately local-only. It reads cached CSV/image metadata through
``api.server`` endpoint functions and writes JSON snapshots under ``cursor/data``.
It never calls the live YouTube audit, external LLM APIs, TRIBE inference, or any
network service.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "cursor" / "data"


def _install_lightweight_csv_shims() -> None:
    """Let cached exports run in tiny Python envs without numpy/pandas.

    The real demo should use ``requirements.txt``. This shim exists only so the
    static exporter can read CSV-backed endpoint payloads on a bare interpreter.
    It implements the tiny subset used by ``api.server``: ``read_csv``,
    ``DataFrame.replace`` and ``DataFrame.to_dict(orient='records')``.
    """
    need_numpy = importlib.util.find_spec("numpy") is None
    need_pandas = importlib.util.find_spec("pandas") is None

    if need_numpy and "numpy" not in sys.modules:
        np = types.ModuleType("numpy")
        np.nan = float("nan")

        def _mean(values: list[float]) -> float:
            vals = [float(v) for v in values]
            return sum(vals) / len(vals) if vals else float("nan")

        np.mean = _mean  # type: ignore[attr-defined]
        sys.modules["numpy"] = np

    if need_pandas and "pandas" not in sys.modules:
        import csv

        class _MiniFrame:
            def __init__(self, rows: list[dict[str, Any]]):
                self._rows = rows

            def replace(self, *_args: Any, **_kwargs: Any) -> "_MiniFrame":
                return self

            def to_dict(self, orient: str = "records") -> list[dict[str, Any]]:
                if orient != "records":
                    raise ValueError("mini pandas shim only supports orient='records'")
                return self._rows

        def _read_csv(path: str | Path) -> _MiniFrame:
            with Path(path).open(newline="", encoding="utf-8-sig") as f:
                return _MiniFrame(list(csv.DictReader(f)))

        pd = types.ModuleType("pandas")
        pd.read_csv = _read_csv  # type: ignore[attr-defined]
        pd.DataFrame = _MiniFrame  # type: ignore[attr-defined]
        sys.modules["pandas"] = pd


def _install_api_import_shims() -> None:
    """Let the exporter import ``api.server`` without FastAPI/Pydantic.

    These shims are used only when the real packages are absent. They support the
    decorator/class definitions needed during import; the exporter calls only
    plain cached endpoint functions afterward.
    """
    if importlib.util.find_spec("pydantic") is None and "pydantic" not in sys.modules:
        pydantic = types.ModuleType("pydantic")

        class BaseModel:
            def __init__(self, **kwargs: Any):
                for key, value in kwargs.items():
                    setattr(self, key, value)

        def Field(default: Any = None, **_kwargs: Any) -> Any:
            return default

        pydantic.BaseModel = BaseModel  # type: ignore[attr-defined]
        pydantic.Field = Field  # type: ignore[attr-defined]
        pydantic.HttpUrl = str  # type: ignore[attr-defined]
        sys.modules["pydantic"] = pydantic

    if importlib.util.find_spec("fastapi") is None and "fastapi" not in sys.modules:
        fastapi = types.ModuleType("fastapi")

        class FastAPI:
            def __init__(self, *_args: Any, **_kwargs: Any):
                pass

            def add_middleware(self, *_args: Any, **_kwargs: Any) -> None:
                return None

            def mount(self, *_args: Any, **_kwargs: Any) -> None:
                return None

            def get(self, *_args: Any, **_kwargs: Any):
                return lambda fn: fn

            def post(self, *_args: Any, **_kwargs: Any):
                return lambda fn: fn

        fastapi.FastAPI = FastAPI  # type: ignore[attr-defined]
        sys.modules["fastapi"] = fastapi

        middleware = types.ModuleType("fastapi.middleware")
        cors_mod = types.ModuleType("fastapi.middleware.cors")

        class CORSMiddleware:
            pass

        cors_mod.CORSMiddleware = CORSMiddleware  # type: ignore[attr-defined]
        sys.modules["fastapi.middleware"] = middleware
        sys.modules["fastapi.middleware.cors"] = cors_mod

        static_mod = types.ModuleType("fastapi.staticfiles")

        class StaticFiles:
            def __init__(self, *_args: Any, **_kwargs: Any):
                pass

        static_mod.StaticFiles = StaticFiles  # type: ignore[attr-defined]
        sys.modules["fastapi.staticfiles"] = static_mod


def _clean(value: Any) -> Any:
    """Convert endpoint payloads into strict JSON-safe objects."""
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    if isinstance(value, tuple):
        return [_clean(v) for v in value]
    if isinstance(value, float):
        return None if math.isnan(value) or math.isinf(value) else value
    if isinstance(value, Path):
        return str(value)
    return value


def _write_json(name: str, payload: Any) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    path.write_text(
        json.dumps(_clean(payload), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    _install_lightweight_csv_shims()
    _install_api_import_shims()
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    # Import only cached endpoint functions. Do not call audit().
    from api.server import cached_clips, qc_gate_benchmark, review_priority, tribe_risk

    exports = {
        "cached-clips.json": cached_clips(),
        "tribe-risk.json": tribe_risk(),
        "review-priority.json": review_priority(),
        "qc-gate.json": qc_gate_benchmark(),
    }

    for name, payload in exports.items():
        path = _write_json(name, payload)
        n = payload.get("n") if isinstance(payload, dict) else "?"
        print(f"wrote {path.relative_to(ROOT)} ({n} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
