"""The reviewed bank is shipped content: verify it is well formed and that coding references really pass."""

import sqlite3
import subprocess
import sys

import pytest

from app.modules.training.bank.catalog import ROUNDS, TOPIC_INDEX
from app.modules.training.bank.coding import CODING
from app.modules.training.seed import all_seed


def test_every_seed_topic_is_in_catalog_and_fingerprints_unique():
    rows = all_seed()  # raises KeyError on an unknown round/topic
    assert len(rows) > 150
    fps = [r["fingerprint"] for r in rows]
    assert len(fps) == len(set(fps)), "duplicate question prompts in the bank"


def test_mcq_are_well_formed():
    for r in all_seed():
        if r["qtype"] != "mcq":
            continue
        opts = r["options"]
        assert len(opts) == 4 and len({o.lower() for o in opts}) == 4, r["prompt"]
        assert 0 <= r["correct_index"] < 4, r["prompt"]
        assert r["explanation"] and len(r["explanation"]) > 10, r["prompt"]


def test_text_questions_have_model_answers_and_rubrics():
    for r in all_seed():
        if r["qtype"] == "text":
            assert r["model_answer"] and len(r["model_answer"]) > 40, r["prompt"]
            assert r["rubric"]["keywords"], r["prompt"]


def test_every_catalog_topic_has_questions_except_resume():
    have = {f"{r['round']}:{r['topic']}" for r in all_seed()}
    missing = [k for k in TOPIC_INDEX if k not in have and not k.startswith("resume:")]
    assert not missing, f"topics with no reviewed questions: {missing}"


def test_all_rounds_present():
    assert set(ROUNDS) == {"aptitude", "technical", "coding", "communication", "hr", "resume", "managerial"}


@pytest.mark.parametrize("problem", [p for p in CODING if p["extra"].get("language") != "sql"], ids=lambda p: p["extra"]["title"])
def test_python_reference_solutions_pass_their_tests(problem):
    for t in problem["extra"]["tests"]:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", problem["model_answer"]],
            input=t["input"] + "\n", capture_output=True, text=True, timeout=20,
        )
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == t["output"].strip(), f"{problem['extra']['title']}: {t['input']!r}"


@pytest.mark.parametrize("problem", [p for p in CODING if p["extra"].get("language") == "sql"], ids=lambda p: p["extra"]["title"])
def test_sql_reference_solutions_return_expected_rows(problem):
    con = sqlite3.connect(":memory:")
    con.executescript(problem["extra"]["schema_sql"])
    rows = con.execute(problem["model_answer"]).fetchall()
    got = "\n".join("|".join(str(c) for c in r) for r in rows)
    assert got == problem["extra"]["tests"][0]["output"]
