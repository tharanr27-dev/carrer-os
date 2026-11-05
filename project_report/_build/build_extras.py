"""Writes Source.md, API_Endpoint_Inventory.md, Screenshots_Required.md and Project_Report_Verification.md (never overwrites others)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import docmodel as M  # noqa: E402
import content1, content2, content3, content4  # noqa: E402,F401

M.resolve()
EP = json.load(open(os.path.join(HERE, "data", "endpoints.json"), encoding="utf-8"))["rows"]

# ---- source markdown ----
out = ["# Career OS - Project Report (source text)\n", "Generated from the same content model as the DOCX/PDF. Edit the content files in `_build/` or this text.\n"]
for b in M.BLOCKS:
    t = b["t"]
    if t in ("chapter", "appendix"):
        out.append(f"\n# {b['label']}: {b['title'].upper()}\n")
    elif t == "h2":
        out.append(f"\n## {b['num']} {b['title']}\n")
    elif t == "h3":
        out.append(f"\n### {b['num']} {b['title']}\n")
    elif t == "p":
        out.append(M.fill(b["text"]) + "\n")
    elif t in ("bullets", "numbered"):
        out += [(f"{i}. " if t == "numbered" else "- ") + M.fill(x) for i, x in enumerate(b["items"], 1)] + [""]
    elif t == "table":
        out.append(f"\n**Table {b['num']} {M.fill(b['caption'])}**\n")
        out.append("| " + " | ".join(b["headers"]) + " |")
        out.append("|" + "---|" * len(b["headers"]))
        out += ["| " + " | ".join(str(c).replace("\n", " ").replace("|", "/") for c in r) + " |" for r in b["rows"]] + [""]
    elif t == "figure":
        out.append(f"\n![Figure {b['num']} {M.fill(b['caption'])}]({b['folder']}/{b['file']})\n\n*Figure {b['num']} {M.fill(b['caption'])}*\n")
    elif t == "code":
        out.append(("\n**" + M.fill(b["caption"]) + "**\n" if b.get("caption") else "") + "\n```\n" + b["text"] + "\n```\n")
    elif t == "references":
        out.append("\n# REFERENCES\n")
        out += [f"{i}. {r}" for i, r in enumerate(b["items"], 1)]
open(os.path.join(ROOT, "Career_OS_Project_Report_Source.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")

# ---- complete endpoint inventory ----
lines = ["# Career OS - Complete API Endpoint Inventory (124 routes)\n",
         "Extracted from the running FastAPI application object (paths, methods and authentication dependencies are the real ones). Prefix `/api/v1` applies to all except health and metrics.\n",
         "| Method | Path | Authentication |", "|---|---|---|"]
for r in EP:
    lines.append(f"| {r[1]} | `{r[2]}` | {r[4].replace('`', '')} |")
open(os.path.join(ROOT, "API_Endpoint_Inventory.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

# ---- screenshots still required ----
req = """# Screenshots still required

Real screenshots of 19 screens were captured from the running application (folder `screenshots/`); 15 of them appear in Chapter 10.
The following screens were **not** captured and should be added by you if your college expects them:

1. Landing page (`01_landing.png` exists but is not used in the report).
2. Live Interview Studio during a WebSocket session (question and live feedback).
3. Communication Coach during a session and its report.
4. Career Discovery questionnaire and result page.
5. Learning roadmap page with tasks.
6. Resume Center showing an error state (for example a rejected file type).
7. AI Mentor setup notice (shown when no provider key is configured).
8. Mobile (phone-width) layout of the dashboard and of role training.
9. Terminal output of the final test run (`pytest`, `vitest`, `tsc`, `npm run build`).
10. Supabase project dashboard showing the tables (only after remote persistence is verified with your approval).

Note: screenshots use a fictional demo user and a temporary local database; no personal data is shown.
"""
open(os.path.join(ROOT, "Screenshots_Required.md"), "w", encoding="utf-8").write(req)

ver = """# Project report verification

## Format check against the college reference PDF (Anna University format, 7 pages)
| Item in the reference | Applied in the report | Note |
|---|---|---|
| Order: cover, bonafide, abstract, contents, list of tables, list of figures, symbols/abbreviations, chapters, appendices, references | Yes | Declaration and Acknowledgement pages are **not** in the reference order and were therefore not added; they can be inserted if your college asks |
| A4 | Yes | |
| Times New Roman 14, 1.5 spacing for general text | Yes | Tables, figure captions, code blocks and the contents list use smaller sizes (8.5-12 pt) to fit the page limit |
| Cover specimen (bold, 18/14/16 sizes) | Yes | Names, degree, branch, college, month and year are placeholders |
| Bonafide certificate (double spacing, 18/16/14 sizes, HOD and SUPERVISOR blocks) | Yes | All names, signatures and addresses are placeholders |
| Abstract: one page, double spacing | Yes | |
| Roman page numbers for front matter, Arabic for chapters | Yes | Cover carries no printed number |
| Tables captioned above, figures below, lists use the same captions | Yes | |
| References: alphabetical, numbered, single spacing, left-justified | Yes | |
| Margins | **Not specified** in the reference | Used 3.0 cm left and 2.0 cm for the other sides |
| Each chapter on a new page | **Not required** by the reference | Chapters flow on to save pages; the first chapter, the appendix and the references start new pages |

## Page count
Final PDF: **60 pages** (9 front-matter pages numbered i-ix, 51 numbered pages). DOCX and PDF come from the same file (the PDF is exported from the DOCX by Word), so content is identical. A different Word version or font set could shift the count by a page.

## Facts verified against the repository (31 October 2026)
- 124 routes, 103 tables, 78 foreign keys, 54 named indexes (extracted programmatically).
- 483 backend tests (33 files): 481 passed, 2 failed (see below). 54 frontend tests (8 files) passed. `tsc` 0 errors, ESLint 0 errors / 2 warnings, production build succeeded.
- 235 reviewed questions; 22 catalogued roles; 17 diagrams were drawn from the real structure; 15 real screenshots are used.
- Language-model checks were manual (27 October 2026); automated tests use scripted providers.

## Open items you must resolve
1. `test_resume_repository_save_analysis_persists_suggestions_after_analysis` fails because of an **uncommitted edit to `resumes/repository.py`** that was in your working tree (not made for this report). Update the test or the edit.
2. `test_password_verify_performance` is a timing benchmark that failed under full-suite load and passed alone.
3. Six ruff E402 findings in `mentor/service.py` come from the same uncommitted editing.
4. Fill all placeholders: student names, degree, branch, college, month and year, guide, HOD, designations, addresses.
5. Remote Supabase persistence was **not** verified (by design); the report says so.
6. References: four papers were checked on the web (Fuller et al.; Roediger and Karpicke; Black and Wiliam; Provos and Mazieres), others are standard citations whose details match published records; the Wei et al. page range was not confirmed, so none is given. Documentation entries have no access date; add one if your college requires it.

## Safety rules followed
No application code was changed for the report; no commit, push or deploy; `.env` values and keys were never printed; the remote database was not contacted; all screenshots and samples use a fictional user on a temporary SQLite database.
"""
open(os.path.join(ROOT, "Project_Report_Verification.md"), "w", encoding="utf-8").write(ver)
print("extras written")
