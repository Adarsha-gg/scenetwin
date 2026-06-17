"""Build a BibTeX file by fetching arXiv metadata via the arXiv API.

Reads PDF filenames from cursor/research/papers/sources/ and writes a
combined bibliography to output/papers/scenetwin-references.bib.

The non-arXiv entries (nature_s41599... and worldscribe_uist2024) get
hand-coded stubs.
"""
from __future__ import annotations

import os
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "cursor" / "research" / "papers" / "sources"
OUT = ROOT / "output" / "papers" / "scenetwin-references.bib"
OUT.parent.mkdir(parents=True, exist_ok=True)

ARXIV_API = "http://export.arxiv.org/api/query?id_list={}"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


def safe_id(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())[:48]


def parse_entry(entry) -> dict:
    title = (entry.findtext(f"{ATOM}title") or "").strip().replace("\n", " ")
    title = re.sub(r"\s+", " ", title)
    authors = [a.findtext(f"{ATOM}name") for a in entry.findall(f"{ATOM}author")]
    published = entry.findtext(f"{ATOM}published") or ""
    year = published[:4] if published else "n.d."
    summary = (entry.findtext(f"{ATOM}summary") or "").strip().replace("\n", " ")
    summary = re.sub(r"\s+", " ", summary)
    primary = entry.find(f"{ARXIV_NS}primary_category")
    category = primary.get("term") if primary is not None else ""
    journal_ref = entry.findtext(f"{ARXIV_NS}journal_ref")
    raw_id = (entry.findtext(f"{ATOM}id") or "").strip()
    # arxiv id format: http://arxiv.org/abs/2402.07300v2
    m = re.search(r"abs/(\d{4}\.\d{4,5})", raw_id)
    aid = m.group(1) if m else ""
    return {
        "id": aid, "title": title, "authors": authors, "year": year,
        "summary": summary[:240], "category": category, "journal_ref": journal_ref,
    }


def fetch_arxiv_batch(arxiv_ids: list[str]) -> list[dict]:
    """Batch fetch up to 100 ids in a single API call."""
    url = ARXIV_API.format(",".join(arxiv_ids))
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    tree = ET.fromstring(r.text)
    return [parse_entry(e) for e in tree.findall(f"{ATOM}entry")]


def bib_entry(d: dict) -> str:
    if not d or d.get("error"):
        return f"% FAILED to fetch arXiv:{d.get('id','?')}: {d.get('error','')}\n\n"
    first_last = (d["authors"][0] or "").split()[-1] if d["authors"] else "Unknown"
    key = f"{safe_id(first_last)}{d['year']}arxiv{d['id'].replace('.','')}"
    authors = " and ".join(d["authors"])
    return (
        f"@article{{{key},\n"
        f"  title         = {{{d['title']}}},\n"
        f"  author        = {{{authors}}},\n"
        f"  year          = {{{d['year']}}},\n"
        f"  eprint        = {{{d['id']}}},\n"
        f"  archivePrefix = {{arXiv}},\n"
        f"  primaryClass  = {{{d['category']}}},\n"
        f"  url           = {{https://arxiv.org/abs/{d['id']}}},\n"
        + (f"  journal       = {{{d['journal_ref']}}},\n" if d.get('journal_ref') else "")
        + f"}}\n\n"
    )


def main():
    ids = []
    nonarxiv = []
    for f in sorted(os.listdir(SRC_DIR)):
        m = re.match(r"^arxiv_(\d{4}\.\d{4,5})\.pdf$", f)
        if m:
            ids.append(m.group(1))
        else:
            nonarxiv.append(f)
    print(f"Found {len(ids)} arXiv papers, {len(nonarxiv)} non-arXiv: {nonarxiv}")

    entries = []
    # Batch fetch in chunks of 50 to be safe
    fetched = {}
    chunk = 50
    for start in range(0, len(ids), chunk):
        batch = ids[start:start + chunk]
        print(f"Batch fetch {start+1}-{start+len(batch)} of {len(ids)}...")
        for attempt in range(3):
            try:
                results = fetch_arxiv_batch(batch)
                break
            except Exception as e:
                print(f"  retry {attempt+1}: {e}")
                time.sleep(10 * (attempt + 1))
        else:
            print(f"  giving up on batch {start}")
            results = []
        for d in results:
            if d.get("id"):
                fetched[d["id"]] = d
        time.sleep(3)  # be polite between batches

    for aid in ids:
        d = fetched.get(aid, {"id": aid, "error": "not returned by arXiv"})
        entries.append(bib_entry(d))

    # Hand-coded stubs for non-arXiv items
    if "nature_s41599-025-05201-3.pdf" in nonarxiv:
        entries.append(
            "@article{emotive2025nature,\n"
            "  title   = {Emotive vs neutral audio descriptions for blind and low-vision viewers},\n"
            "  author  = {Nature 2025 (replace with actual authors from PDF)},\n"
            "  year    = {2025},\n"
            "  journal = {Humanities and Social Sciences Communications},\n"
            "  doi     = {10.1057/s41599-025-05201-3},\n"
            "}\n\n"
        )
    if "worldscribe_uist2024.pdf" in nonarxiv:
        entries.append(
            "@inproceedings{worldscribe2024uist,\n"
            "  title     = {WorldScribe: Toward Context-Aware Live Visual Descriptions},\n"
            "  author    = {WorldScribe Authors (replace from PDF)},\n"
            "  year      = {2024},\n"
            "  booktitle = {Proceedings of ACM UIST 2024},\n"
            "  url       = {https://doi.org/10.1145/3654777.3676379},\n"
            "}\n\n"
        )

    # Add TRIBE v2 explicitly if it's not in the arXiv list (it should be, but just in case)
    OUT.write_text(
        "% SceneTwin paper bibliography -- 37 papers + non-arXiv supplements\n"
        f"% Auto-generated on 2026-05-29 from cursor/research/papers/sources/\n\n"
        + "".join(entries),
        encoding="utf-8",
    )
    print(f"\nWrote {OUT}  ({sum(1 for e in entries if not e.startswith('%'))} entries)")


if __name__ == "__main__":
    main()
