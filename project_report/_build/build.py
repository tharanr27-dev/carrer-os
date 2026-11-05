"""Builds Career_OS_Project_Report.docx / .pdf / _Source.md. Usage: python build.py"""
import json
import os
import re
import subprocess
import sys

import fitz  # PyMuPDF

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)

import docmodel as M  # noqa: E402
import content1, content2, content3, content4  # noqa: E402,F401  (importing appends the blocks)
from build_docx import build  # noqa: E402

DOCX = os.path.join(ROOT, "Career_OS_Project_Report.docx")
PDF = os.path.join(ROOT, "Career_OS_Project_Report.pdf")
FRONT = content1.FRONT


def roman(n):
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


def export_pdf():
    ps = (
        "$ErrorActionPreference='Stop'; $w=New-Object -ComObject Word.Application; $w.Visible=$false; $w.DisplayAlerts=0;"
        f"$d=$w.Documents.Open('{DOCX}', $false, $true); $d.ExportAsFixedFormat('{PDF}', 17); $d.Close(0); $w.Quit();"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[:500])


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def measure(outline, tables, figures):
    doc = fitz.open(PDF)
    texts = [norm(pg.get_text()) for pg in doc]
    n = len(texts)
    body = next(i for i, t in enumerate(texts) if re.search(r"CHAPTER 1 INTRODUCTION", t) and "CHAPTER NO." not in t)

    def disp(i):
        return roman(i + 1) if i < body else str(i - body + 1)

    pages = {}
    for name, key in (("ABSTRACT", "ABSTRACT"), ("LIST OF TABLES", "TABLE NO."), ("LIST OF FIGURES", "FIGURE NO."),
                      ("LIST OF SYMBOLS, ABBREVIATIONS AND NOMENCLATURE", "Abbreviation Expansion")):
        idx = next((i for i in range(1, body) if (name in texts[i] and (key in texts[i] if key != "ABSTRACT" else True)) and "TABLE OF CONTENTS" not in texts[i][:60]), None)
        pages["front:" + name] = disp(idx) if idx is not None else "?"
    for o in outline:
        if o["level"] == 1:
            if o["title"] == "REFERENCES":
                pat = "REFERENCES"
                start = next((i for i in range(body, n) if re.match(r"^\d+ REFERENCES", texts[i])), None)
            elif o.get("appendix"):
                pat = f"{o['num']} {o['title']}"
                start = next((i for i in range(body, n) if pat in texts[i]), None)
            else:
                pat = f"CHAPTER {o['num']} {o['title']}"
                start = next((i for i in range(body, n) if pat in texts[i]), None)
        else:
            pat = f"{o['num']} {o['title']}"
            start = next((i for i in range(body, n) if pat in texts[i]), None)
        pages[f"outline:{o['num']}|{o['title']}"] = disp(start) if start is not None else "?"
    for kind, items, word in (("tab", tables, "Table"), ("fig", figures, "Figure")):
        for b in items:
            pat = norm(f"{word} {b['num']} {M.fill(b['caption'])}")
            start = next((i for i in range(body, n) if pat in texts[i]), None)
            if start is None:  # captions may be split by a page break; fall back to the numbered prefix
                start = next((i for i in range(body, n) if f"{word} {b['num']} " in texts[i]), None)
            pages[f"{kind}:{b['num']}"] = disp(start) if start is not None else "?"
    return pages, n, body


def main():
    pages = {}
    for rnd in range(1, 5):
        outline, tables, figures = build(DOCX, pages, FRONT)
        export_pdf()
        new, n, body = measure(outline, tables, figures)
        print(f"pass {rnd}: {n} pages, body starts on PDF page {body + 1}, unresolved: {[k for k, v in new.items() if v == '?'][:5]}")
        if new == pages:
            break
        pages = new
        M.BLOCKS.clear() if False else None
    json.dump(pages, open(os.path.join(HERE, "data", "pages.json"), "w"), indent=1)
    print("final page count:", n)
    ch = [(k[8:].split("|", 1), v) for k, v in pages.items() if k.startswith("outline:") and "." not in k[8:].split("|", 1)[0]]
    print("front:", {k: v for k, v in pages.items() if k.startswith("front:")})
    print([f"{a[0] or 'REF'}:{v}" for a, v in ch])


if __name__ == "__main__":
    main()
