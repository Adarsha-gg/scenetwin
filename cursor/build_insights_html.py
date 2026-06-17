#!/usr/bin/env python3
"""Build cursor/insights.html from experiment CSV outputs."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

CURSOR = Path(__file__).resolve().parent
ROOT = CURSOR.parent


def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(CURSOR / "output" / name)


def main() -> None:
    category = load_csv("category_risk_summary.csv")
    priority = load_csv("combined_review_priority.csv")
    manifest = json.loads((CURSOR / "data" / "manifest.json").read_text())

    top_priority = priority.nsmallest(5, "review_rank")[
        ["clip_idx", "category", "review_rank", "review_priority", "quality_risk"]
    ].to_dict(orient="records")

    cat_rows = category.to_dict(orient="records")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>SceneTwin cursor insights</title>
  <style>
    :root {{ font-family: system-ui, sans-serif; background: #0a0b0d; color: #e8e8ea; }}
    body {{ max-width: 960px; margin: 0 auto; padding: 24px; line-height: 1.5; }}
    h1 {{ font-weight: 500; letter-spacing: -0.02em; }}
    .muted {{ color: #888; font-size: 14px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px; }}
    th, td {{ border: 1px solid #333; padding: 8px 10px; text-align: left; }}
    th {{ background: #14161a; }}
    .card {{ border: 1px solid #333; padding: 16px; margin: 16px 0; background: #111318; }}
    code {{ font-family: ui-monospace, monospace; font-size: 13px; }}
  </style>
</head>
<body>
  <h1>SceneTwin cursor insights</h1>
  <p class="muted">Generated from <code>cursor/output/</code> · headline ρ = {manifest.get('headline_rho')}</p>

  <div class="card">
    <h2>Composite review priority (top 5)</h2>
    <p class="muted">60% TRIBE risk + 40% ADQA judge fragility. Recall@3 catches both known failures.</p>
    <table>
      <tr><th>Clip</th><th>Category</th><th>Rank</th><th>Score</th><th>Risk note</th></tr>
      {"".join(
        f"<tr><td>clip_{int(r['clip_idx']):02d}</td><td>{r['category']}</td>"
        f"<td>{int(r['review_rank'])}</td><td>{r['review_priority']:.3f}</td>"
        f"<td>{r['quality_risk']}</td></tr>"
        for r in top_priority
      )}
    </table>
  </div>

  <div class="card">
    <h2>TRIBE pressure by category</h2>
    <table>
      <tr><th>Category</th><th>Clips</th><th>Mean risk</th><th>Mean pressure</th><th>Extended AD</th></tr>
      {"".join(
        f"<tr><td>{r['category']}</td><td>{int(r['n_clips'])}</td>"
        f"<td>{r['mean_risk_score']:.3f}</td><td>{r['mean_tribe_pressure']:.3f}</td>"
        f"<td>{int(r['extended_ad_count'])}</td></tr>"
        for r in cat_rows
      )}
    </table>
  </div>

  <div class="card">
    <h2>TRIBE story (one line)</h2>
    <p>TRIBE predicts when automatic ADQA will disagree on tier order (ρ ≈ −0.75) from video+audio alone.
    Use it to triage human review before writing or scoring AD text.</p>
  </div>

  <p class="muted">Re-run: <code>python3 cursor/build_insights_html.py</code></p>
</body>
</html>
"""
    out = CURSOR / "insights.html"
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
