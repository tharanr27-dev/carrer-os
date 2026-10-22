"""Round / topic catalog and the helper constructors used by the curated question seed files."""

from typing import Any, Dict, List, Optional

# round -> {"label", "category" -> [(topic_slug, topic_label)]}
ROUNDS: Dict[str, Dict[str, Any]] = {
    "aptitude": {
        "label": "Aptitude & Online Assessment",
        "stage": 1,
        "groups": {
            "Quantitative Aptitude": [
                ("percentages", "Percentages"),
                ("ratios", "Ratios and Proportions"),
                ("averages", "Averages"),
                ("profit-loss", "Profit and Loss"),
                ("time-work", "Time and Work"),
                ("speed-distance", "Speed, Distance and Time"),
                ("interest", "Simple and Compound Interest"),
                ("number-systems", "Number Systems"),
                ("probability", "Probability"),
                ("permutations", "Permutations and Combinations"),
                ("data-interpretation", "Data Interpretation"),
                ("statistics", "Basic Statistics"),
            ],
            "Logical Reasoning": [
                ("series", "Number and Letter Series"),
                ("coding-decoding", "Coding and Decoding"),
                ("blood-relations", "Blood Relations"),
                ("directions", "Directions"),
                ("syllogisms", "Syllogisms"),
                ("seating", "Seating Arrangements"),
                ("puzzles", "Puzzles"),
                ("analogies", "Analogies"),
                ("deductions", "Logical Deductions"),
                ("statement-conclusion", "Statement and Conclusion"),
            ],
            "Verbal Ability": [
                ("grammar", "Grammar"),
                ("vocabulary", "Vocabulary"),
                ("sentence-correction", "Sentence Correction"),
                ("reading-comprehension", "Reading Comprehension"),
                ("error-identification", "Error Identification"),
                ("sentence-arrangement", "Sentence Arrangement"),
                ("business-communication", "Business Communication"),
            ],
            "Technical Screening": [
                ("programming-mcq", "Programming MCQs"),
                ("output-prediction", "Output Prediction"),
                ("debugging", "Debugging"),
                ("complexity-basics", "Complexity Basics"),
                ("sql-screening", "SQL Questions"),
                ("cs-fundamentals", "CS Fundamentals"),
            ],
        },
    },
    "technical": {
        "label": "Technical Interview",
        "stage": 2,
        "groups": {
            "Programming Languages": [
                ("python", "Python"),
                ("java", "Java"),
                ("c", "C"),
                ("cpp", "C++"),
                ("javascript", "JavaScript"),
                ("typescript", "TypeScript"),
            ],
            "Computer Science": [
                ("dsa", "Data Structures and Algorithms"),
                ("oop", "OOP"),
                ("dbms", "DBMS"),
                ("sql", "SQL"),
                ("os", "Operating Systems"),
                ("networks", "Computer Networks"),
                ("software-engineering", "Software Engineering"),
                ("complexity", "Time and Space Complexity"),
            ],
            "Development": [
                ("web-basics", "HTML, CSS, JavaScript"),
                ("react-next", "React and Next.js"),
                ("backend", "Backend Development"),
                ("rest-api", "REST APIs"),
                ("authentication", "Authentication"),
                ("databases", "Databases"),
                ("git", "Git and GitHub"),
                ("testing", "Testing and Debugging"),
            ],
            "AI and Data Science": [
                ("machine-learning", "Machine Learning"),
                ("deep-learning", "Deep Learning Fundamentals"),
                ("data-analysis", "Data Analysis"),
                ("ds-statistics", "Statistics"),
                ("nlp-llm", "NLP and LLM Fundamentals"),
                ("rag", "RAG Concepts"),
                ("ai-project", "AI Project Explanation"),
            ],
        },
    },
    "coding": {
        "label": "Coding & Problem Solving",
        "stage": 3,
        "groups": {
            "Problem Patterns": [
                ("arrays-strings", "Arrays and Strings"),
                ("linked-lists", "Linked Lists"),
                ("stacks-queues", "Stacks and Queues"),
                ("hashing", "Hashing"),
                ("trees-graphs", "Trees and Graphs"),
                ("searching-sorting", "Searching and Sorting"),
                ("recursion", "Recursion and Backtracking"),
                ("dynamic-programming", "Dynamic Programming"),
                ("greedy", "Greedy Algorithms"),
                ("sql-coding", "SQL Coding Challenges"),
            ]
        },
    },
    "communication": {
        "label": "Communication Lab",
        "stage": 4,
        "groups": {
            "Communication": [
                ("self-introduction", "Self-Introduction"),
                ("explain-simply", "Explaining Technical Concepts Simply"),
                ("explain-project", "Explaining Projects"),
                ("workplace", "Workplace Communication"),
                ("difficult-questions", "Answering Difficult Questions"),
                ("group-discussion", "Group Discussion"),
                ("presentation", "Presentation Practice"),
                ("strengths-weaknesses", "Strengths and Weaknesses"),
            ]
        },
    },
    "hr": {
        "label": "HR & Behavioural Interview",
        "stage": 5,
        "groups": {
            "HR Questions": [
                ("hr-core", "Core HR Questions"),
                ("behavioural", "Behavioural (STAR)"),
                ("situational", "Situational Questions"),
                ("ethics", "Ethical Scenarios"),
                ("teamwork-conflict", "Teamwork and Conflict"),
                ("fresher", "Fresher-Specific"),
            ]
        },
    },
    "resume": {
        "label": "Resume & Project Interview",
        "stage": 6,
        "groups": {"Your Profile": [("resume-project", "Projects, Skills and Education")]},
    },
    "managerial": {
        "label": "Managerial & Final Round",
        "stage": 7,
        "groups": {
            "Final Round": [
                ("ownership", "Ownership and Accountability"),
                ("decisions", "Technical Decisions and Trade-offs"),
                ("system-design", "Basic System Design"),
                ("adaptability", "Learning Ability and Adaptability"),
            ]
        },
    },
}

TARGET_ROLES = [
    "Python Developer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Software Engineer",
    "Data Analyst",
    "AI/ML Engineer",
    "DevOps Engineer",
]
LEVELS = ["fresher", "junior", "mid"]
DIFFICULTIES = ["easy", "medium", "hard"]

TOPIC_INDEX: Dict[str, Dict[str, str]] = {}
for _r, _meta in ROUNDS.items():
    for _group, _topics in _meta["groups"].items():
        for _slug, _label in _topics:
            TOPIC_INDEX[f"{_r}:{_slug}"] = {"round": _r, "slug": _slug, "label": _label, "group": _group}


def valid_topic(round_: str, topic: str) -> bool:
    return f"{round_}:{topic}" in TOPIC_INDEX


# ─── Seed constructors ────────────────────────────────────────────────────────

Q = Dict[str, Any]


def mcq(
    round_: str,
    topic: str,
    difficulty: str,
    prompt: str,
    options: List[str],
    correct: int,
    explanation: str,
    label: str = "foundational",
) -> Q:
    assert 0 <= correct < len(options), prompt
    return dict(
        round=round_, topic=topic, difficulty=difficulty, qtype="mcq", prompt=prompt,
        options=options, correct_index=correct, explanation=explanation, label=label,
    )


def text(
    round_: str,
    topic: str,
    difficulty: str,
    prompt: str,
    model_answer: str,
    keywords: Optional[List[List[str]]] = None,
    follow_ups: Optional[List[str]] = None,
    label: str = "commonly tested",
    framework: Optional[str] = None,
    mistakes: Optional[str] = None,
    roles: Optional[List[str]] = None,
) -> Q:
    return dict(
        round=round_, topic=topic, difficulty=difficulty, qtype="text", prompt=prompt,
        model_answer=model_answer, explanation=mistakes,
        rubric={"keywords": keywords or [], "framework": framework},
        follow_ups=follow_ups or [], label=label, roles=roles,
    )


def code(
    topic: str,
    difficulty: str,
    title: str,
    statement: str,
    input_format: str,
    output_format: str,
    constraints: List[str],
    examples: List[Dict[str, str]],
    hints: List[str],
    tests: List[Dict[str, str]],
    time_complexity: str,
    space_complexity: str,
    solution: str,
    explanation: str,
    concepts: List[str],
) -> Q:
    return dict(
        round="coding", topic=topic, difficulty=difficulty, qtype="code", label="commonly tested",
        prompt=f"{title}\n\n{statement}", explanation=explanation, model_answer=solution,
        extra={
            "title": title, "input_format": input_format, "output_format": output_format,
            "constraints": constraints, "examples": examples, "hints": hints, "tests": tests,
            "time_complexity": time_complexity, "space_complexity": space_complexity,
            "concepts": concepts,
        },
    )
