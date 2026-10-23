"""Unit tests for the Interview Evaluation Engine contract.

The engine used to return canned values through a mocked "AI orchestrator". It now scores real answers against the
reviewed question bank and builds the report from the answers given (see also tests/training/test_real_coaching_features.py).
This file keeps the original contract checks (types, non-empty feedback, report shape) against the real behaviour,
using an isolated in-memory SQLite database.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.modules.interviews.evaluation_engine import InterviewEvaluationEngine
from app.modules.interviews.models import InterviewAnswer, InterviewQuestion, InterviewSession
from app.modules.interviews.schemas import AIEvaluationScore, AIFinalReport
from app.modules.training.seed import ensure_seed

QUESTION = "Explain the four pillars of OOP with a real-world example."
ANSWER = (
    "Encapsulation hides data behind methods, like a bank account balance. Abstraction exposes what an object does. "
    "Inheritance reuses a parent class and polymorphism lets one call behave differently per type."
)


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as s:
        await ensure_seed(s)
        yield s
    await engine.dispose()


@pytest.fixture
def engine(session):
    return InterviewEvaluationEngine(session)


@pytest.mark.asyncio
async def test_evaluate_answer_returns_score(engine):
    """evaluate_answer returns a score with feedback derived from the answer."""
    score = await engine.evaluate_answer(question=QUESTION, answer=ANSWER)
    assert isinstance(score, AIEvaluationScore)
    assert score.overall_score > 0
    assert len(score.strengths) > 0
    # A weak answer gets actionable improvements.
    weak = await engine.evaluate_answer(question=QUESTION, answer="Not sure.")
    assert len(weak.improvements) > 0 and weak.overall_score < score.overall_score


@pytest.mark.asyncio
async def test_next_question_returns_a_reviewed_question(engine):
    """next_question returns a non-empty question from the reviewed bank, with the topic it covers."""
    question, skills = await engine.next_question(uuid.uuid4(), "technical", "MEDIUM", asked=["Tell me about yourself"])
    assert isinstance(question, str) and len(question) > 5
    assert await engine._lookup(question) is not None
    assert skills


@pytest.mark.asyncio
async def test_generate_final_report(engine, session):
    """generate_final_report returns a valid AIFinalReport computed from the session's answers."""
    s = InterviewSession(user_id=uuid.uuid4(), interview_type="TECHNICAL", difficulty="MEDIUM")
    session.add(s)
    await session.flush()
    for q, a in ((QUESTION, ANSWER), ("Explain closures in JavaScript with an example.", "Not sure.")):
        row = InterviewQuestion(session_id=s.id, question_text=q)
        session.add(row)
        await session.flush()
        session.add(InterviewAnswer(question_id=row.id, answer_text=a))
    await session.commit()
    report = await engine.generate_final_report(s.id)
    assert isinstance(report, AIFinalReport)
    assert 0 < report.overall_score < 100
    assert isinstance(report.recommended_learning, list) and report.recommended_learning
    assert report.detailed_analysis["scored_answers"] == 2
