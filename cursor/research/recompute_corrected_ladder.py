"""Recompute the SceneTwin corrected three-tier ladder headline numbers from the raw
per-tier score CSVs. Pure stdlib (no numpy/scipy), deterministic (seeded).

The "corrected ladder" drops the invalid T2 ("long VATEX") verbosity rung and ranks
T0 (cross-decoy) < T1 (crowd caption) < T3 (professional AD). The 60-clip set is the
primary evaluation; the 18-clip set is the corroborating pilot. The two sets are
disjoint by construction (the 60-clip set excludes the 18 pilot clips).

Inputs:
  cursor/output/external_ensemble_eval.csv                              (60-clip primary)
  output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv (18-clip pilot)

Validation target (cursor/output/corrected_ladder_robustness.json, w_adqa=0.5, minmax):
  60-clip ensemble rho = 0.9516 ; 18-clip ensemble rho = 0.9570

Run:  python cursor/research/recompute_corrected_ladder.py [--json OUT.json]
"""
import csv, math, random, json, sys, os
from collections import defaultdict

random.seed(7)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DROP = "tier2_vatex_long"                       # the rung removed in the corrected ladder
ORDER = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier3_va11y": 2}
TIERS = list(ORDER)

# ----- rank statistics (stdlib) -----------------------------------------------
def _ranks(xs):
    s = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0] * len(xs); i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[s[j + 1]] == xs[s[i]]:
            j += 1
        for k in range(i, j + 1):
            r[s[k]] = (i + j) / 2.0 + 1
        i = j + 1
    return r

def _pearson(a, b):
    n = len(a); ma = sum(a) / n; mb = sum(b) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = math.sqrt(sum((x - ma) ** 2 for x in a)); db = math.sqrt(sum((x - mb) ** 2 for x in b))
    return num / (da * db) if da and db else 0.0

def spearman(x, y):
    return _pearson(_ranks(x), _ranks(y))

def kendall_tau_b(x, y):
    n = len(x); c = d = tx = ty = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx, dy = x[i] - x[j], y[i] - y[j]
            if dx == 0 and dy == 0: continue
            if dx == 0: tx += 1; continue
            if dy == 0: ty += 1; continue
            c += 1 if (dx > 0) == (dy > 0) else 0
            d += 1 if (dx > 0) != (dy > 0) else 0
    n0, n1 = c + d + tx, c + d + ty
    return (c - d) / math.sqrt(n0 * n1) if n0 and n1 else 0.0

# ----- data loading -----------------------------------------------------------
def _load(path, id_key, adqa_key):
    clips, cat = defaultdict(dict), {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["tier"] == DROP: continue
            vid = row[id_key]
            cat[vid] = row.get("category", "")
            clips[vid][row["tier"]] = {"clip": float(row["clip_top3"]), "adqa": float(row[adqa_key])}
    return clips, cat

def _minmax(clips, key):
    out = {}
    for vid, tiers in clips.items():
        vals = [tiers[t][key] for t in tiers]; lo, hi = min(vals), max(vals)
        out[vid] = {t: (tiers[t][key] - lo) / (hi - lo) if hi > lo else 0.0 for t in tiers}
    return out

# ----- core stats -------------------------------------------------------------
def analyze(clips, cat, label, w_adqa=0.5):
    cn, an = _minmax(clips, "clip"), _minmax(clips, "adqa")
    ens = {v: {t: (1 - w_adqa) * cn[v][t] + w_adqa * an[v][t] for t in clips[v]} for v in clips}
    g  = [ORDER[t] for v in clips for t in TIERS]
    se = [ens[v][t] for v in clips for t in TIERS]
    sa = [an[v][t]  for v in clips for t in TIERS]
    sc = [cn[v][t]  for v in clips for t in TIERS]
    # pooled-raw single signals (matches the manuscript baseline table)
    ra_raw = spearman(g, [clips[v][t]["adqa"] for v in clips for t in TIERS])
    rc_raw = spearman(g, [clips[v][t]["clip"] for v in clips for t in TIERS])
    # ordering / pairwise
    full = t3w = t3t = pw = pwt = hard_w = hard_t = 0
    losses = []
    for v in clips:
        s0, s1, s3 = ens[v]["tier0_cross"], ens[v]["tier1_vatex_short"], ens[v]["tier3_va11y"]
        full += 1 if s0 < s1 < s3 else 0
        for lo in (s0, s1):
            t3t += 1; t3w += 1 if s3 > lo else 0
        for a, b, nm in ((s0, s1, "T0<T1"), (s0, s3, "T0<T3"), (s1, s3, "T1<T3")):
            pwt += 1; ok = b > a; pw += 1 if ok else 0
            if nm == "T1<T3":
                hard_t += 1; hard_w += 1 if ok else 0
            if not ok: losses.append((v, nm, round(a, 3), round(b, 3)))
    # permutation + bootstrap on ensemble
    obs = spearman(g, se); B = 5000; ge = 0
    for _ in range(B):
        pg, ps = [], []
        for v in clips:
            labs = [ORDER[t] for t in TIERS]; random.shuffle(labs)
            for i, t in enumerate(TIERS): pg.append(labs[i]); ps.append(ens[v][t])
        ge += 1 if spearman(pg, ps) >= obs else 0
    perm_p = (ge + 1) / (B + 1)
    vids = list(clips); boots = []
    for _ in range(2000):
        samp = [random.choice(vids) for _ in vids]; bg, bs = [], []
        for v in samp:
            for t in TIERS: bg.append(ORDER[t]); bs.append(ens[v][t])
        boots.append(spearman(bg, bs))
    boots.sort(); ci = [round(boots[int(0.025 * len(boots))], 3), round(boots[int(0.975 * len(boots))], 3)]
    n = len(g); rho_min = math.tanh((1.96 + 0.84) / math.sqrt(n - 3))
    res = {
        "label": label, "n_clips": len(clips), "n_obs": n, "w_adqa": w_adqa,
        "ensemble_rho": round(obs, 4), "adqa_norm_rho": round(spearman(g, sa), 4),
        "clip_norm_rho": round(spearman(g, sc), 4),
        "adqa_pooled_raw_rho": round(ra_raw, 4), "clip_pooled_raw_rho": round(rc_raw, 4),
        "kendall_tau": round(kendall_tau_b(g, se), 4),
        "fully_ordered": f"{full}/{len(clips)}", "t3_vs_lower": f"{t3w}/{t3t}",
        "all_pairwise": f"{pw}/{pwt}", "hard_pair_T1_vs_T3": f"{hard_w}/{hard_t}",
        "perm_p": perm_p, "bootstrap_ci95": ci, "min_detectable_rho": round(rho_min, 3),
        "ensemble_losses": losses,
    }
    if any(cat.values()):
        bycat = defaultdict(list)
        for v in clips: bycat[cat[v]].append(v)
        res["per_category"] = {
            c: {"n": len(vs),
                "ens_rho": round(spearman([ORDER[t] for v in vs for t in TIERS],
                                          [ens[v][t] for v in vs for t in TIERS]), 3)}
            for c, vs in sorted(bycat.items())}
    return res

def main():
    ext, ecat = _load(os.path.join(ROOT, "cursor/output/external_ensemble_eval.csv"),
                      "video_id", "adqa_score")
    inb, _ = _load(os.path.join(ROOT, "output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv"),
                   "clip_idx", "adqa_v2_score")
    primary = analyze(ext, ecat, "PRIMARY 60-clip")
    pilot   = analyze(inb, {}, "PILOT 18-clip")
    # combined 78
    cn_e, an_e = _minmax(ext, "clip"), _minmax(ext, "adqa")
    cn_i, an_i = _minmax(inb, "clip"), _minmax(inb, "adqa")
    g, s = [], []
    for clips, cn, an in ((ext, cn_e, an_e), (inb, cn_i, an_i)):
        for v in clips:
            for t in TIERS:
                g.append(ORDER[t]); s.append(0.5 * cn[v][t] + 0.5 * an[v][t])
    combined = {"label": "COMBINED 78-clip", "n_clips": len(ext) + len(inb), "n_obs": len(g),
                "ensemble_rho": round(spearman(g, s), 4),
                "min_detectable_rho": round(math.tanh((1.96 + 0.84) / math.sqrt(len(g) - 3)), 3)}
    out = {"primary_60": primary, "pilot_18": pilot, "combined_78": combined}
    for key in ("primary_60", "pilot_18", "combined_78"):
        r = out[key]; print(f"\n=== {r['label']} ===")
        for k, v in r.items():
            if k not in ("label", "per_category", "ensemble_losses"): print(f"  {k:22s} {v}")
        for v in r.get("ensemble_losses", []): print(f"  loss {v}")
    if "--json" in sys.argv:
        p = sys.argv[sys.argv.index("--json") + 1]
        with open(p, "w", encoding="utf-8") as f: json.dump(out, f, indent=2)
        print(f"\nwrote {p}")

if __name__ == "__main__":
    main()
