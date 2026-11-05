"""Content model for the report: blocks with automatic numbering and cross-references.

Content files append blocks with the helpers below; `resolve()` numbers chapters, sections, tables and figures and replaces
{fig:key} / {tab:key} references. The same model is rendered to DOCX (build_docx.py) and Markdown (build_md.py).
"""
import re

BLOCKS = []
REFS = {}
CH = {"n": 0, "kind": "chapter", "sec": 0, "sub": 0, "tab": 0, "fig": 0, "label": ""}


def chapter(title):
    BLOCKS.append(dict(t="chapter", title=title))


def appendix(title):
    BLOCKS.append(dict(t="appendix", title=title))


def h2(title):
    BLOCKS.append(dict(t="h2", title=title))


def h3(title):
    BLOCKS.append(dict(t="h3", title=title))


def p(text):
    BLOCKS.append(dict(t="p", text=text))


def bullets(items):
    BLOCKS.append(dict(t="bullets", items=items))


def numbered(items):
    BLOCKS.append(dict(t="numbered", items=items))


def table(key, caption, headers, rows, widths=None, fs=11, align=None):
    BLOCKS.append(dict(t="table", key=key, caption=caption, headers=headers, rows=rows, widths=widths, fs=fs, align=align))


def figure(key, file, caption, width=5.6, folder="figures", tall=False):
    BLOCKS.append(dict(t="figure", key=key, file=file, caption=caption, width=width, folder=folder, tall=tall))


def code(text, caption=None):
    BLOCKS.append(dict(t="code", text=text, caption=caption))


def references(items):
    BLOCKS.append(dict(t="references", items=items))


def resolve():
    """Assign numbers; return outline info for the TOC and the lists of tables/figures."""
    ch = 0
    ap = 0
    sec = sub = tab = fig = 0
    prefix = ""
    outline, tables, figures = [], [], []
    for b in BLOCKS:
        t = b["t"]
        if t == "chapter":
            ch += 1
            sec = sub = tab = fig = 0
            prefix = f"{ch}"
            b["num"], b["label"] = str(ch), f"CHAPTER {ch}"
            outline.append(dict(level=1, num=str(ch), title=b["title"].upper(), block=b))
        elif t == "appendix":
            ap += 1
            sec = sub = tab = fig = 0
            prefix = f"A{ap}"
            b["num"], b["label"] = f"A{ap}", f"APPENDIX {ap}"
            outline.append(dict(level=1, num=f"APPENDIX {ap}", title=b["title"].upper(), block=b, appendix=True))
        elif t == "references":
            outline.append(dict(level=1, num="", title="REFERENCES", block=b))
        elif t == "h2":
            sec += 1
            sub = 0
            b["num"] = f"{prefix.replace('A', '') if not prefix.startswith('A') else prefix}.{sec}"
            outline.append(dict(level=2, num=b["num"], title=b["title"].upper(), block=b))
        elif t == "h3":
            sub += 1
            b["num"] = f"{prefix}.{sec}.{sub}" if not prefix.startswith("A") else f"{prefix}.{sec}.{sub}"
        elif t == "table":
            tab += 1
            b["num"] = f"{prefix}.{tab}"
            REFS[f"tab:{b['key']}"] = f"Table {b['num']}"
            tables.append(b)
        elif t == "figure":
            fig += 1
            b["num"] = f"{prefix}.{fig}"
            REFS[f"fig:{b['key']}"] = f"Figure {b['num']}"
            figures.append(b)
    return outline, tables, figures


def fill(text):
    return re.sub(r"\{((?:fig|tab):[A-Za-z0-9_]+)\}", lambda m: REFS.get(m.group(1), m.group(0) + "?"), text)


def all_text():
    """Every user-visible string (used for the unresolved-reference check)."""
    out = []
    for b in BLOCKS:
        for k in ("title", "text", "caption"):
            if b.get(k):
                out.append(b[k])
        for k in ("items", "headers"):
            for it in b.get(k, []) or []:
                out.append(str(it))
        for r in b.get("rows", []) or []:
            out.extend(str(c) for c in r)
    return out
