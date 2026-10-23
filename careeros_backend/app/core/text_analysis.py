"""Deterministic, local text analysis shared by résumé analysis, communication feedback and candidate matching.

Nothing here calls an AI service. Every function is a transparent rule (word lists, counts, patterns), so the
results are *measurements of the text*, not judgements, and are labelled that way wherever they are shown.
"""

import re
from collections import Counter
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# ── Skill vocabulary ─────────────────────────────────────────────────────────
# canonical name -> aliases (matched case-insensitively with symbol-aware word boundaries)
SKILLS: Dict[str, Sequence[str]] = {
    "Python": ["python"], "Java": ["java"], "JavaScript": ["javascript", "js", "ecmascript"],
    "TypeScript": ["typescript"], "C": ["c language", "ansi c"], "C++": ["c++", "cpp"], "C#": ["c#", "csharp"],
    "Go": ["golang"], "Rust": ["rust"], "Kotlin": ["kotlin"], "Swift": ["swift"], "PHP": ["php"], "Ruby": ["ruby"],
    "R": ["r programming", "rstudio"], "MATLAB": ["matlab"], "Bash": ["bash", "shell scripting"],
    "HTML": ["html", "html5"], "CSS": ["css", "css3"], "Tailwind CSS": ["tailwind", "tailwindcss"],
    "Sass": ["sass", "scss"], "React": ["react", "reactjs", "react.js"], "Next.js": ["next.js", "nextjs"],
    "Angular": ["angular"], "Vue": ["vue", "vue.js", "vuejs"], "Redux": ["redux"], "jQuery": ["jquery"],
    "Node.js": ["node.js", "nodejs", "node js"], "Express": ["express.js", "expressjs"],
    "FastAPI": ["fastapi"], "Django": ["django"], "Flask": ["flask"], "Spring Boot": ["spring boot", "springboot"],
    "Spring": ["spring framework"], ".NET": [".net", "dotnet", "asp.net"], "Laravel": ["laravel"],
    "REST APIs": ["rest api", "rest apis", "restful", "rest"], "GraphQL": ["graphql"], "gRPC": ["grpc"],
    "Microservices": ["microservices", "microservice"], "WebSockets": ["websocket", "websockets"],
    "SQL": ["sql"], "PostgreSQL": ["postgresql", "postgres"], "MySQL": ["mysql"], "SQLite": ["sqlite"],
    "MongoDB": ["mongodb", "mongo"], "Redis": ["redis"], "Elasticsearch": ["elasticsearch"], "Oracle": ["oracle db", "oracle sql"],
    "SQLAlchemy": ["sqlalchemy"], "Hibernate": ["hibernate"], "Firebase": ["firebase"], "Supabase": ["supabase"],
    "Docker": ["docker"], "Kubernetes": ["kubernetes", "k8s"], "Terraform": ["terraform"], "Ansible": ["ansible"],
    "Jenkins": ["jenkins"], "GitHub Actions": ["github actions"], "CI/CD": ["ci/cd", "cicd", "ci cd"],
    "Git": ["git"], "GitHub": ["github"], "GitLab": ["gitlab"], "Linux": ["linux", "ubuntu"],
    "AWS": ["aws", "amazon web services", "ec2", "s3 bucket"], "Azure": ["azure"], "GCP": ["gcp", "google cloud"],
    "Nginx": ["nginx"], "Prometheus": ["prometheus"], "Grafana": ["grafana"],
    "Machine Learning": ["machine learning", "ml"], "Deep Learning": ["deep learning"], "NLP": ["nlp", "natural language processing"],
    "Computer Vision": ["computer vision", "opencv"], "LLMs": ["llm", "llms", "large language model", "large language models"],
    "RAG": ["rag", "retrieval augmented generation", "retrieval-augmented generation"],
    "TensorFlow": ["tensorflow"], "PyTorch": ["pytorch"], "Keras": ["keras"], "scikit-learn": ["scikit-learn", "sklearn"],
    "Pandas": ["pandas"], "NumPy": ["numpy"], "Matplotlib": ["matplotlib"], "Jupyter": ["jupyter"],
    "Data Analysis": ["data analysis", "data analytics"], "Statistics": ["statistics", "statistical analysis"],
    "Excel": ["excel", "ms excel", "microsoft excel"], "Power BI": ["power bi", "powerbi"], "Tableau": ["tableau"],
    "Spark": ["apache spark", "pyspark"], "Hadoop": ["hadoop"], "Airflow": ["airflow"], "Kafka": ["kafka"],
    "Data Structures": ["data structures"], "Algorithms": ["algorithms"], "OOP": ["oop", "object oriented", "object-oriented"],
    "System Design": ["system design"], "DBMS": ["dbms"], "Operating Systems": ["operating systems"],
    "Computer Networks": ["computer networks", "networking"],
    "Testing": ["unit testing", "test automation", "tdd"], "Pytest": ["pytest"], "JUnit": ["junit"], "Selenium": ["selenium"],
    "Jest": ["jest"], "Cypress": ["cypress"], "Postman": ["postman"], "Swagger": ["swagger", "openapi"],
    "Agile": ["agile"], "Scrum": ["scrum"], "Jira": ["jira"], "Figma": ["figma"],
    "Android": ["android"], "iOS": ["ios"], "Flutter": ["flutter"], "React Native": ["react native"],
    "Cybersecurity": ["cybersecurity", "cyber security", "information security"], "OAuth": ["oauth"], "JWT": ["jwt"],
}

# Skills usually expected for a target role. Used for "keywords not found" hints and candidate matching.
ROLE_SKILLS: Dict[str, List[str]] = {
    "python developer": ["Python", "SQL", "Git", "REST APIs", "FastAPI", "Django", "Flask", "Docker", "Testing", "Linux"],
    "frontend developer": ["JavaScript", "TypeScript", "React", "HTML", "CSS", "Git", "REST APIs", "Testing", "Next.js"],
    "backend developer": ["REST APIs", "SQL", "PostgreSQL", "Git", "Docker", "Redis", "Testing", "Linux", "Microservices"],
    "full stack developer": ["JavaScript", "React", "Node.js", "SQL", "REST APIs", "Git", "HTML", "CSS", "Docker"],
    "software engineer": ["Data Structures", "Algorithms", "OOP", "Git", "SQL", "Testing", "System Design", "Linux"],
    "data analyst": ["SQL", "Excel", "Python", "Pandas", "Power BI", "Tableau", "Statistics", "Data Analysis"],
    "ai/ml engineer": ["Python", "Machine Learning", "Deep Learning", "NumPy", "Pandas", "scikit-learn", "TensorFlow", "PyTorch", "NLP"],
    "devops engineer": ["Linux", "Docker", "Kubernetes", "CI/CD", "Git", "AWS", "Terraform", "Bash", "Jenkins"],
}
GENERIC_SKILLS = ["Git", "SQL", "Data Structures", "Algorithms", "Testing"]


def role_skills(role: Optional[str]) -> Tuple[List[str], bool]:
    """(skills, matched_a_known_role). Matching is by whole words so 'Backend Engineer' maps to backend."""
    if role:
        r = role.lower()
        if r in ROLE_SKILLS:
            return ROLE_SKILLS[r], True
        for key, skills in ROLE_SKILLS.items():
            head = key.split()[0].split("/")[0]
            if head in r and (len(key.split()) == 1 or key.split()[-1] in r or "engineer" in r or "developer" in r):
                return skills, True
    return GENERIC_SKILLS, False


def _alias_pattern(alias: str) -> "re.Pattern[str]":
    # Boundaries tolerate symbols in names such as C++, C#, .NET and Node.js.
    return re.compile(r"(?<![A-Za-z0-9+#.])" + re.escape(alias) + r"(?![A-Za-z0-9+#]|\.[A-Za-z0-9])", re.IGNORECASE)


_COMPILED = {name: [_alias_pattern(a) for a in aliases] for name, aliases in SKILLS.items()}
# One-letter / ambiguous names are only counted in clear skill contexts (lists or "<name> programming").
_CONTEXT_ONLY = {
    "C": [re.compile(r"(?<![A-Za-z0-9+#.])C(?=\s*(?:,|/|;|\||\band\b|programming\b|language\b))(?!\+|#)")],
    "R": [re.compile(r"(?<![A-Za-z0-9+#.])R(?=\s*(?:,|/|;|\||programming\b|language\b))")],
    "Go": [re.compile(r"(?<![A-Za-z0-9+#.])Go(?=\s*(?:,|/|;|\||lang\b|programming\b|developer\b|routines?\b))")],
}


def extract_skills(text: str) -> List[str]:
    """Skills from the vocabulary that literally appear in the text, in vocabulary order."""
    found = []
    for name, pats in _COMPILED.items():
        pats = _CONTEXT_ONLY.get(name, []) + ([] if name in ("C", "R") else pats if name != "Go" else pats)
        if any(p.search(text) for p in pats):
            found.append(name)
    return found


# ── Sentences, words ─────────────────────────────────────────────────────────
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")


def sentences(text: str) -> List[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text) if len(s.strip()) > 1]


def words(text: str) -> List[str]:
    return _WORD.findall(text)


# ── Language measurements (text only) ────────────────────────────────────────
FILLERS = ["um", "uh", "erm", "you know", "i mean", "basically", "actually", "literally", "kind of", "sort of", "like"]
HEDGES = ["maybe", "perhaps", "i think", "i guess", "probably", "possibly", "not sure", "i feel like", "might be", "just"]
INFORMAL = {
    "gonna": "going to", "wanna": "want to", "gotta": "have to", "kinda": "somewhat", "sorta": "somewhat",
    "stuff": "work / items (be specific)", "things": "specific items (be specific)", "lots of": "many",
    "a lot of": "many", "guys": "team members", "awesome": "excellent", "cool": "impressive",
    "ok": "acceptable", "okay": "acceptable", "yeah": "yes", "nope": "no", "btw": "by the way",
    "thanks a lot": "thank you", "pretty good": "good", "super": "very",
}
ACTION_VERBS = {
    "built", "developed", "designed", "implemented", "created", "led", "managed", "improved", "optimized",
    "optimised", "reduced", "increased", "delivered", "launched", "automated", "analysed", "analyzed",
    "engineered", "architected", "deployed", "integrated", "migrated", "refactored", "tested", "debugged",
    "collaborated", "mentored", "organised", "organized", "researched", "trained", "published", "presented",
    "established", "streamlined", "resolved", "coordinated", "configured", "maintained", "wrote", "drove",
}
WEAK_PHRASES = {
    "responsible for": "built / led / delivered", "worked on": "built / developed / implemented",
    "helped with": "contributed to / supported / delivered", "involved in": "led / contributed to",
    "duties included": "achieved / delivered", "assisted in": "supported / contributed to",
}


def count_phrase(text: str, phrase: str) -> int:
    return len(re.findall(r"(?<![A-Za-z])" + re.escape(phrase) + r"(?![A-Za-z])", text, re.IGNORECASE))


def filler_counts(text: str) -> Dict[str, int]:
    # "like" is only counted as a filler when not preceded by a verb-ish context; keep it simple and conservative:
    out = {}
    for f in FILLERS:
        n = count_phrase(text, f)
        if f == "like":
            n = len(re.findall(r"(?:,|\b(?:was|is|it's|was just|so|and|but))\s+like\b", text, re.IGNORECASE))
        if n:
            out[f] = n
    return out


def hedge_counts(text: str) -> Dict[str, int]:
    return {h: n for h in HEDGES if (n := count_phrase(text, h))}


def informal_hits(text: str) -> Dict[str, str]:
    return {w: alt for w, alt in INFORMAL.items() if count_phrase(text, w)}


def mechanical_issues(text: str) -> List[Dict[str, str]]:
    """Mechanical writing slips only (not full grammar): capitalisation, punctuation, repeated words, spacing."""
    issues: List[Dict[str, str]] = []
    for m in re.finditer(r"\b(\w+)\s+\1\b", text, re.IGNORECASE):
        if m.group(1).lower() not in {"that", "had", "very"}:
            issues.append({"category": "Repeated word", "original": m.group(0), "suggestion": m.group(1),
                           "reasoning": "The same word appears twice in a row."})
    for m in re.finditer(r"(?<![A-Za-z'’])i(?![A-Za-z'’])", text):
        issues.append({"category": "Capitalisation", "original": text[max(0, m.start() - 8): m.end() + 8].strip(),
                       "suggestion": "I", "reasoning": "The pronoun 'I' is always capitalised."})
        break
    for s in sentences(text):
        if s[0].isalpha() and s[0].islower():
            issues.append({"category": "Capitalisation", "original": s[:30], "suggestion": s[0].upper() + s[1:30],
                           "reasoning": "A sentence starts with a capital letter."})
            break
    stripped = text.strip()
    if stripped and len(words(stripped)) >= 6 and stripped[-1] not in ".!?\"')":
        issues.append({"category": "Punctuation", "original": stripped[-25:], "suggestion": stripped[-25:] + ".",
                       "reasoning": "The message does not end with sentence punctuation."})
    if re.search(r" {2,}", text):
        issues.append({"category": "Spacing", "original": "double space", "suggestion": "single space",
                       "reasoning": "Extra spaces between words."})
    return issues


def type_token_ratio(ws: Iterable[str]) -> float:
    ws = [w.lower() for w in ws]
    return len(set(ws)) / len(ws) if ws else 0.0


def avg_sentence_length(text: str) -> float:
    ss = sentences(text)
    return sum(len(words(s)) for s in ss) / len(ss) if ss else 0.0


def top_repeated_words(text: str, n: int = 3, min_len: int = 5) -> List[Tuple[str, int]]:
    stop = {"which", "would", "should", "could", "their", "there", "about", "because", "these", "those", "where", "while", "being"}
    c = Counter(w.lower() for w in words(text) if len(w) >= min_len and w.lower() not in stop)
    return [(w, k) for w, k in c.most_common(n) if k >= 4]


def clamp(x: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, x))
