"""Run text-only paper baselines on the 60-clip external set.

Replicates the 18-clip leaderboard for external generalization. Each metric
takes (per clip, per tier) AD text -> score. Outputs:
- per-(clip,tier) scores in cursor/research/output/external_paper_baselines.csv
- in-benchmark vs external rho leaderboard in
  cursor/research/output/external_paper_baselines_leaderboard.csv
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "cursor" / "data" / "external_clips" / "registry.jsonl"
OUT_DIR  = ROOT / "cursor" / "research" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)
EXTERNAL_BASELINES_CSV = OUT_DIR / "external_paper_baselines.csv"
LEADERBOARD_CSV        = OUT_DIR / "external_paper_baselines_leaderboard.csv"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {t: i for i, t in enumerate(TIERS)}


# ---------- text utilities ----------

def sentences(text: str) -> list[str]:
    return [s.strip().lower() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 8]


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z]{3,}", str(text).lower())


# ---------- baseline 1: LLM-AD-Eval (sentence embedding similarity to tier3) ----------

def llm_ad_eval_proxy(rows: list[dict]) -> None:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    for r in rows:
        ref = r["tier3_va11y_text"]
        for t in TIERS:
            hyp = r[f"{t}_text"]
            ea = model.encode([hyp], normalize_embeddings=True)
            eb = model.encode([ref], normalize_embeddings=True)
            sim = float((ea @ eb.T)[0, 0])
            score = 1 + 4 * max(0.0, min(1.0, (sim + 1) / 2))
            r[f"llm_ad_eval__{t}"] = score


# ---------- baseline 2: CRITIC entity proxy ----------

ENTITY_ROLE_RE = re.compile(
    r"\b(man|woman|boy|girl|person|chef|player|child|dog|cat|deer|baby|kid|"
    r"horse|teacher|student|driver|cook|musician|athlete|coach)\b"
)
PROPER_RE = re.compile(r"\b[A-Z][a-z]{2,}\b")


def entity_tokens(text: str) -> set[str]:
    caps = set(PROPER_RE.findall(text))
    roles = set(ENTITY_ROLE_RE.findall(text.lower()))
    return caps | roles


def critic_score(ad: str, reference_entities: set[str]) -> float:
    ad_ent = entity_tokens(ad)
    if not reference_entities:
        return 0.5
    hit = len(ad_ent & reference_entities) / max(1, len(reference_entities))
    has_entity = 1.0 if ad_ent else 0.0
    return 0.7 * hit + 0.3 * has_entity


def critic_entity(rows: list[dict]) -> None:
    for r in rows:
        ref = entity_tokens(r["tier3_va11y_text"]) | entity_tokens(r["tier2_vatex_long_text"])
        for t in TIERS:
            r[f"critic_entity__{t}"] = critic_score(r[f"{t}_text"], ref)


# ---------- baseline 3: CoAD repetition (lower is better for AD quality) ----------

def repetition_score(text: str) -> float:
    """Return 1 - repetition_rate so 'higher = better' for rho comparison."""
    sents = sentences(text)
    if len(sents) < 2:
        return 1.0
    bigrams = []
    for s in sents:
        words = re.findall(r"[a-z]+", s)
        bigrams.extend(zip(words, words[1:]))
    if not bigrams:
        return 1.0
    c = Counter(bigrams)
    rep = sum(v - 1 for v in c.values() if v > 1) / len(bigrams)
    sims = []
    for i in range(len(sents)):
        wi = set(re.findall(r"[a-z]{4,}", sents[i]))
        for j in range(i + 1, len(sents)):
            wj = set(re.findall(r"[a-z]{4,}", sents[j]))
            if wi and wj:
                sims.append(len(wi & wj) / len(wi | wj))
    self_sim = sum(sims) / len(sims) if sims else 0.0
    penalty = 0.6 * rep + 0.4 * self_sim
    return 1.0 - penalty


def coad_repetition(rows: list[dict]) -> None:
    for r in rows:
        for t in TIERS:
            r[f"coad_repetition_inv__{t}"] = repetition_score(r[f"{t}_text"])


# ---------- baseline 4: Multi-ref R@3/N (token recall vs all-tier reference union) ----------

def multi_ref_recall(ad: str, refs: list[str]) -> float:
    """R@3/N: fraction of reference content-tokens recovered by the AD."""
    ad_tok = set(tokens(ad))
    ref_tok = set()
    for r in refs:
        ref_tok |= set(tokens(r))
    if not ref_tok:
        return 0.0
    return len(ad_tok & ref_tok) / len(ref_tok)


def multi_ref_r_at_k(rows: list[dict]) -> None:
    for r in rows:
        # references = all tiers except tier3 (so tier3 is being ranked vs the others)
        # Following the 18-clip recipe: tier3 = reference; lower tiers ranked against it
        refs = [r["tier3_va11y_text"], r["tier2_vatex_long_text"], r["tier1_vatex_short_text"]]
        for t in TIERS:
            r[f"multi_ref_r3__{t}"] = multi_ref_recall(r[f"{t}_text"], refs)


# ---------- baseline 5: simple lexical-overlap (sanity baseline) ----------

def token_overlap(rows: list[dict]) -> None:
    for r in rows:
        ref = set(tokens(r["tier3_va11y_text"]))
        for t in TIERS:
            hyp = set(tokens(r[f"{t}_text"]))
            r[f"token_overlap__{t}"] = (len(ref & hyp) / max(1, len(ref))) if ref else 0.0


# ---------- baseline 6: word-count proxy (control: does length predict tier?) ----------

def word_count_baseline(rows: list[dict]) -> None:
    for r in rows:
        for t in TIERS:
            r[f"word_count__{t}"] = len(tokens(r[f"{t}_text"]))


# ---------- runner ----------

def load_60_clip_rows() -> list[dict]:
    out = []
    with REGISTRY.open() as f:
        for line in f:
            d = json.loads(line)
            if not d.get("download_ok"):
                continue
            out.append({
                "video_id":               d["video_id"],
                "category":               d["category"],
                "tier3_va11y_text":       d["tier3_va11y"],
                "tier2_vatex_long_text":  d["tier2_vatex_long"],
                "tier1_vatex_short_text": d["tier1_vatex_short"],
                "tier0_cross_text":       d["tier0_cross"],
            })
    return out


def main() -> None:
    rows = load_60_clip_rows()
    print(f"Loaded {len(rows)} external clips from registry")

    print("Computing LLM-AD-Eval (sentence-transformers)...")
    llm_ad_eval_proxy(rows)
    print("Computing CRITIC entity proxy...")
    critic_entity(rows)
    print("Computing CoAD repetition...")
    coad_repetition(rows)
    print("Computing multi-ref R@3/N...")
    multi_ref_r_at_k(rows)
    print("Computing token overlap baseline...")
    token_overlap(rows)
    print("Computing word-count baseline...")
    word_count_baseline(rows)

    # Pivot to long format
    long_rows = []
    for r in rows:
        for t in TIERS:
            long_rows.append({
                "video_id": r["video_id"],
                "category": r["category"],
                "tier":     t,
                "gt":       TIER_GT[t],
                "llm_ad_eval":         r[f"llm_ad_eval__{t}"],
                "critic_entity":       r[f"critic_entity__{t}"],
                "coad_repetition_inv": r[f"coad_repetition_inv__{t}"],
                "multi_ref_r3":        r[f"multi_ref_r3__{t}"],
                "token_overlap":       r[f"token_overlap__{t}"],
                "word_count":          r[f"word_count__{t}"],
            })
    df = pd.DataFrame(long_rows)
    df.to_csv(EXTERNAL_BASELINES_CSV, index=False)
    print(f"\nPer-(clip,tier) scores -> {EXTERNAL_BASELINES_CSV}")

    # Compute rho per metric, plus full ordering count
    metrics = ["llm_ad_eval", "critic_entity", "coad_repetition_inv", "multi_ref_r3",
               "token_overlap", "word_count"]
    results = []
    for m in metrics:
        rho, p = spearmanr(df[m], df["gt"])
        ordered = 0
        for vid, grp in df.groupby("video_id"):
            sub = grp.sort_values("gt")[m].values
            if len(sub) == 4 and all(sub[i] < sub[i + 1] for i in range(3)):
                ordered += 1
        # T3 pairwise wins (T3 score > each lower tier score, per clip)
        t3_wins = 0
        t3_total = 0
        for vid, grp in df.groupby("video_id"):
            t3 = grp[grp["tier"] == "tier3_va11y"][m].values
            if not len(t3):
                continue
            t3 = t3[0]
            for t in ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]:
                sub = grp[grp["tier"] == t][m].values
                if not len(sub):
                    continue
                t3_total += 1
                if t3 > sub[0]:
                    t3_wins += 1
        results.append({
            "metric": m,
            "external_rho": rho,
            "external_p": p,
            "external_t3_wins": f"{t3_wins}/{t3_total}",
            "external_fully_ordered": f"{ordered}/{df['video_id'].nunique()}",
            "n_obs": len(df),
        })

    leaderboard = pd.DataFrame(results).sort_values("external_rho", ascending=False)
    leaderboard.to_csv(LEADERBOARD_CSV, index=False)
    print(f"\nLeaderboard -> {LEADERBOARD_CSV}\n")
    print(leaderboard.to_string(index=False))

    # In-benchmark reference numbers (for the markdown summary)
    in_bench = {
        "llm_ad_eval":         0.899,
        "critic_entity":       0.638,
        "coad_repetition_inv": -0.064,
        "multi_ref_r3":        0.532,
    }
    print("\n=== Generalization gap (in-benchmark 18-clip vs external 60-clip) ===")
    for _, row in leaderboard.iterrows():
        m = row["metric"]
        if m in in_bench:
            delta = row["external_rho"] - in_bench[m]
            print(f"  {m:25s}  in-bench={in_bench[m]:+.3f}  external={row['external_rho']:+.3f}  delta={delta:+.3f}")


if __name__ == "__main__":
    main()
