import logging
import re
from collections import Counter
from typing import Dict, List

from app.core.text_analysis import extract_skills, role_skills
from app.modules.career_discovery.schemas import AICareerAnalysis, AICareerMatch

logger = logging.getLogger("careeros")

METHOD = "answer_tally_v1"

# field -> (job title, answer keywords, skills that point to it)
FIELDS: Dict[str, Dict] = {
    "Software Engineering": {
        "title": "Software Engineer", "role": "Software Engineer",
        "words": ["build", "product", "develop", "code", "coding", "backend", "api", "app", "software", "program"],
        "skills": ["Python", "Java", "C++", "C#", "Go", "FastAPI", "Django", "Flask", "Spring Boot", "Node.js", "REST APIs", "Data Structures", "Algorithms", "OOP", "Git"],
    },
    "Data & Analytics": {
        "title": "Data Analyst", "role": "Data Analyst",
        "words": ["data", "analys", "statistic", "insight", "model", "machine learning", "dashboard", "research"],
        "skills": ["Pandas", "NumPy", "SQL", "Excel", "Power BI", "Tableau", "Statistics", "Data Analysis", "Machine Learning", "scikit-learn", "R", "TensorFlow", "PyTorch"],
    },
    "Frontend & Design": {
        "title": "Frontend Developer", "role": "Frontend Developer",
        "words": ["design", "experience", "interface", "visual", "frontend", "user", "creative", "ui", "ux"],
        "skills": ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Next.js", "Angular", "Vue", "Tailwind CSS", "Figma"],
    },
    "DevOps & Cloud": {
        "title": "DevOps Engineer", "role": "DevOps Engineer",
        "words": ["deploy", "cloud", "infrastructure", "pipeline", "automation", "server", "reliab"],
        "skills": ["Docker", "Kubernetes", "AWS", "Azure", "GCP", "Linux", "CI/CD", "Terraform", "Jenkins", "Bash", "Nginx"],
    },
    "Team Leadership & Product": {
        "title": "Product / Team Lead", "role": "Software Engineer",
        "words": ["lead", "leading", "team", "manage", "mentor", "plan", "coordinate", "organis", "organiz"],
        "skills": ["Agile", "Scrum", "Jira"],
    },
}
PREFERENCE_QUESTIONS = ("prefer to work", "work best", "environment")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower())


class CareerDiscoveryAIEngine:
    """Transparent tally of the student's OWN stated answers. Not AI and not a psychometric test.

    Each answer adds evidence to a field: +2 for every skill from the field's list mentioned, +1 for every keyword.
    Match percentages are shares of the total evidence, so they describe what the student SAID, not their ability.
    """

    async def generate_career_report(self, raw_answers: List[Dict]) -> AICareerAnalysis:
        texts = [a.get("text") or "" for a in raw_answers if (a.get("text") or "").strip()]
        points: Counter = Counter()
        reasons: Dict[str, List[str]] = {f: [] for f in FIELDS}
        mentioned: List[str] = []
        for t in texts:
            low = _norm(t)
            skills = extract_skills(t)
            mentioned += skills
            for field, spec in FIELDS.items():
                for sk in skills:
                    if sk in spec["skills"]:
                        points[field] += 2
                        reasons[field].append(sk)
                for w in spec["words"]:
                    if re.search(rf"\b{re.escape(w)}", low):
                        points[field] += 1
                        reasons[field].append(w)

        total = sum(points.values())
        ranked = [(f, p) for f, p in points.most_common() if p > 0]
        evidence_items = total
        confidence = round(100 * min(1.0, evidence_items / 8), 1)  # more evidence -> more reliable, capped
        matches: List[AICareerMatch] = []
        for field, p in ranked[:3]:
            matches.append(AICareerMatch(
                job_title=FIELDS[field]["title"], suitability_score=round(100 * p / total, 1), confidence_score=confidence,
                reasoning=f"Your answers mention: {', '.join(dict.fromkeys(reasons[field]))}. "
                          "The percentage is this field's share of the interests you stated, not a prediction of success.",
            ))

        top_field = ranked[0][0] if ranked else None
        expected, _ = role_skills(FIELDS[top_field]["role"]) if top_field else ([], False)
        have = {s.lower() for s in mentioned}
        not_mentioned = [s for s in expected if s.lower() not in have] if evidence_items >= 3 else []
        choice_answers = [t for t in texts if len(t) < 60]

        return AICareerAnalysis(
            personality_analysis={
                "method": METHOD,
                "stated_preferences": choice_answers[:6],
                "note": "These are your own short answers shown back to you. This is not a personality test.",
            },
            interest_analysis={
                "method": METHOD,
                "fields": [f for f, _ in ranked],
                "share_of_stated_interests_pct": {f: round(100 * p / total, 1) for f, p in ranked},
                "note": "Based only on the words and skills in your answers." if ranked else "Your answers did not mention enough skills or interests to rank any field. Add more detail and retake the assessment.",
            },
            skill_gaps={
                "method": METHOD,
                "based_on": FIELDS[top_field]["title"] if top_field else None,
                "missing": not_mentioned,
                "note": "Skills typical for that role that you did not mention. You may have them: this is a prompt to reflect, not a finding.",
            },
            career_timeline={
                "note": "A career timeline cannot be predicted from a short assessment. Use the Learning roadmap for a concrete, role-based study plan.",
            },
            recommended_matches=matches,
        )
