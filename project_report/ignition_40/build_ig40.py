"""Builds the 40-page Ignition-format report (DOCX + PDF via Word). Usage: python build_ig40.py"""
import json
import os
import re
import subprocess
import sys

import fitz
from PIL import Image
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content40 as C  # noqa: E402

DOCX = os.path.join(HERE, "Career_OS_Project_Report_40_Pages.docx")
PDF = os.path.join(HERE, "Career_OS_Project_Report_40_Pages.pdf")
PAGES = os.path.join(HERE, "pages.json")
J, CT, L = WD_ALIGN_PARAGRAPH.JUSTIFY, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT
FONT = "Times New Roman"


def runs(par, text, size=12, bold=False, italic=False):
    # **bold** and *italic* inline markup
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not part:
            continue
        b, i = bold, italic
        if part.startswith("**"):
            part, b = part[2:-2], True
        elif part.startswith("*"):
            part, i = part[1:-1], True
        r = par.add_run(part)
        r.font.name, r.font.size, r.bold, r.italic = FONT, Pt(size), b, i
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)


def para(doc, text="", align=J, size=12, bold=False, italic=False, indent=False, before=0, after=6, line=1.5, keep=False):
    par = doc.add_paragraph()
    f = par.paragraph_format
    f.alignment, f.space_before, f.space_after, f.line_spacing = align, Pt(before), Pt(after), line
    if indent:
        f.first_line_indent = Cm(1.27)
    if keep:
        f.keep_with_next = True
    runs(par, text, size, bold, italic)
    return par


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def no_borders(tbl):
    tblPr = tbl._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        x = OxmlElement(f"w:{e}")
        x.set(qn("w:val"), "nil")
        b.append(x)
    tblPr.append(b)


def cell_text(cell, text, size=10.5, bold=False, align=L, line=1.0, after=0):
    cell.paragraphs[0].text = ""
    lines = text.split("\n")
    for k, t in enumerate(lines):
        par = cell.paragraphs[0] if k == 0 else cell.add_paragraph()
        f = par.paragraph_format
        f.alignment, f.space_after, f.space_before, f.line_spacing = align, Pt(after), Pt(0), line
        runs(par, t, size, bold)


def set_widths(tbl, widths):
    for row in tbl.rows:
        for c, w in zip(row.cells, widths):
            c.width = Cm(w)


def footer_page(section, fmt, start):
    section.footer.is_linked_to_previous = False
    sp = section._sectPr
    for old in sp.findall(qn("w:pgNumType")):
        sp.remove(old)
    pg = OxmlElement("w:pgNumType")
    pg.set(qn("w:fmt"), fmt or "decimal")
    pg.set(qn("w:start"), str(start))
    sp.append(pg)
    par = section.footer.paragraphs[0]
    par.alignment = CT
    r = par.add_run()
    r.font.name, r.font.size = FONT, Pt(12)
    for kind, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), kind)
        else:
            e = OxmlElement("w:instrText")
            e.set(qn("xml:space"), "preserve")
            e.text = txt
        r._r.append(e)


def margins(s):
    s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    s.left_margin, s.right_margin, s.top_margin, s.bottom_margin = Cm(3.0), Cm(2.0), Cm(2.5), Cm(2.2)
    s.footer_distance = Cm(1.2)


def picture(doc, path, wmax, hmax):
    w, h = Image.open(path).size
    width = min(wmax, hmax * w / h)
    par = doc.add_paragraph()
    par.alignment = CT
    f = par.paragraph_format
    f.space_before, f.space_after, f.keep_with_next, f.line_spacing = Pt(4), Pt(2), True, 1.0
    par.add_run().add_picture(path, width=Cm(width))


def caption(doc, text, keep=False, before=2, after=8):
    return para(doc, text, CT, 11, bold=True, before=before, after=after, line=1.0, keep=keep)


# ------------------------------------------------------------------ front matter
def cover(doc):
    t = doc.add_table(rows=1, cols=3)
    no_borders(t)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_widths(t, [3.2, 9.4, 3.2])
    c0, c1, c2 = t.rows[0].cells
    for c, img, w in ((c0, "logo_left.png", 2.4), (c2, "logo_right.png", 2.4)):
        pp = c.paragraphs[0]
        pp.alignment = CT
        pp.add_run().add_picture(os.path.join(HERE, "assets", img), width=Cm(w))
    cell_text(c1, "CAREER OS: AI-POWERED\nJOB PREPARATION AND\nCAREER READINESS\nPLATFORM", 16, True, CT, 1.5)
    para(doc, "PROJECT REPORT", CT, 14, True, before=30, after=18)
    para(doc, "Submitted by", CT, 12, italic=True, after=14)
    nt = doc.add_table(rows=len(C.TEAM), cols=2)
    no_borders(nt)
    nt.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_widths(nt, [6.0, 4.2])
    for row, (n, r) in zip(nt.rows, C.TEAM):
        cell_text(row.cells[0], n, 12, True, WD_ALIGN_PARAGRAPH.RIGHT, 1.0, 6)
        cell_text(row.cells[1], f"   ({r})", 12, True, L, 1.0, 6)
    para(doc, "In partial fulfilment for the award of the degree of", CT, 12, italic=True, before=26, after=16)
    para(doc, "BACHELOR OF TECHNOLOGY", CT, 12, True, after=10)
    para(doc, "IN", CT, 12, after=10)
    para(doc, "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE", CT, 12, True, after=26)
    para(doc, "SRI SHAKTHI INSTITUTE OF ENGINEERING AND TECHNOLOGY", CT, 12, True, after=6)
    para(doc, "COIMBATORE – 641 062", CT, 12, True, after=6)
    para(doc, "An Autonomous Institute,", CT, 12, after=2)
    para(doc, "Accredited by NAAC with “A” Grade", CT, 12, after=10)
    para(doc, "ANNA UNIVERSITY: CHENNAI 600 025", CT, 12, True, after=10)
    para(doc, "NOVEMBER 2026", CT, 12, True, after=0)
    page_break(doc)


def bonafide(doc):
    para(doc, "BONAFIDE CERTIFICATE", CT, 14, True, after=24)
    names = ", ".join(f"{n} ({r})" for n, r in C.TEAM)
    para(doc, f"Certified that this project report “**{C.TITLE}**” is the bonafide work of “**{names}**” who carried out the project work under my supervision.", J, 12, indent=True, line=2.0, after=50)
    t = doc.add_table(rows=1, cols=2)
    no_borders(t)
    set_widths(t, [8.0, 8.0])
    blocks = [
        "**SIGNATURE**\n\n\n\n**Dr. KAMALAVENI V**\n**M.E., Ph.D.**\n**PROJECT GUIDE**\nAssistant Professor,\nDepartment of Artificial Intelligence and Data Science,\nSri Shakthi Institute of Engineering and Technology, Coimbatore – 641 062.",
        "**SIGNATURE**\n\n\n\n**Dr. N. M. SARAVANA KUMAR**\n**M.E., Ph.D.**\n**HEAD OF THE DEPARTMENT**\nDepartment of Artificial Intelligence and Data Science,\nSri Shakthi Institute of Engineering and Technology, Coimbatore – 641 062.",
    ]
    for c, b in zip(t.rows[0].cells, blocks):
        cell_text(c, b, 12, False, L, 1.15, 0)
    para(doc, "Submitted for the project viva-voce examination held on ____________________", L, 12, True, before=60, after=60)
    t2 = doc.add_table(rows=1, cols=2)
    no_borders(t2)
    set_widths(t2, [8.0, 8.0])
    cell_text(t2.rows[0].cells[0], "INTERNAL EXAMINER", 12, True, L)
    cell_text(t2.rows[0].cells[1], "EXTERNAL EXAMINER", 12, True, WD_ALIGN_PARAGRAPH.RIGHT)


def team_block(doc):
    t = doc.add_table(rows=len(C.TEAM), cols=2)
    no_borders(t)
    t.alignment = WD_TABLE_ALIGNMENT.RIGHT
    set_widths(t, [5.0, 3.6])
    for row, (n, r) in zip(t.rows, C.TEAM):
        cell_text(row.cells[0], n, 12, True, WD_ALIGN_PARAGRAPH.RIGHT, 1.0, 4)
        cell_text(row.cells[1], f"   ({r})", 12, True, L, 1.0, 4)


def heading_page(doc, text):
    para(doc, text, CT, 14, True, after=18, keep=True)


def toc(doc, pages):
    heading_page(doc, "TABLE OF CONTENTS")
    t = doc.add_table(rows=1, cols=4)
    no_borders(t)
    set_widths(t, [1.8, 1.2, 10.6, 2.4])
    h = t.rows[0].cells
    cell_text(h[0], "CHAPTER NO.", 11, True)
    h[1].merge(h[2])
    cell_text(h[1], "TITLE", 11, True)
    cell_text(h[3], "PAGE NO.", 11, True, WD_ALIGN_PARAGRAPH.RIGHT)

    def row(a, b, c, pg, bold):
        r = t.add_row().cells
        cell_text(r[0], a, 11, bold, L, 1.0, 3)
        if b == "":
            r[1].merge(r[2])
            cell_text(r[1], c, 11, bold, L, 1.0, 3)
        else:
            cell_text(r[1], b, 11, bold, L, 1.0, 3)
            cell_text(r[2], c, 11, bold, L, 1.0, 3)
        cell_text(r[3], str(pg), 11, bold, WD_ALIGN_PARAGRAPH.RIGHT, 1.0, 3)

    for key in ("ACKNOWLEDGEMENT", "ABSTRACT", "LIST OF TABLES", "LIST OF FIGURES", "LIST OF SYMBOLS, ABBREVIATIONS AND NOMENCLATURE"):
        row("", "", key, pages.get(key, "?"), True)
    for b in C.B:
        if b[0] == "ch":
            row(f"{b[1]}.", "", b[2], pages.get(f"CH{b[1]}", "?"), True)
        elif b[0] == "h2":
            n, title = b[1].split(" ", 1)
            row("", n, title, pages.get(b[1], "?"), False)
    row("8.", "", "REFERENCES", pages.get("REFERENCES", "?"), True)
    set_widths(t, [1.8, 1.2, 10.6, 2.4])


def list_of(doc, title, word, kind, pages):
    heading_page(doc, title)
    t = doc.add_table(rows=1, cols=3)
    no_borders(t)
    h = t.rows[0].cells
    cell_text(h[0], f"{word} NO.", 11, True)
    cell_text(h[1], "TITLE", 11, True, CT)
    cell_text(h[2], "PAGE NO.", 11, True, WD_ALIGN_PARAGRAPH.RIGHT)
    for b in C.B:
        if b[0] in kind:
            m = re.match(r"(?:Table|Fig\.) ([\d.]+): (.*)", b[1])
            r = t.add_row().cells
            cell_text(r[0], m.group(1), 11, False, L, 1.0, 4)
            cell_text(r[1], m.group(2), 11, False, L, 1.0, 4)
            cell_text(r[2], str(pages.get(b[1], "?")), 11, False, WD_ALIGN_PARAGRAPH.RIGHT, 1.0, 4)
    set_widths(t, [2.6, 11.0, 2.4])


# ------------------------------------------------------------------ body
def table(doc, cap, head, rows, widths):
    caption(doc, cap, keep=True, before=6, after=4)
    t = doc.add_table(rows=1, cols=len(head))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for c, x in zip(t.rows[0].cells, head):
        cell_text(c, x, 10.5, True, CT)
    for r in rows:
        cells = t.add_row().cells
        for c, x in zip(cells, r):
            cell_text(c, x, 10.5)
    set_widths(t, widths)
    # repeat header row, keep rows together where possible
    trPr = t.rows[0]._tr.get_or_add_trPr()
    e = OxmlElement("w:tblHeader")
    e.set(qn("w:val"), "true")
    trPr.append(e)
    for row in t.rows:
        cant = OxmlElement("w:cantSplit")
        row._tr.get_or_add_trPr().append(cant)
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(4)
    sp.paragraph_format.line_spacing = 1.0


def body(doc):
    first = True
    for b in C.B:
        k = b[0]
        if k == "ch":
            if not first:
                page_break(doc)
            first = False
            para(doc, f"CHAPTER {b[1]}", CT, 14, True, after=6, keep=True)
            para(doc, b[2], CT, 14, True, after=18, keep=True)
        elif k == "h2":
            para(doc, b[1], L, 12, True, before=8, after=6, keep=True)
        elif k == "p":
            para(doc, b[1], J, 12, indent=True)
        elif k in ("bul", "num"):
            for i, x in enumerate(b[1], 1):
                par = para(doc, "", J, 12, after=3)
                f = par.paragraph_format
                f.left_indent, f.first_line_indent = Cm(1.27), Cm(-0.63)
                runs(par, ("•  " if k == "bul" else f"{i}. ") + x, 12)
        elif k == "tab":
            table(doc, *b[1:])
        elif k == "fig":
            picture(doc, b[2], b[3], b[4])
            caption(doc, b[1])
        elif k == "code":
            for ln in b[1].split("\n"):
                par = doc.add_paragraph()
                f = par.paragraph_format
                f.space_after, f.line_spacing, f.left_indent = Pt(0), 1.0, Cm(0.5)
                r = par.add_run(ln)
                r.font.name, r.font.size = "Courier New", Pt(9)
            doc.add_paragraph().paragraph_format.space_after = Pt(2)
    page_break(doc)
    para(doc, "CHAPTER 8", CT, 14, True, after=6, keep=True)
    para(doc, "REFERENCES", CT, 14, True, after=18, keep=True)
    for i, r in enumerate(C.REFS, 1):
        par = para(doc, "", J, 11.5, line=1.15, after=5)
        f = par.paragraph_format
        f.left_indent, f.first_line_indent = Cm(1.1), Cm(-1.1)
        runs(par, f"[{i}]\t" + r, 11.5)
        par.paragraph_format.tab_stops.add_tab_stop(Cm(1.1))


def build(pages):
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name, st.font.size = FONT, Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    s1 = doc.sections[0]
    margins(s1)
    cover(doc)
    bonafide(doc)
    s2 = doc.add_section(WD_SECTION.NEW_PAGE)
    margins(s2)
    footer_page(s2, "lowerRoman", 3)
    heading_page(doc, "ACKNOWLEDGEMENT")
    for t in C.ACK:
        para(doc, t, J, 12, indent=True, after=4)
    team_block(doc)
    page_break(doc)
    heading_page(doc, "ABSTRACT")
    for t in C.ABSTRACT:
        para(doc, t, J, 12, indent=True, line=1.5, after=8)
    para(doc, "**Keywords:** " + C.KEYWORDS, J, 12, before=6)
    page_break(doc)
    toc(doc, pages)
    page_break(doc)
    list_of(doc, "LIST OF TABLES", "TABLE", ("tab",), pages)
    page_break(doc)
    list_of(doc, "LIST OF FIGURES", "FIGURE", ("fig", "figrow"), pages)
    page_break(doc)
    heading_page(doc, "LIST OF SYMBOLS, ABBREVIATIONS AND NOMENCLATURE")
    t = doc.add_table(rows=1, cols=2)
    no_borders(t)
    cell_text(t.rows[0].cells[0], "ABBREVIATION", 11.5, True, L, 1.0, 4)
    cell_text(t.rows[0].cells[1], "DESCRIPTION", 11.5, True, L, 1.0, 4)
    for a, d in C.ABBR:
        r = t.add_row().cells
        cell_text(r[0], a, 11.5, False, L, 1.0, 3)
        cell_text(r[1], d, 11.5, False, L, 1.0, 3)
    set_widths(t, [4.0, 11.0])
    s3 = doc.add_section(WD_SECTION.NEW_PAGE)
    margins(s3)
    footer_page(s3, None, 1)
    body(doc)
    doc.core_properties.title = C.TITLE
    doc.core_properties.author = ", ".join(n for n, _ in C.TEAM)
    doc.save(DOCX)


def export_pdf():
    ps = ("$ErrorActionPreference='Stop'; $w=New-Object -ComObject Word.Application; $w.Visible=$false; $w.DisplayAlerts=0;"
          f"$d=$w.Documents.Open('{DOCX}', $false, $true); $d.ExportAsFixedFormat('{PDF}', 17); $d.Close(0); $w.Quit();")
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[:500])


def roman(n):
    out = ""
    for v, s in ((10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")):
        while n >= v:
            out += s
            n -= v
    return out


def measure():
    d = fitz.open(PDF)
    texts = [re.sub(r"\s+", " ", pg.get_text()) for pg in d]
    pages = {}
    body_start = next(i for i, t in enumerate(texts) if "CHAPTER 1 INTRODUCTION" in t and "1.1 BACKGROUND" in t)
    for key in ("ACKNOWLEDGEMENT", "ABSTRACT", "LIST OF TABLES", "LIST OF FIGURES", "LIST OF SYMBOLS, ABBREVIATIONS AND NOMENCLATURE"):
        i = next(i for i, t in enumerate(texts[:body_start]) if t.strip().startswith(key) or f" {key} " in t[:80] or t.startswith(key))
        pages[key] = roman(i + 1)
    for b in C.B + [("ref",)]:
        if b[0] == "ch":
            pat, key = f"CHAPTER {b[1]} {b[2]}", f"CH{b[1]}"
        elif b[0] == "h2":
            pat, key = b[1], b[1]
        elif b[0] in ("tab", "fig", "figrow"):
            pat, key = b[1], b[1]
        elif b[0] == "ref":
            pat, key = "CHAPTER 8 REFERENCES", "REFERENCES"
        else:
            continue
        pat = re.sub(r"\s+", " ", pat)
        i = next((i for i in range(body_start, len(texts)) if pat in texts[i]), None)
        pages[key] = (i - body_start + 1) if i is not None else "?"
    return pages, len(d), body_start


if __name__ == "__main__":
    pages = json.load(open(PAGES)) if os.path.exists(PAGES) else {}
    for it in range(3):
        build(pages)
        export_pdf()
        new, total, bs = measure()
        missing = [k for k, v in new.items() if v == "?"]
        print(f"pass {it + 1}: {total} pages (front {bs}), missing {missing}")
        if new == pages:
            break
        pages = new
        json.dump(pages, open(PAGES, "w"), indent=1)
