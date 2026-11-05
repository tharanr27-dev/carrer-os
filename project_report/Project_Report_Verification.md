# Project report verification

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
