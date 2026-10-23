"""Rule-based résumé analysis. Every score is a documented formula over measurable features of the text.

These are NOT AI judgements and NOT what a particular company's ATS would output. They measure how complete and
machine-readable the résumé is, and how it reads (action verbs, measurable results, mechanical slips).

  ats_readiness (0-100)  = 35 * min(1, words / 150)            readable text was extracted
                         + 25 * essential_sections_found / 4   education, experience-or-projects, skills, contact
                         + 20 * contact_completeness           email 10, phone 5, profile link 5
                         + 10 * has_skills_section
                         + 10 * (symbol noise below 8% of characters)
  quality (0-100)        = 40 * action_verb_ratio + 30 * min(1, quantified_lines / 5)
                         + 15 * (>= 6 skills found) + 15 * (1 - weak_phrase_penalty)
  writing_mechanics      = 100 - 10 * mechanical_slips (repeated words, lowercase 'I', lowercase sentence starts)
"""

import re
from typing import Any, Dict, List, Optional

from app.core.text_analysis import (
    ACTION_VERBS,
    WEAK_PHRASES,
    count_phrase,
    extract_skills,
    mechanical_issues,
    role_skills,
    words,
)
from app.modules.resumes.schemas import AIResumeAnalysis, AIResumeSuggestion

METHOD = "rule_based_v1"

_SECTION_PATTERNS = {
    "summary": r"(?:professional\s+)?(?:summary|objective|profile|about me)",
    "education": r"education(?:al)?(?:\s+(?:background|qualifications?))?|academics?|qualifications?",
    "experience": r"(?:work\s+|professional\s+|relevant\s+)?experience|employment(?:\s+history)?|internships?|work history",
    "projects": r"(?:academic\s+|personal\s+|key\s+)?projects?",
    "skills": r"(?:technical\s+|key\s+|core\s+)?(?:skills|competenc(?:ies|y)|technologies|tech stack)",
    "certifications": r"certifications?|courses?|licen[sc]es?",
    "achievements": r"achievements?|awards?|honou?rs|accomplishments|extracurriculars?",
}
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?:\+?\d[\d\s().-]{8,}\d)")
_LINK = re.compile(r"(?:linkedin\.com|github\.com|gitlab\.com|portfolio|behance\.net)", re.IGNORECASE)
_QUANT = re.compile(r"\d+(?:\.\d+)?\s?(?:%|\+|x\b|k\b|m\b|lakh|crore|users|students|clients|hours|ms|seconds)|[$₹€£]\s?\d|\b\d{2,}\b")
_BULLET = re.compile(r"^\s*(?:[•●▪■◦\-–—*]|\d+[.)])\s+")


def _lines(text: str) -> List[str]:
    return [l.strip() for l in text.split("\n") if l.strip()]


def detect_sections(text: str) -> List[str]:
    found = []
    for name, pat in _SECTION_PATTERNS.items():
        rx = re.compile(rf"^\s*(?:{pat})\s*[:\-–]?\s*$", re.IGNORECASE | re.MULTILINE)
        if rx.search(text):
            found.append(name)
    return found


def analyze_text(text: str, target_role: Optional[str] = None, extraction_warnings: Optional[List[str]] = None) -> AIResumeAnalysis:
    warnings = list(extraction_warnings or [])
    wc = len(words(text))
    lines = _lines(text)
    sections = detect_sections(text)
    email, phone, link = bool(_EMAIL.search(text)), bool(_PHONE.search(text)), bool(_LINK.search(text))
    skills = extract_skills(text)

    bullets = [_BULLET.sub("", l) for l in lines if _BULLET.match(l)]
    content_lines = bullets or [l for l in lines if len(words(l)) >= 5]
    first_words = [(words(l) or [""])[0].lower() for l in content_lines]
    verb_hits = sum(1 for w in first_words if w in ACTION_VERBS)
    verb_ratio = verb_hits / len(first_words) if first_words else 0.0
    quant_lines = sum(1 for l in content_lines if _QUANT.search(l))
    weak = {p: alt for p, alt in WEAK_PHRASES.items() if count_phrase(text, p)}
    weak_penalty = min(1.0, sum(count_phrase(text, p) for p in weak) / 5)
    symbol_noise = (sum(1 for ch in text if not (ch.isalnum() or ch.isspace() or ch in ".,;:()-–—/@+#&%'\"•●▪|_")) / len(text)) if text else 1.0

    essential = [
        "education" in sections,
        ("experience" in sections) or ("projects" in sections),
        "skills" in sections,
        email or phone,
    ]
    contact = (10 if email else 0) + (5 if phone else 0) + (5 if link else 0)
    ats = (
        35 * min(1.0, wc / 150)
        + 25 * (sum(essential) / 4)
        + contact
        + (10 if "skills" in sections else 0)
        + (10 if symbol_noise < 0.08 else 0)
    ) if wc else 0.0
    quality = (
        40 * verb_ratio + 30 * min(1.0, quant_lines / 5) + (15 if len(skills) >= 6 else 15 * len(skills) / 6) + 15 * (1 - weak_penalty)
    ) if wc else 0.0
    # Only prose is checked for slips: header lines (emails, links, phone numbers) and skill lists start in lower case
    # or with symbols by design and would be false positives.
    prose = "\n".join(l for l in content_lines if len(words(l)) >= 6 and l[0].isalpha())
    slips = [i for i in mechanical_issues(prose) if i["category"] in ("Repeated word", "Capitalisation")]
    mechanics = max(0.0, 100 - 10 * len(slips)) if wc else 0.0

    expected, role_known = role_skills(target_role)
    have = {s.lower() for s in skills}
    missing = [s for s in expected if s.lower() not in have]

    suggestions: List[AIResumeSuggestion] = []

    def add(cat: str, text_: str, impact: str) -> None:
        suggestions.append(AIResumeSuggestion(category=cat, suggestion_text=text_, impact=impact))

    if not wc:
        add("Readability", "No readable text was extracted from this file. Upload a text-based PDF or a DOCX (not a scanned image) so recruiters' ATS software can read it.", "HIGH")
    elif wc < 20:
        add("Readability", f"Only {wc} words were found, which is too little to analyse. Add your education, skills, projects and experience.", "HIGH")
    else:
        if not email:
            add("Contact details", "Add a professional email address at the top of the résumé.", "HIGH")
        if not phone:
            add("Contact details", "Add a phone number so recruiters can reach you.", "MEDIUM")
        if not link:
            add("Contact details", "Add a LinkedIn or GitHub link to show your work.", "LOW")
        names = {"education": "Education", "skills": "Skills", "experience": "Experience (or Internships)", "projects": "Projects"}
        for key in ("education", "skills"):
            if key not in sections:
                add("Structure", f"Add a clearly titled '{names[key]}' section on its own line.", "HIGH")
        if "experience" not in sections and "projects" not in sections:
            add("Structure", "Add an 'Experience', 'Internships' or 'Projects' section so your practical work is easy to find.", "HIGH")
        if quant_lines < 2:
            add("Measurable results", "Few lines contain numbers. Where true, add measurable results (for example users served, percentage improved, time saved).", "HIGH")
        if verb_ratio < 0.5 and first_words:
            add("Action verbs", f"Only {int(verb_ratio * 100)}% of your lines start with an action verb. Start bullets with verbs such as Built, Designed, Implemented, Reduced.", "MEDIUM")
        for phrase, alt in list(weak.items())[:3]:
            add("Wording", f"Replace '{phrase}' with a stronger, specific verb such as: {alt}.", "MEDIUM")
        if wc < 150:
            add("Length", f"The résumé has only {wc} words. Add detail about projects, tools used and your role.", "MEDIUM")
        elif wc > 1100:
            add("Length", f"The résumé has {wc} words. Aim for one or two pages by cutting older or less relevant detail.", "LOW")
        if slips:
            add("Writing", f"{len(slips)} small writing slip(s) were detected (for example: {slips[0]['category'].lower()}: '{slips[0]['original'][:30]}'). Proofread carefully.", "LOW")
        if missing and role_known:
            add("Keywords", f"Keywords commonly expected for {target_role} that do not appear: {', '.join(missing[:6])}. Add them only if you genuinely have that experience.", "MEDIUM")
        elif not role_known:
            add("Keywords", "Set your target role in Interview Prep to see role-specific keyword suggestions.", "LOW")

    keyword_analysis: Dict[str, Any] = {
        "method": METHOD,
        "disclaimer": "Rule-based measurements of the text, not an AI judgement and not the output of any company's ATS.",
        "found": skills,
        "missing": missing if role_known else [],
        "target_role": target_role if role_known else None,
        "word_count": wc,
        "sections_found": sections,
        "contact": {"email": email, "phone": phone, "profile_link": link},
        "quantified_lines": quant_lines,
        "action_verb_ratio": round(verb_ratio, 2),
        "weak_phrases": list(weak),
        "warnings": warnings,
    }
    return AIResumeAnalysis(
        ats_score=round(ats, 1),
        grammar_score=round(mechanics, 1),
        quality_score=round(quality, 1),
        keyword_analysis=keyword_analysis,
        suggestions=suggestions,
        extracted_skills=skills,
    )
