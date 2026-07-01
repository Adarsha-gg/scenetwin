"""VLM-as-judge cross-provider analyzer.

Reads all available `vlm_as_judge_<provider>_<model>_combined.csv` files,
computes per-provider/per-corpus metrics, and writes:

- cursor/research/output/vlm_as_judge_leaderboard.csv
- cursor/research/output/vlm_as_judge_agreement.csv  (inter-provider rho)
- cursor/research/output/vlm_as_judge_summary.md
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "cursor" / "research" / "output"

# Our ensemble baseline numbers for the comparison row
ENSEMBLE = {
    "inbench":  {"rho": 0.929, "t3_wins": "54/54",   "n": 72},
    "external": {"rho": 0.873, "t3_wins": "173/180", "n": 240},
    "combined": {"rho": 0.886, "t3_wins": "227/234", "n": 312},
}


def per_corpus_stats(df: pd.DataFrame) -> dict:
    out = {}
    for corpus_name in ("inbench", "external", "combined"):
        sub = df if corpus_name == "combined" else df[df["corpus"] == corpus_name]
        ok = sub["overall"].notna()
        if ok.sum() < 4:
            out[corpus_name] = None
            continue
        rho, p = spearmanr(sub.loc[ok, "overall"], sub.loc[ok, "gt"])
        # T3 pairwise wins
        wins, total = 0, 0
        for _, grp in sub.groupby("video_id"):
            t3 = grp[grp["tier"] == "tier3_va11y"]["overall"]
            if len(t3) == 0 or pd.isna(t3.iloc[0]):
                continue
            t3v = float(t3.iloc[0])
            for t in ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]:
                s = grp[grp["tier"] == t]["overall"]
                if len(s) == 0 or pd.isna(s.iloc[0]):
                    continue
                total += 1
                if t3v > float(s.iloc[0]):
                    wins += 1
        # Fully ordered
        ordered = 0
        clip_n = 0
        for _, grp in sub.groupby("video_id"):
            ranked = grp.sort_values("gt")["overall"].values
            if len(ranked) != 4 or any(pd.isna(ranked)):
                continue
            clip_n += 1
            if all(ranked[i] < ranked[i + 1] for i in range(3)):
                ordered += 1
        out[corpus_name] = {
            "rho": float(rho), "p": float(p), "n_obs": int(ok.sum()),
            "t3_wins": f"{wins}/{total}", "fully_ordered": f"{ordered}/{clip_n}",
            "n_valid_clips": clip_n,
        }
    return out


def load_results() -> dict[str, pd.DataFrame]:
    results = {}
    for f in sorted(OUT_DIR.glob("vlm_as_judge_*_combined.csv")):
        m = re.match(r"vlm_as_judge_([^_]+)_(.+)_combined\.csv", f.name)
        if not m:
            continue
        provider, model = m.group(1), m.group(2).replace("_", "-")
        df = pd.read_csv(f)
        # Require at least one full clip
        if df["overall"].notna().sum() < 4:
            continue
        results[f"{provider}/{model}"] = df
    return results


def main():
    results = load_results()
    print(f"Found {len(results)} VLM result CSVs: {list(results.keys())}")

    leaderboard_rows = []
    leaderboard_rows.append({
        "model": "SceneTwin ensemble (CLIP+ADQA)",
        "inbench_rho": ENSEMBLE["inbench"]["rho"],
        "inbench_t3_wins": ENSEMBLE["inbench"]["t3_wins"],
        "external_rho": ENSEMBLE["external"]["rho"],
        "external_t3_wins": ENSEMBLE["external"]["t3_wins"],
        "combined_rho": ENSEMBLE["combined"]["rho"],
        "combined_t3_wins": ENSEMBLE["combined"]["t3_wins"],
    })
    for label, df in results.items():
        stats = per_corpus_stats(df)
        leaderboard_rows.append({
            "model": label,
            "inbench_rho":      stats["inbench"]["rho"]      if stats["inbench"]  else None,
            "inbench_t3_wins":  stats["inbench"]["t3_wins"]  if stats["inbench"]  else None,
            "external_rho":     stats["external"]["rho"]     if stats["external"] else None,
            "external_t3_wins": stats["external"]["t3_wins"] if stats["external"] else None,
            "combined_rho":     stats["combined"]["rho"]     if stats["combined"] else None,
            "combined_t3_wins": stats["combined"]["t3_wins"] if stats["combined"] else None,
        })
    leaderboard = pd.DataFrame(leaderboard_rows)
    leaderboard.to_csv(OUT_DIR / "vlm_as_judge_leaderboard.csv", index=False)
    print(f"\nLeaderboard -> {OUT_DIR/'vlm_as_judge_leaderboard.csv'}\n")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 220)
    print(leaderboard.to_string(index=False))

    # Inter-provider agreement on combined corpus
    if len(results) >= 2:
        print("\nInter-provider agreement (Spearman rho on overall scores per (clip,tier)):")
        merged = None
        for label, df in results.items():
            sub = df[["video_id", "tier", "overall"]].rename(columns={"overall": label})
            if merged is None:
                merged = sub
            else:
                merged = merged.merge(sub, on=["video_id", "tier"], how="outer")
        labels = list(results.keys())
        agree_rows = []
        print(f"\n{'pair':50s}  {'rho':>8s}  {'n_obs':>6s}")
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                a, b = labels[i], labels[j]
                mask = merged[a].notna() & merged[b].notna()
                if mask.sum() < 4:
                    continue
                r, _ = spearmanr(merged.loc[mask, a], merged.loc[mask, b])
                agree_rows.append({"a": a, "b": b, "rho": r, "n_obs": int(mask.sum())})
                print(f"  {a} <-> {b}:  rho = {r:.4f}  n = {mask.sum()}")
        pd.DataFrame(agree_rows).to_csv(OUT_DIR / "vlm_as_judge_agreement.csv", index=False)

    # Markdown summary
    lines = ["# VLM-as-judge cross-provider results", ""]
    lines += ["## Leaderboard vs SceneTwin ensemble", "",
              "| Model | In-bench rho | T3 wins | External rho | T3 wins | Combined rho | T3 wins |",
              "|---|---:|---|---:|---|---:|---|"]
    for _, row in leaderboard.iterrows():
        fmt = lambda v: f"{v:.4f}" if isinstance(v, float) else (str(v) if v is not None else "-")
        lines.append(
            f"| {row['model']} | {fmt(row['inbench_rho'])} | {fmt(row['inbench_t3_wins'])} "
            f"| {fmt(row['external_rho'])} | {fmt(row['external_t3_wins'])} "
            f"| {fmt(row['combined_rho'])} | {fmt(row['combined_t3_wins'])} |"
        )
    lines.append("")
    if leaderboard.shape[0] > 1:
        # Conclusion line
        ens_combined = ENSEMBLE["combined"]["rho"]
        best_vlm = leaderboard.iloc[1:]["combined_rho"].max()
        gap = ens_combined - best_vlm if pd.notna(best_vlm) else None
        if gap is not None:
            lines.append(f"### Headline gap")
            lines.append(f"SceneTwin ensemble beats the best VLM-as-judge by **{gap:+.3f} rho** on the combined corpus (n=312).")
            lines.append("")
    (OUT_DIR / "vlm_as_judge_summary.md").write_text("\n".join(lines))
    print(f"\nSummary -> {OUT_DIR/'vlm_as_judge_summary.md'}")


if __name__ == "__main__":
    main()
