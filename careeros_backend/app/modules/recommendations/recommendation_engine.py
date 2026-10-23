import logging
from typing import List

from app.modules.recommendations.schemas import AIRecommendationItem, AIRecommendationList

logger = logging.getLogger("careeros")

_DIFFICULTY = {"easy": "EASY", "medium": "MEDIUM", "hard": "HARD"}
# Below these report scores (0-100) an interview / communication recommendation is raised.
_LOW_REPORT_SCORE = 60.0


class RecommendationEngine:
    """Rule-based recommendations built ONLY from the student's own saved data.

    The class keeps its historical name and interface, but nothing here is AI-generated: each rule checks a
    measurable fact about the student (profile completeness, the latest résumé analysis, saved practice
    attempts, report scores, whether a roadmap exists) and says exactly which fact triggered it.

    `confidence_score` is how directly the fact was measured (0.9 = read straight from saved data,
    0.6 = "nothing saved yet" prompts). `estimated_impact` is a fixed relative priority for each kind of
    action, NOT a prediction of career outcomes. Ranking is done separately by the RankingEngine.
    """

    async def generate_candidates(self, context: dict) -> AIRecommendationList:
        logger.info("Building rule-based recommendations", extra={"user_id": context.get("user_id")})
        items: List[AIRecommendationItem] = []

        def add(category, title, description, reason, confidence, impact, difficulty, skills, sources):
            items.append(AIRecommendationItem(
                category=category, title=title, description=description, reason=reason,
                confidence_score=confidence, estimated_impact=impact, difficulty=difficulty,
                related_skills=skills, source_modules=sources,
            ))

        profile = context.get("profile") or {}
        completion = profile.get("completion")
        if not profile or (completion is not None and completion < 70):
            add("RESUME", "Complete your profile",
                "Add your education, skills, projects and a headline. Recruiters and the matching tools use these details.",
                f"Your profile is {int(completion or 0)}% complete." if profile else "No profile details are saved yet.",
                0.9, 0.5, "EASY", [], ["Profile"])

        ats = context.get("ats_score")
        if ats is None:
            add("RESUME", "Upload your résumé for analysis",
                "Upload a text-based PDF or DOCX. You will get a rule-based review of its structure, keywords and wording.",
                "You have no analysed résumé yet.", 0.6, 0.8, "EASY", [], ["Resume"])
        else:
            method = context.get("resume_method")
            suggestions = context.get("resume_suggestions") or []
            if ats < 75:
                add("RESUME", "Improve your résumé's readiness",
                    " ".join(f"{i + 1}. {s['text']}" for i, s in enumerate(suggestions))
                    or "Open the résumé analysis in the Resume Center for the details.",
                    f"Your latest résumé analysis scored {ats:.0f}/100 for readiness (rule-based measurement"
                    + ("" if method else "; this result came from an older, simulated analysis, so please re-upload") + ").",
                    0.9 if method else 0.4, 0.8, "EASY", [], ["Resume"])
            missing = [m for m in (context.get("resume_weaknesses") or []) if isinstance(m, str)][:6]
            if missing and context.get("target_role"):
                add("SKILL", f"Show or build skills for {context['target_role']}",
                    f"These commonly expected skills were not found on your résumé: {', '.join(missing)}. Add the ones you genuinely have; "
                    "learn and practise the rest.",
                    f"Compared your résumé keywords with typical skills for {context['target_role']}.",
                    0.9 if method else 0.4, 0.7, "MEDIUM", missing, ["Resume", "Interview Prep"])

        training = context.get("training") or {}
        for rec in (training.get("recommendations") or [])[:3]:
            act = rec.get("action") or {}
            if act.get("type") == "mock":
                add("INTERVIEW", rec["title"], "Run a timed multi-round simulation to test your rounds together.",
                    rec["reason"], 0.9, 0.7, "MEDIUM", [], ["Interview Prep"])
            elif act.get("round"):
                weak = rec.get("rule") == "weak_topic"
                add("PRACTICE", rec["title"],
                    f"Open Interview Prep → {act['round']} and practise{(' ' + act['topic']) if act.get('topic') else ''} questions"
                    f"{' at ' + act['difficulty'] + ' difficulty' if act.get('difficulty') else ''}.",
                    rec["reason"], 0.9 if weak else 0.6, 0.85 if weak else 0.6,
                    _DIFFICULTY.get(act.get("difficulty") or "", "MEDIUM"),
                    [act["topic"]] if act.get("topic") else [], ["Interview Prep"])

        interview = context.get("interview_scores") or {}
        if interview.get("overall") is not None and interview["overall"] < _LOW_REPORT_SCORE:
            add("INTERVIEW", "Repeat a mock interview and focus on structured answers",
                "Your last interview report was below 60/100. Re-attempt with the STAR structure (situation, task, action, result).",
                f"Your latest interview report scored {interview['overall']:.0f}/100 (rule-based estimate).",
                0.9, 0.75, "MEDIUM", [], ["Interview"])
        comm = context.get("communication_scores") or {}
        if comm.get("overall") is not None and comm["overall"] < _LOW_REPORT_SCORE / 10:
            add("COMMUNICATION", "Work on clarity and filler words",
                "Practise shorter sentences and cut filler words such as 'basically' and 'like' in the Communication Coach.",
                f"Your latest communication report scored {comm['overall']:.1f}/10 (text-based measurement).",
                0.9, 0.6, "EASY", [], ["Communication"])

        if not context.get("roadmap_status"):
            add("COURSE", "Generate your learning roadmap",
                "Pick a target role and get a study plan built from the Interview Prep topics for that role.",
                "You have no active learning roadmap.", 0.6, 0.6, "EASY", [], ["Learning"])
        if not context.get("has_career_report"):
            add("SKILL", "Take the career discovery assessment",
                "Answer a few questions to see which tech fields match the interests you state.",
                "You have not completed the career assessment.", 0.6, 0.4, "EASY", [], ["Career Discovery"])

        if not items:
            add("INTERVIEW", "Take a full mock interview",
                "Everything we track is on track. A timed mock interview is the best next test.",
                "No weaknesses were detected in your saved data.", 0.6, 0.5, "MEDIUM", [], ["Interview Prep"])
        return AIRecommendationList(recommendations=items[:12])
