#!/usr/bin/env python3
"""Build submission artifacts from the SceneTwin Markdown draft.

Outputs:
- output/papers/scenetwin-submission.tex
- output/papers/scenetwin-submission.html

The LaTeX is self-contained and uses manual references from the draft. The HTML
is a print-ready fallback for environments without a TeX engine.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "output" / "reports" / "paper-scenetwin-submission-draft.md"
OUT_DIR = ROOT / "output" / "papers"
TEX_OUT = OUT_DIR / "scenetwin-submission.tex"
HTML_OUT = OUT_DIR / "scenetwin-submission.html"

TITLE = "SceneTwin: Human-Reference-Free Audio Description Auditing with Visual Grounding, Frame-Grounded QA, and Review Triage"
AUTHOR = "Adarsha Mishra"
AFFILIATION = "William Paterson University"

FIGURES = {
    "4. Method": [
        ("../charts/scenetwin_methodology.png", "SceneTwin audit stack: CLIP visual grounding, frame-grounded ADQA, safety gates, and TRIBE review triage."),
    ],
    "5. Main Results": [
        ("../charts/scenetwin_per_tier_heatmap.png", "Corrected-ladder score structure across cross-decoy, crowd-caption, and professional-AD candidates."),
    ],
    "7. Deployment Safety Gates": [
        ("../charts/scenetwin_gate_summary.png", "Safety-gate summary for hallucination and grounding-drop checks."),
        ("../charts/scenetwin_wrong_content_global_gate.png", "Wrong-content gate separates cross-decoy descriptions from legitimate same-clip descriptions."),
    ],
    "8. TRIBE Review Triage and Access-Surface Routing": [
        ("../charts/scenetwin_failure_forecast.png", "TRIBE review-priority visualization for cached benchmark clips; main text reports the safer external cheap-baseline triage result."),
    ],
}


def read_body() -> str:
    text = DRAFT.read_text(encoding="utf-8")
    if text.startswith("---"):
        _, _, rest = text.partition("---")
        _, _, text = rest.partition("---")
    return text.strip()


def split_abstract(text: str) -> tuple[str, str]:
    m = re.search(r"^## Abstract\s*$", text, flags=re.MULTILINE)
    if not m:
        return "", text
    start = m.end()
    n = re.search(r"^## ", text[start:], flags=re.MULTILINE)
    if not n:
        return text[start:].strip(), ""
    abstract = text[start:start + n.start()].strip()
    body = text[start + n.start():].strip()
    return abstract, body


def strip_title_block(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    skipping = True
    for line in lines:
        if skipping:
            if line.startswith("## Abstract"):
                skipping = False
                out.append(line)
            elif line.startswith("# ") or line.strip() in {AUTHOR, AFFILIATION, ""}:
                continue
            else:
                continue
        else:
            out.append(line)
    return "\n".join(out)


LATEX_REPL = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def latex_escape(text: str) -> str:
    placeholders: list[str] = []

    def stash(value: str) -> str:
        placeholders.append(value)
        return f"@@SCENETWIN{len(placeholders)-1}@@"

    text = text.replace("ρ", stash(r"$\rho$"))
    text = text.replace("→", stash(r"$\rightarrow$"))
    text = text.replace("<", stash(r"$<$"))
    text = text.replace(">", stash(r"$>$"))
    text = text.replace("≤", stash(r"$\leq$"))
    text = text.replace("≥", stash(r"$\geq$"))
    text = text.replace("×", stash(r"$\times$"))
    text = text.replace("—", "---").replace("–", "--")
    text = text.replace("“", "``").replace("”", "''").replace("’", "'")
    text = "".join(LATEX_REPL.get(ch, ch) for ch in text)
    text = re.sub(r"\*\*(.+?)\*\*", lambda m: r"\textbf{" + m.group(1) + "}", text)
    text = re.sub(r"`([^`]+)`", lambda m: r"\texttt{" + m.group(1) + "}", text)
    for i, value in enumerate(placeholders):
        text = text.replace(f"@@SCENETWIN{i}@@", value)
    return text


def strip_heading_number(title: str) -> str:
    # Handles both "2. Related Work" and "2.1 Automated audio description".
    return re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", title.strip())


def parse_table(lines: list[str], i: int) -> tuple[str, int]:
    block: list[str] = []
    while i < len(lines) and lines[i].strip().startswith("|"):
        block.append(lines[i].strip())
        i += 1
    rows = []
    for line in block:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return "", i
    ncols = max(len(r) for r in rows)
    colspec = "@{}" + "l" * ncols + "@{}"
    env = "table*" if ncols > 4 else "table"
    size = r"\scriptsize" if ncols > 4 else r"\small"
    out = [rf"\begin{{{env}}}[t]", r"\centering", size, rf"\begin{{tabular}}{{{colspec}}}", r"\toprule"]
    for ridx, row in enumerate(rows):
        row = row + [""] * (ncols - len(row))
        out.append(" & ".join(latex_escape(c) for c in row) + r" \\")
        if ridx == 0:
            out.append(r"\midrule")
    out.extend([r"\bottomrule", r"\end{tabular}", rf"\end{{{env}}}"])
    return "\n".join(out), i


def figure_latex(section_key: str) -> str:
    figs = FIGURES.get(section_key, [])
    if not figs:
        return ""
    out = []
    for rel, caption in figs:
        out.extend([
            r"\begin{figure*}[t]",
            r"\centering",
            rf"\includegraphics[width=0.92\textwidth]{{{rel}}}",
            rf"\caption{{{latex_escape(caption)}}}",
            r"\end{figure*}",
            "",
        ])
    return "\n".join(out)


def markdown_to_latex(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    list_mode: str | None = None
    in_code = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                out.append(r"\end{verbatim}")
                in_code = False
            else:
                out.append(r"\begin{verbatim}")
                in_code = True
            i += 1
            continue
        if in_code:
            out.append(line)
            i += 1
            continue
        if stripped.startswith("|"):
            if list_mode:
                out.append(rf"\end{{{list_mode}}}")
                list_mode = None
            table, i = parse_table(lines, i)
            out.append(table)
            continue
        if not stripped:
            if list_mode:
                out.append(rf"\end{{{list_mode}}}")
                list_mode = None
            out.append("")
            i += 1
            continue
        h2 = re.match(r"^##\s+(.+)$", stripped)
        h3 = re.match(r"^###\s+(.+)$", stripped)
        if h2:
            if list_mode:
                out.append(rf"\end{{{list_mode}}}")
                list_mode = None
            title = h2.group(1).strip()
            if title == "References":
                out.append(r"\section*{References}")
            else:
                out.append(rf"\section{{{latex_escape(strip_heading_number(title))}}}")
                out.append(figure_latex(title))
            i += 1
            continue
        if h3:
            if list_mode:
                out.append(rf"\end{{{list_mode}}}")
                list_mode = None
            out.append(rf"\subsection{{{latex_escape(strip_heading_number(h3.group(1)))}}}")
            i += 1
            continue
        if stripped.startswith(">"):
            if list_mode:
                out.append(rf"\end{{{list_mode}}}")
                list_mode = None
            out.append(r"\begin{quote}" + latex_escape(stripped.lstrip("> ")) + r"\end{quote}")
            i += 1
            continue
        m_num = re.match(r"^\d+\.\s+(.+)$", stripped)
        m_bul = re.match(r"^-\s+(.+)$", stripped)
        if m_num:
            if list_mode != "enumerate":
                if list_mode:
                    out.append(rf"\end{{{list_mode}}}")
                out.append(r"\begin{enumerate}[leftmargin=*]")
                list_mode = "enumerate"
            out.append(r"\item " + latex_escape(m_num.group(1)))
            i += 1
            continue
        if m_bul:
            if list_mode != "itemize":
                if list_mode:
                    out.append(rf"\end{{{list_mode}}}")
                out.append(r"\begin{itemize}[leftmargin=*]")
                list_mode = "itemize"
            out.append(r"\item " + latex_escape(m_bul.group(1)))
            i += 1
            continue
        if list_mode:
            out.append(rf"\end{{{list_mode}}}")
            list_mode = None
        out.append(latex_escape(stripped) + "\n")
        i += 1
    if list_mode:
        out.append(rf"\end{{{list_mode}}}")
    return "\n".join(out)


def build_tex(abstract: str, body: str) -> str:
    body_tex = markdown_to_latex(body)
    abstract_tex = "\n\n".join(latex_escape(p.strip()) for p in abstract.split("\n\n") if p.strip())
    return rf"""\documentclass[10pt,twocolumn]{{article}}
\usepackage[letterpaper,margin=0.72in]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{booktabs}}
\usepackage{{array}}
\usepackage{{hyperref}}
\usepackage{{amsmath}}
\usepackage{{enumitem}}
\usepackage{{caption}}
\usepackage{{times}}
\usepackage[T1]{{fontenc}}
\usepackage[utf8]{{inputenc}}
\setlength{{\columnsep}}{{0.22in}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{0.45em}}
\hypersetup{{colorlinks=true,linkcolor=black,citecolor=black,urlcolor=blue}}
\title{{\textbf{{{latex_escape(TITLE)}}}}}
\author{{{latex_escape(AUTHOR)}\\{latex_escape(AFFILIATION)}}}
\date{{June 26, 2026}}
\begin{{document}}
\maketitle
\begin{{abstract}}
{abstract_tex}
\end{{abstract}}

\noindent\textbf{{Keywords:}} audio description; blind and low-vision accessibility; reference-free evaluation; video understanding; hallucination detection; human-AI authoring; review triage

{body_tex}
\end{{document}}
"""


def html_inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def parse_html_table(lines: list[str], i: int) -> tuple[str, int]:
    block: list[str] = []
    while i < len(lines) and lines[i].strip().startswith("|"):
        block.append(lines[i].strip())
        i += 1
    rows = []
    for line in block:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return "", i
    head, body = rows[0], rows[1:]
    parts = ["<table><thead><tr>"]
    parts.extend(f"<th>{html_inline(c)}</th>" for c in head)
    parts.append("</tr></thead><tbody>")
    for row in body:
        parts.append("<tr>")
        parts.extend(f"<td>{html_inline(c)}</td>" for c in row)
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts), i


def figure_html(section_key: str) -> str:
    figs = FIGURES.get(section_key, [])
    if not figs:
        return ""
    out = []
    for rel, caption in figs:
        out.append(f'<figure><img src="{html.escape(rel)}" alt=""><figcaption>{html.escape(caption)}</figcaption></figure>')
    return "\n".join(out)


def markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    in_code = False
    list_mode: str | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                out.append("<pre><code>")
                in_code = True
            i += 1
            continue
        if in_code:
            out.append(html.escape(line))
            i += 1
            continue
        if stripped.startswith("|"):
            if list_mode:
                out.append(f"</{list_mode}>")
                list_mode = None
            table, i = parse_html_table(lines, i)
            out.append(table)
            continue
        if not stripped:
            if list_mode:
                out.append(f"</{list_mode}>")
                list_mode = None
            i += 1
            continue
        h2 = re.match(r"^##\s+(.+)$", stripped)
        h3 = re.match(r"^###\s+(.+)$", stripped)
        if h2:
            if list_mode:
                out.append(f"</{list_mode}>")
                list_mode = None
            title = h2.group(1).strip()
            out.append(f"<h2>{html.escape(strip_heading_number(title))}</h2>")
            out.append(figure_html(title))
            i += 1
            continue
        if h3:
            if list_mode:
                out.append(f"</{list_mode}>")
                list_mode = None
            out.append(f"<h3>{html.escape(strip_heading_number(h3.group(1)))}</h3>")
            i += 1
            continue
        if stripped.startswith(">"):
            out.append(f"<blockquote>{html_inline(stripped.lstrip('> '))}</blockquote>")
            i += 1
            continue
        m_num = re.match(r"^\d+\.\s+(.+)$", stripped)
        m_bul = re.match(r"^-\s+(.+)$", stripped)
        if m_num:
            if list_mode != "ol":
                if list_mode:
                    out.append(f"</{list_mode}>")
                out.append("<ol>")
                list_mode = "ol"
            out.append(f"<li>{html_inline(m_num.group(1))}</li>")
            i += 1
            continue
        if m_bul:
            if list_mode != "ul":
                if list_mode:
                    out.append(f"</{list_mode}>")
                out.append("<ul>")
                list_mode = "ul"
            out.append(f"<li>{html_inline(m_bul.group(1))}</li>")
            i += 1
            continue
        if list_mode:
            out.append(f"</{list_mode}>")
            list_mode = None
        out.append(f"<p>{html_inline(stripped)}</p>")
        i += 1
    if list_mode:
        out.append(f"</{list_mode}>")
    return "\n".join(out)


def build_html(abstract: str, body: str) -> str:
    abstract_html = "\n".join(f"<p>{html_inline(p.strip())}</p>" for p in abstract.split("\n\n") if p.strip())
    body_html = markdown_to_html(body)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(TITLE)}</title>
<style>
@page {{ size: Letter; margin: 0.65in; }}
* {{ box-sizing: border-box; }}
body {{ font-family: Arial, Helvetica, sans-serif; color: #111; font-size: 10.2pt; line-height: 1.36; margin: 0 auto; max-width: 7.3in; }}
h1 {{ font-size: 20pt; line-height: 1.08; margin: 0 0 0.25in; text-align: center; }}
.author {{ text-align: center; margin-bottom: 0.25in; }}
h2 {{ font-size: 13pt; margin: 0.22in 0 0.06in; border-bottom: 1px solid #aaa; padding-bottom: 2px; }}
h3 {{ font-size: 11pt; margin: 0.16in 0 0.04in; }}
p {{ margin: 0 0 0.075in; }}
.abstract {{ border: 1px solid #bbb; padding: 0.12in; margin-bottom: 0.14in; background: #f7f7f7; }}
.abstract h2 {{ border: 0; margin-top: 0; padding: 0; }}
table {{ width: 100%; border-collapse: collapse; font-size: 8.5pt; margin: 0.10in 0 0.15in; page-break-inside: avoid; }}
th, td {{ border: 1px solid #ccc; padding: 3px 4px; vertical-align: top; }}
th {{ background: #efefef; font-weight: 700; }}
figure {{ margin: 0.12in 0; page-break-inside: avoid; }}
figure img {{ max-width: 100%; display: block; margin: 0 auto; border: 1px solid #ddd; }}
figcaption {{ font-size: 8.7pt; color: #333; margin-top: 4px; }}
blockquote {{ margin: 0.1in 0.2in; color: #333; font-style: italic; }}
code, pre {{ font-family: Consolas, monospace; }}
pre {{ background: #f4f4f4; padding: 0.08in; white-space: pre-wrap; }}
ul, ol {{ margin-top: 0.04in; margin-bottom: 0.08in; padding-left: 0.22in; }}
li {{ margin-bottom: 0.035in; }}
</style>
</head>
<body>
<h1>{html.escape(TITLE)}</h1>
<div class="author"><strong>{html.escape(AUTHOR)}</strong><br>{html.escape(AFFILIATION)}<br>June 26, 2026</div>
<section class="abstract"><h2>Abstract</h2>{abstract_html}<p><strong>Keywords:</strong> audio description; blind and low-vision accessibility; reference-free evaluation; video understanding; hallucination detection; human-AI authoring; review triage</p></section>
{body_html}
</body>
</html>
"""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    full = read_body()
    full = strip_title_block(full)
    abstract, body = split_abstract(full)
    abstract = re.sub(r"\n?\*\*Keywords:\*\*.*", "", abstract).strip()
    TEX_OUT.write_text(build_tex(abstract, body), encoding="utf-8")
    HTML_OUT.write_text(build_html(abstract, body), encoding="utf-8")
    print(f"wrote {TEX_OUT.relative_to(ROOT)}")
    print(f"wrote {HTML_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
