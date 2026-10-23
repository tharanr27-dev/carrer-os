import logging
from typing import List, Optional

from app.modules.resumes.analysis import analyze_text
from app.modules.resumes.schemas import AIResumeAnalysis

logger = logging.getLogger("careeros")


class AIResumeAnalyzer:
    """Résumé analysis facade.

    Despite the historical name this is NOT an AI model: it runs the local, rule-based analysis in
    `analysis.py`. Results are labelled `rule_based_v1` in `keyword_analysis["method"]`.
    """

    async def analyze_resume_text(
        self,
        text_content: str,
        job_description: Optional[str] = None,
        target_role: Optional[str] = None,
        warnings: Optional[List[str]] = None,
    ) -> AIResumeAnalysis:
        return analyze_text(text_content, target_role=target_role, extraction_warnings=warnings)
