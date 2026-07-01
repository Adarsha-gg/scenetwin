"""Build a BibTeX file from local INDEX.md + writeup pages (offline, no API).

Titles come from each `.md` per-paper writeup; arxiv IDs from the INDEX.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "cursor" / "research" / "papers" / "INDEX.md"
PAPERS_DIR = ROOT / "cursor" / "research" / "papers"
OUT = ROOT / "output" / "papers" / "scenetwin-references.bib"
OUT.parent.mkdir(parents=True, exist_ok=True)


def read_title_from_writeup(md_path: Path) -> str:
    """First # heading of the markdown."""
    if not md_path.exists():
        return ""
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            t = line[2:].strip()
            t = re.sub(r"\s*\(.*?\)\s*$", "", t)  # drop trailing parens
            t = re.sub(r"\s*[—-].*$", "", t)      # drop subtitles after em-dash
            return t.strip()
    return ""


def safe_key(stem: str, year: str, aid: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "", stem.lower())
    return f"{base}{year}{aid.replace('.', '')}"


def main():
    # Parse INDEX for (file, arxiv_id) pairs
    rows = []
    in_table = False
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        if "|-------|" in line:
            in_table = True
            continue
        if not in_table or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        paper_name = cells[0]
        link = cells[1]
        arxiv_field = cells[2]
        # link like "[adqa.md](adqa.md)" -> stem "adqa"
        m_link = re.search(r"\(([^)]+)\.md\)", link)
        if not m_link:
            continue
        stem = m_link.group(1)
        # arxiv field can be "2510.00808" or "2602.02684, 2605.05348" or "Nature 2025"
        for aid in re.findall(r"\b(\d{4}\.\d{4,5})\b", arxiv_field):
            rows.append((paper_name, stem, aid))

    print(f"Parsed {len(rows)} arxiv entries from INDEX")

    entries = []
    for paper_name, stem, aid in rows:
        title = read_title_from_writeup(PAPERS_DIR / f"{stem}.md") or paper_name
        # year from arxiv id "YYMM.NNNNN" -> year 20YY (e.g. 2402 = 2024, 2510 = 2025, 2602 = 2026)
        yy = int(aid[:2])
        # 2-digit year heuristic: 20-29 are 2020-2029, 30-99 would be 1930-1999 (unlikely)
        year = f"20{yy:02d}" if yy < 80 else f"19{yy:02d}"
        key = safe_key(stem, year, aid)
        entry = (
            f"@article{{{key},\n"
            f"  title         = {{{title}}},\n"
            f"  author        = {{TODO: fill from PDF first author}},\n"
            f"  year          = {{{year}}},\n"
            f"  eprint        = {{{aid}}},\n"
            f"  archivePrefix = {{arXiv}},\n"
            f"  url           = {{https://arxiv.org/abs/{aid}}},\n"
            f"  note          = {{Paper writeup: cursor/research/papers/{stem}.md}},\n"
            f"}}\n\n"
        )
        entries.append(entry)

    # Non-arXiv items
    entries.append(
        "@article{emotive2025nature,\n"
        "  title   = {Emotive vs neutral audio descriptions for blind and low-vision viewers},\n"
        "  author  = {TODO: fill from PDF first author},\n"
        "  year    = {2025},\n"
        "  journal = {Humanities and Social Sciences Communications},\n"
        "  doi     = {10.1057/s41599-025-05201-3},\n"
        "  note    = {Paper writeup: cursor/research/papers/emotive-ad-style.md},\n"
        "}\n\n"
    )
    entries.append(
        "@inproceedings{worldscribe2024uist,\n"
        "  title     = {WorldScribe: Toward Context-Aware Live Visual Descriptions},\n"
        "  author    = {TODO: fill from PDF first author},\n"
        "  year      = {2024},\n"
        "  booktitle = {Proceedings of ACM UIST 2024},\n"
        "  doi       = {10.1145/3654777.3676379},\n"
        "  note      = {Paper writeup: cursor/research/papers/worldscribe.md},\n"
        "}\n\n"
    )

    # SceneTwin's own citations (TRIBE v2 directly)
    entries.append(
        "@article{tribev22026,\n"
        "  title         = {TRIBE: A Foundation Model of Vision, Audition, and Language for In-Silico Neuroscience},\n"
        "  author        = {TODO: fill from PDF; D{\\'e}fossez et al.},\n"
        "  year          = {2026},\n"
        "  eprint        = {2605.04326},\n"
        "  archivePrefix = {arXiv},\n"
        "  url           = {https://arxiv.org/abs/2605.04326},\n"
        "  note          = {Meta AI Research; see https://huggingface.co/facebook/tribev2},\n"
        "}\n\n"
    )

    OUT.write_text(
        "% SceneTwin paper bibliography -- 37 papers + non-arXiv supplements\n"
        "% Auto-generated 2026-05-29 from cursor/research/papers/INDEX.md (offline).\n"
        "% TODO entries: open the corresponding PDF in cursor/research/papers/sources/\n"
        "% and fill in the first author for each entry.\n\n"
        + "".join(entries),
        encoding="utf-8",
    )
    n_entries = sum(1 for e in entries)
    print(f"Wrote {OUT}  ({n_entries} entries)")


if __name__ == "__main__":
    main()
