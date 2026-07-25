"""Unit tests for the Interview Evaluation Engine."""

from unittest.mock import AsyncMock, patch

import pytest

from app.modules.interviews.evaluation_engine import InterviewEvaluationEngine
from app.modules.interviews.schemas import AIEvaluationScore, AIFinalReport


@pytest.fixture
def engine():
    with patch("app.modules.interviews.evaluation_engine.get_ai_orchestrator") as mock_orch_fn:
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(
            return_value={
                "status": "success",
                "response_text": "Great answer",
                "tokens_used": 50,
            }
        )
        mock_orch_fn.return_value = mock_orch
        yield InterviewEvaluationEngine()


@pytest.mark.asyncio
async def test_evaluate_answer_returns_score(engine):
    """evaluate_answer routes through orchestrator and returns a score."""
    score = await engine.evaluate_answer(
        question="Describe a challenging project.",
        answer="I led a migration of a monolith to microservices...",
    )
    assert isinstance(score, AIEvaluationScore)
    assert score.overall_score > 0
    assert len(score.strengths) > 0
    assert len(score.improvements) > 0


@pytest.mark.asyncio
async def test_generate_next_question(engine):
    """generate_next_question returns a non-empty string."""
    question = await engine.generate_next_question(
        past_qa=[{"q": "Tell me about yourself", "a": "I am a software engineer."}],
        interview_type="technical",
    )
    assert isinstance(question, str)
    assert len(question) > 5


@pytest.mark.asyncio
async def test_generate_final_report(engine):
    """generate_final_report returns a valid AIFinalReport."""
    report = await engine.generate_final_report(
        all_qa=[{"q": "Q1", "a": "A1"}, {"q": "Q2", "a": "A2"}]
    )
    assert isinstance(report, AIFinalReport)
    assert report.overall_score >= 0
    assert isinstance(report.recommended_learning, list)
