"""Renders the report model to a DOCX that follows the Anna University project-report format
(A4, Times New Roman 14 pt, 1.5 spacing, roman front matter, specimen cover and Bonafide layout)."""
import json
import os
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from PIL import Image

import docmodel as M

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "Times New Roman"
TEXT_W_CM = 16.0  # A4 21.0 - left 3.0 - right 2.0 (the format PDF does not specify margins)
PH = {  # placeholders: personal and institutional details must be supplied by the student
    "title": "CAREER OS: AI-POWERED JOB PREPARATION AND CAREER READINESS PLATFORM",
    "names": "[STUDENT NAME(S)]", "degree": "[NAME OF THE DEGREE]", "branch": "[BRANCH OF STUDY]", "college": "[NAME OF THE COLLEGE]",
    "monthyear": "[MONTH & YEAR]",
}


# ───────────────────────── low-level helpers ─────────────────────────
def set_font(run, size=14, bold=None, italic=None, name=FONT, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), name)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


_INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)")


def add_runs(par, text, size=14, bold=False, italic=False):
    for part in _INLINE.split(M.fill(text)):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = par.add_run(part[2:-2]); set_font(r, size, True, italic)
        elif part.startswith("`") and part.endswith("`"):
            r = par.add_run(part[1:-1]); set_font(r, max(size - 2, 8), bold, italic, name="Courier New")
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r = par.add_run(part[1:-1]); set_font(r, size, bold, True)
        else:
            r = par.add_run(part); set_font(r, size, bold, italic)


def fmt(par, align=WD_ALIGN_PARAGRAPH.JUSTIFY, spacing=1.5, before=0, after=6, keep_next=False, keep_lines=False, left=None, first=None, page_break=False):
    pf = par.paragraph_format
    par.alignment = align
    pf.line_spacing = spacing
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.keep_with_next = keep_next
    pf.keep_together = keep_lines
    pf.page_break_before = page_break
    pf.widow_control = True
    if left is not None:
        pf.left_indent = Cm(left)
    if first is not None:
        pf.first_line_indent = Cm(first)
    return par


def para(doc, text, size=14, bold=False, italic=False, **kw):
    par = doc.add_paragraph()
    add_runs(par, text, size, bold, italic)
    return fmt(par, **kw)


def shade(cell, color):
    tcpr = cell._element.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), color)
    tcpr.append(sh)


def cell_margins(table, top=40, bottom=40, left=70, right=70):
    tblpr = table._element.tblPr
    m = OxmlElement("w:tblCellMar")
    for k, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        e = OxmlElement(f"w:{k}"); e.set(qn("w:w"), str(v)); e.set(qn("w:type"), "dxa"); m.append(e)
    tblpr.append(m)


def row_props(row, header=False):
    trpr = row._tr.get_or_add_trPr()
    cs = OxmlElement("w:cantSplit"); trpr.append(cs)
    if header:
        th = OxmlElement("w:tblHeader"); trpr.append(th)


def borders(table, sz=6):
    tblpr = table._element.tblPr
    b = OxmlElement("w:tblBorders")
    for k in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{k}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000")
        b.append(e)
    tblpr.append(b)


def fixed_layout(table):
    tblpr = table._element.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblpr.append(lay)


def page_field(par, size=12):
    for kind, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        r = par.add_run()
        set_font(r, size)
        if kind:
            f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), kind); r._r.append(f)
        else:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; r._r.append(it)


def set_pgnum(section, fmt_="decimal", start=1):
    sp = section._sectPr
    for old in sp.findall(qn("w:pgNumType")):
        sp.remove(old)
    pg = OxmlElement("w:pgNumType"); pg.set(qn("w:fmt"), fmt_); pg.set(qn("w:start"), str(start)); sp.append(pg)


def footer_number(section, show_first=True):
    section.footer.is_linked_to_previous = False
    fp = section.footer.paragraphs[0]
    for r in list(fp.runs):
        r._r.getparent().remove(r._r)
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    page_field(fp)
    if not show_first:
        section.different_first_page_header_footer = True
        section.first_page_footer.is_linked_to_previous = False
        section.first_page_footer.paragraphs[0].text = ""


# ───────────────────────── document parts ─────────────────────────
def new_document():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin = Cm(3.0), Cm(2.0), Cm(2.0), Cm(2.0)
    sec.footer_distance = Cm(0.9)
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(14)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    return doc


def cover(doc):
    c = WD_ALIGN_PARAGRAPH.CENTER

    def line(text, size, italic=False, before=0, after=0, spacing=1.0):
        par = doc.add_paragraph()
        add_runs(par, text, size, bold=True, italic=italic)
        fmt(par, align=c, spacing=spacing, before=before, after=after)

    line(PH["title"], 18, spacing=1.5, before=36, after=40)
    line("A PROJECT REPORT", 14, after=30)
    line("Submitted by", 14, italic=True, after=14)
    line(PH["names"], 16, after=30)
    line("in partial fulfillment for the award of the degree", 14, italic=True, spacing=1.5, after=4)
    line("of", 14, italic=True, after=10)
    line(PH["degree"], 16, after=8)
    line("IN", 14, after=8)
    line(PH["branch"], 14, after=40)
    line(PH["college"], 14, after=40)
    line("ANNA UNIVERSITY : CHENNAI 600 025", 16, spacing=1.5, after=30)
    line(PH["monthyear"], 14)


def bonafide(doc):
    c = WD_ALIGN_PARAGRAPH.CENTER
    par = doc.add_paragraph(); add_runs(par, "ANNA UNIVERSITY : CHENNAI 600 025", 18, True)
    fmt(par, align=c, spacing=1.5, before=0, after=14, page_break=True)
    par = doc.add_paragraph(); add_runs(par, "BONAFIDE CERTIFICATE", 16, True)
    fmt(par, align=c, spacing=1.5, after=22)
    par = doc.add_paragraph()
    add_runs(par, f"Certified that this project report “{PH['title']}” is the bonafide work of “{PH['names']}” who carried out the project work under my supervision.", 14)
    fmt(par, align=WD_ALIGN_PARAGRAPH.JUSTIFY, spacing=2.0, after=36, first=1.0)
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    fixed_layout(t)
    left = ["<<SIGNATURE>>", "", "<<NAME OF THE HEAD OF THE DEPARTMENT>>", "HEAD OF THE DEPARTMENT", "<<Department>>", "<<Full address of the Department and College>>"]
    right = ["<<SIGNATURE>>", "", "<<NAME OF THE SUPERVISOR>>", "SUPERVISOR", "<<Academic Designation>>", "<<Department>>", "<<Full address of the Department and College>>"]
    for cell, lines in zip(t.rows[0].cells, (left, right)):
        cell.width = Cm(7.5)
        cell.paragraphs[0].text = ""
        for i, ln in enumerate(lines):
            par = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
            add_runs(par, ln, 12, bold=ln in ("HEAD OF THE DEPARTMENT", "SUPERVISOR"))
            fmt(par, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.15, after=4)


def abstract(doc, text, keywords):
    par = doc.add_paragraph(); add_runs(par, "ABSTRACT", 14, True)
    fmt(par, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=2.0, after=6, page_break=True)
    par = doc.add_paragraph(); add_runs(par, text, 14)
    fmt(par, spacing=2.0, after=6, first=1.0)
    par = doc.add_paragraph(); add_runs(par, "**Keywords:** " + keywords, 14)
    fmt(par, spacing=2.0, after=0)


def front_heading(doc, text, page_break=True):
    par = doc.add_paragraph(); add_runs(par, text, 14, True)
    fmt(par, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.5, after=10, page_break=page_break, keep_next=True)


def toc_line(doc, left_txt, title, page, level=1, size=12, bold=False):
    par = doc.add_paragraph()
    pf = par.paragraph_format
    ts = pf.tab_stops
    if level == 1:
        ts.add_tab_stop(Cm(3.2))
        hang = 3.2
        text = f"{left_txt}	{title}	{page}"
    else:
        ts.add_tab_stop(Cm(3.2)); ts.add_tab_stop(Cm(4.3))
        hang = 4.3
        text = f"	{left_txt}	{title}	{page}"
    ts.add_tab_stop(Cm(TEXT_W_CM - 0.1), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    run = par.add_run(text)
    set_font(run, size, bold)
    fmt(par, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.5, after=0, keep_lines=True)
    pf.left_indent = Cm(hang); pf.first_line_indent = Cm(-hang); pf.right_indent = Cm(1.3)


def toc(doc, outline, pages):
    front_heading(doc, "TABLE OF CONTENTS")
    par = doc.add_paragraph()
    ts = par.paragraph_format.tab_stops
    ts.add_tab_stop(Cm(3.2)); ts.add_tab_stop(Cm(TEXT_W_CM - 0.1), WD_TAB_ALIGNMENT.RIGHT)
    r = par.add_run("CHAPTER NO.\tTITLE\tPAGE NO."); set_font(r, 12, True)
    fmt(par, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.5, after=2)
    for name in ("ABSTRACT", "LIST OF TABLES", "LIST OF FIGURES", "LIST OF SYMBOLS, ABBREVIATIONS AND NOMENCLATURE"):
        toc_line(doc, "", name, pages.get("front:" + name, "0"), 1, 11)
    for o in outline:
        pg = pages.get("outline:" + o["num"] + "|" + o["title"], "0")
        if o["level"] == 1:
            lab = o["num"] if not o.get("appendix") else ""
            title = o["title"] if not o.get("appendix") else f"{o['num']}  {o['title']}"
            if o["title"] == "REFERENCES":
                lab = ""
            toc_line(doc, lab, title, pg, 1, 11, True)
        else:
            toc_line(doc, o["num"], o["title"].title().replace("And", "and").replace("Of", "of").replace("Api", "API") if False else o["title"], pg, 2, 11)


def list_of(doc, heading, items, pages, kind):
    front_heading(doc, heading)
    par = doc.add_paragraph()
    ts = par.paragraph_format.tab_stops
    ts.add_tab_stop(Cm(2.4)); ts.add_tab_stop(Cm(TEXT_W_CM - 0.1), WD_TAB_ALIGNMENT.RIGHT)
    r = par.add_run(("TABLE NO.\tTITLE OF THE TABLE" if kind == "tab" else "FIGURE NO.\tTITLE OF THE FIGURE") + "\tPAGE NO."); set_font(r, 12, True)
    fmt(par, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.5, after=2)
    for b in items:
        par = doc.add_paragraph()
        pf = par.paragraph_format
        pf.tab_stops.add_tab_stop(Cm(2.4))
        pf.tab_stops.add_tab_stop(Cm(TEXT_W_CM - 0.1), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        pf.left_indent = Cm(2.4); pf.first_line_indent = Cm(-2.4)
        pg = pages.get(f"{kind}:{b['num']}", "0")
        r = par.add_run(f"{b['num']}\t{M.fill(b['caption'])}\t{pg}"); set_font(r, 12)
        fmt(par, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.5, after=0, keep_lines=True)
        pf.left_indent = Cm(2.4); pf.first_line_indent = Cm(-2.4); pf.right_indent = Cm(1.3)


def abbreviations(doc, rows):
    front_heading(doc, "LIST OF SYMBOLS, ABBREVIATIONS AND NOMENCLATURE")
    para(doc, "No mathematical symbols are used in this report other than those defined where they appear. Standard abbreviations are listed below.", 12, spacing=1.5, after=6)
    t = doc.add_table(rows=1, cols=2)
    borders(t); fixed_layout(t); cell_margins(t)
    for c, txt in zip(t.rows[0].cells, ("Abbreviation", "Expansion")):
        c.text = ""; add_runs(c.paragraphs[0], txt, 12, True); shade(c, "D9D9D9"); fmt(c.paragraphs[0], align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.15, after=0)
    row_props(t.rows[0], True)
    for a, e in rows:
        r = t.add_row(); row_props(r)
        for c, txt in zip(r.cells, (a, e)):
            c.text = ""; add_runs(c.paragraphs[0], txt, 12); fmt(c.paragraphs[0], align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.15, after=0)
    for r in t.rows:
        r.cells[0].width = Cm(3.6); r.cells[1].width = Cm(TEXT_W_CM - 3.6)


# ───────────────────────── body blocks ─────────────────────────
def heading_chapter(doc, b):
    new_page = b["t"] == "appendix" or b.get("num") == "1"
    par = doc.add_paragraph(); add_runs(par, b["label"], 16, True)
    fmt(par, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.5, before=0 if new_page else 14, after=0, page_break=new_page, keep_next=True)
    par = doc.add_paragraph(); add_runs(par, b["title"].upper(), 16, True)
    fmt(par, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.5, after=8, keep_next=True)


def tiny_spacer(doc, half_points=8):
    """A thin empty paragraph (paragraph mark of 4 pt) used to separate a table from the next text."""
    sp = doc.add_paragraph()
    fmt(sp, spacing=1.0, after=0)
    ppr = sp._p.get_or_add_pPr()
    rpr = OxmlElement("w:rPr")
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), str(half_points)); rpr.append(sz)
    ppr.append(rpr)


def render_table(doc, b):
    cap = doc.add_paragraph(); add_runs(cap, f"Table {b['num']}  {M.fill(b['caption'])}", 12, True)
    fmt(cap, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.15, before=8, after=4, keep_next=True)
    ncol = len(b["headers"])
    t = doc.add_table(rows=1, cols=ncol)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    borders(t); fixed_layout(t); cell_margins(t)
    w = b["widths"] or [1] * ncol
    tot = float(sum(w))
    widths = [Cm(TEXT_W_CM * x / tot) for x in w]
    fs = max(8.5, b["fs"] - 1)
    for i, h in enumerate(b["headers"]):
        c = t.rows[0].cells[i]; c.text = ""
        add_runs(c.paragraphs[0], h, fs, True); shade(c, "D9D9D9")
        fmt(c.paragraphs[0], align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.0, after=0)
    row_props(t.rows[0], True)
    for row in b["rows"]:
        r = t.add_row(); row_props(r)
        for i, txt in enumerate(row):
            c = r.cells[i]; c.text = ""
            parts = str(txt).split("\n")
            for j, ptxt in enumerate(parts):
                par = c.paragraphs[0] if j == 0 else c.add_paragraph()
                add_runs(par, ptxt, fs)
                fmt(par, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.0, after=0)
    for r in t.rows:
        for i, c in enumerate(r.cells):
            c.width = widths[i]
    tiny_spacer(doc)


def render_figure(doc, b):
    path = os.path.join(ROOT, b["folder"], b["file"])
    im = Image.open(path)
    wpx, hpx = im.size
    width = b["width"]
    if b.get('tall'):
        width, max_h = min(width, 5.6), 7.0
    else:
        width, max_h = min(width, 4.1 if b['folder'] == 'screenshots' else 4.6), 4.9
    if width * hpx / wpx > max_h:
        width = max_h * wpx / hpx
    par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.add_run().add_picture(path, width=Inches(width))
    fmt(par, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.0, before=6, after=3, keep_next=True)
    cap = doc.add_paragraph(); add_runs(cap, f"Figure {b['num']}  {M.fill(b['caption'])}", 12, True)
    fmt(cap, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.15, after=10)


def render_code(doc, b):
    if b.get("caption"):
        cap = doc.add_paragraph(); add_runs(cap, M.fill(b["caption"]), 12, True)
        fmt(cap, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.15, before=6, after=3, keep_next=True)
    t = doc.add_table(rows=1, cols=1)
    borders(t, 4); fixed_layout(t); cell_margins(t, 60, 60, 110, 110)
    c = t.rows[0].cells[0]; c.width = Cm(TEXT_W_CM); shade(c, "F2F2F2")
    c.text = ""
    for i, ln in enumerate(b["text"].split("\n")):
        par = c.paragraphs[0] if i == 0 else c.add_paragraph()
        r = par.add_run(ln if ln else " "); set_font(r, 9, name="Courier New")
        fmt(par, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.0, after=0)
    tiny_spacer(doc)


def render_list(doc, items, numbered):
    for i, it in enumerate(items, 1):
        par = doc.add_paragraph()
        marker = f"{i}." if numbered else "•"
        r = par.add_run(marker + "\t"); set_font(r, 14)
        add_runs(par, it, 14)
        par.paragraph_format.tab_stops.add_tab_stop(Cm(1.3))
        fmt(par, align=WD_ALIGN_PARAGRAPH.JUSTIFY, spacing=1.5, after=3, left=1.3, first=-0.8)


def render_references(doc, b):
    par = doc.add_paragraph(); add_runs(par, "REFERENCES", 14, True)
    fmt(par, align=WD_ALIGN_PARAGRAPH.CENTER, spacing=1.5, after=0, page_break=True, keep_next=True)
    for _ in range(3):
        sp = doc.add_paragraph(); fmt(sp, spacing=1.0, after=6, keep_next=True)
    for i, ref in enumerate(b["items"], 1):
        par = doc.add_paragraph()
        r = par.add_run(f"{i}.\t"); set_font(r, 14)
        add_runs(par, ref, 14)
        par.paragraph_format.tab_stops.add_tab_stop(Cm(1.0))
        fmt(par, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.0, after=4, left=1.0, first=-1.0)


def render_blocks(doc):
    for b in M.BLOCKS:
        t = b["t"]
        if t in ("chapter", "appendix"):
            heading_chapter(doc, b)
        elif t == "h2":
            par = doc.add_paragraph(); add_runs(par, f"{b['num']}  {b['title'].upper()}", 14, True)
            fmt(par, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.5, before=6, after=2, keep_next=True)
        elif t == "h3":
            par = doc.add_paragraph(); add_runs(par, f"{b['num']}  {b['title']}", 14, True)
            fmt(par, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.5, before=6, after=3, keep_next=True)
        elif t == "p":
            para(doc, b["text"], 14, spacing=1.5, after=3, first=1.0)
        elif t == "bullets":
            render_list(doc, b["items"], False)
        elif t == "numbered":
            render_list(doc, b["items"], True)
        elif t == "table":
            render_table(doc, b)
        elif t == "figure":
            render_figure(doc, b)
        elif t == "code":
            render_code(doc, b)
        elif t == "references":
            render_references(doc, b)


def build(out_path, pages=None, front=None):
    pages = pages or {}
    outline, tables, figures = M.resolve()
    doc = new_document()
    footer_number(doc.sections[0], show_first=False)
    set_pgnum(doc.sections[0], "lowerRoman", 1)
    cover(doc)
    bonafide(doc)
    abstract(doc, front["abstract"], front["keywords"])
    toc(doc, outline, pages)
    list_of(doc, "LIST OF TABLES", tables, pages, "tab")
    list_of(doc, "LIST OF FIGURES", figures, pages, "fig")
    abbreviations(doc, front["abbreviations"])
    body = doc.add_section(WD_SECTION.NEW_PAGE)
    body.different_first_page_header_footer = False
    footer_number(body, show_first=True)
    set_pgnum(body, "decimal", 1)
    render_blocks(doc)
    doc.core_properties.title = "Career OS - Project Report"
    doc.core_properties.author = "[STUDENT NAME(S)]"
    doc.save(out_path)
    return outline, tables, figures
