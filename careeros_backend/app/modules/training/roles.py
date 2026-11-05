"""Universal job-role handling for role-based training.

Any reasonable job title is accepted. The student's wording is preserved for display; a normalised key is used only for
matching. A title is mapped to practice topics in this order:

  1. a known catalog role (or alias) - curated topic lists;
  2. a close variant of one ("Senior React Frontend Developer" -> Frontend Developer);
  3. keyword inference over the title ("Cloud Security Specialist" -> cloud + security topics);
  4. otherwise the role is "unmapped": it is still accepted, but questions can only come from AI generation
     (when a provider is configured) because no reviewed topics are known for it. Nothing unrelated is substituted.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.modules.training.bank.catalog import TOPIC_INDEX
from app.modules.training.textutils import clean_text

MAX_TITLE = 60
_ALLOWED = re.compile(r"^[\w][\w /&+#.,'()\-]*$", re.UNICODE)
_URL = re.compile(r"(https?://|www\.)", re.IGNORECASE)

# Seniority words are removed for matching but kept in the displayed title.
_SENIORITY = {"senior", "sr", "junior", "jr", "lead", "principal", "staff", "associate", "intern", "trainee", "entry", "level",
              "fresher", "graduate", "head", "chief", "i", "ii", "iii"}
_LEVEL_HINT = {"fresher": "fresher", "graduate": "fresher", "intern": "fresher", "trainee": "fresher", "entry": "fresher",
               "junior": "junior", "jr": "junior", "associate": "junior",
               "senior": "mid", "sr": "mid", "lead": "mid", "principal": "mid", "staff": "mid"}
_SYNONYMS = {"developer": "engineer", "programmer": "engineer", "dev": "engineer", "sde": "engineer", "swe": "engineer",
             "tester": "qa", "testing": "qa", "quality": "qa", "assurance": "qa", "analyst": "analyst",
             "specialist": "engineer", "architect": "architect", "designer": "designer", "manager": "manager"}
_FILLER = {"and", "the", "of", "for", "in", "a", "an", "at"}
_REWRITES = [("c++", "cpp"), ("c#", "csharp"), (".net", "dotnet"), ("node.js", "nodejs"), ("front-end", "frontend"),
             ("front end", "frontend"), ("back-end", "backend"), ("back end", "backend"), ("full-stack", "fullstack"),
             ("full stack", "fullstack"), ("ui/ux", "ux ui"), ("ai/ml", "ai ml"), ("ci/cd", "cicd")]

# family -> catalog entries: title, aliases, topic slugs in priority order
ROLE_CATALOG: List[Dict] = [
    {"title": "Frontend Developer", "family": "Software", "aliases": ["Front End Developer", "UI Developer", "React Developer", "Web Developer"],
     "domains": ["web-basics", "javascript", "react-next", "typescript", "rest-api", "testing", "git"]},
    {"title": "Backend Developer", "family": "Software", "aliases": ["Back End Developer", "API Developer", "Server-side Developer"],
     "domains": ["backend", "rest-api", "authentication", "databases", "sql", "dbms", "os", "networks"]},
    {"title": "Full Stack Developer", "family": "Software", "aliases": ["Fullstack Engineer", "Full-Stack Developer"],
     "domains": ["javascript", "react-next", "backend", "rest-api", "sql", "authentication", "git"]},
    {"title": "Software Engineer", "family": "Software", "aliases": ["Software Developer", "SDE", "Programmer"],
     "domains": ["dsa", "oop", "dbms", "os", "networks", "software-engineering", "complexity"]},
    {"title": "Python Developer", "family": "Software", "aliases": ["Python Engineer"],
     "domains": ["python", "oop", "dsa", "sql", "dbms", "rest-api", "git", "testing"]},
    {"title": "Java Developer", "family": "Software", "aliases": ["Java Engineer"],
     "domains": ["java", "oop", "dsa", "dbms", "rest-api", "sql"]},
    {"title": "C++ Developer", "family": "Software", "aliases": ["C++ Engineer", "Embedded Software Engineer"],
     "domains": ["cpp", "dsa", "oop", "os", "c"]},
    {"title": "Data Analyst", "family": "Data & AI", "aliases": ["Business Intelligence Analyst", "BI Analyst", "Reporting Analyst"],
     "domains": ["sql", "data-analysis", "ds-statistics", "python", "dbms"]},
    {"title": "Data Scientist", "family": "Data & AI", "aliases": ["Research Scientist"],
     "domains": ["machine-learning", "ds-statistics", "python", "data-analysis", "deep-learning", "sql"]},
    {"title": "Data Engineer", "family": "Data & AI", "aliases": ["ETL Developer"],
     "domains": ["sql", "dbms", "python", "databases", "cloud-computing"]},
    {"title": "AI/ML Engineer", "family": "Data & AI", "aliases": ["Machine Learning Engineer", "ML Engineer"],
     "domains": ["machine-learning", "deep-learning", "python", "nlp-llm", "rag", "ds-statistics"]},
    {"title": "AI Engineer", "family": "Data & AI", "aliases": ["Generative AI Engineer", "GenAI Engineer", "LLM Engineer"],
     "domains": ["nlp-llm", "rag", "prompt-engineering", "llm-safety", "python", "machine-learning"]},
    {"title": "Prompt Engineer", "family": "Data & AI", "aliases": ["Prompt Designer", "Conversational AI Designer"],
     "domains": ["prompt-engineering", "llm-safety", "nlp-llm", "rag"]},
    {"title": "DevOps Engineer", "family": "Cloud & Security", "aliases": ["Site Reliability Engineer", "SRE", "Platform Engineer", "Release Engineer"],
     "domains": ["devops-practices", "cloud-computing", "os", "networks", "git", "testing"]},
    {"title": "Cloud Engineer", "family": "Cloud & Security", "aliases": ["Cloud Architect", "Cloud Solutions Architect", "AWS Engineer", "Azure Engineer"],
     "domains": ["cloud-computing", "networks", "os", "devops-practices", "cybersecurity"]},
    {"title": "Cybersecurity Analyst", "family": "Cloud & Security", "aliases": ["Security Analyst", "Information Security Analyst", "SOC Analyst", "Penetration Tester", "Ethical Hacker"],
     "domains": ["cybersecurity", "networks", "os", "authentication"]},
    {"title": "Network Engineer", "family": "Cloud & Security", "aliases": ["Network Administrator", "System Administrator", "Systems Engineer"],
     "domains": ["networks", "os", "cybersecurity"]},
    {"title": "Database Administrator", "family": "Software", "aliases": ["DBA", "Database Developer"],
     "domains": ["dbms", "sql", "databases", "os"]},
    {"title": "QA Engineer", "family": "Quality", "aliases": ["Software Tester", "Test Engineer", "SDET", "Test Automation Engineer", "Quality Analyst"],
     "domains": ["qa-practices", "testing", "sql", "git"]},
    {"title": "UI/UX Designer", "family": "Design & Product", "aliases": ["UX Designer", "UI Designer", "Product Designer", "Interaction Designer"],
     "domains": ["ux-design", "web-basics"]},
    {"title": "Product Manager", "family": "Design & Product", "aliases": ["Product Owner", "Associate Product Manager", "APM"],
     "domains": ["product-management", "data-analysis"]},
    {"title": "Business Analyst", "family": "Design & Product", "aliases": ["Systems Analyst"],
     "domains": ["sql", "data-analysis", "product-management"]},
]

# topic slug -> title keywords used to infer topics for titles that are not in the catalog
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "prompt-engineering": ["prompt", "genai", "generative ai", "llm"],
    "llm-safety": ["prompt", "ai safety", "responsible ai", "llm", "trust and safety"],
    "nlp-llm": ["nlp", "llm", "language model", "chatbot", "conversational", "genai", "generative ai", "ai engineer"],
    "rag": ["rag", "retrieval", "genai", "generative ai"],
    "machine-learning": ["machine learning", "ml", "data scien", "ai", "mlops"],
    "deep-learning": ["deep learning", "computer vision", "neural"],
    "ds-statistics": ["data scien", "statistic", "analytics", "research scientist"],
    "data-analysis": ["data analy", "analytics", "business intelligence", "bi", "reporting", "insights", "business analyst"],
    "sql": ["sql", "database", "dba", "data engineer", "data analy", "business analyst", "bi", "reporting"],
    "dbms": ["database", "dba", "data engineer"],
    "python": ["python", "django", "flask", "fastapi", "automation"],
    "java": ["java", "spring", "android"],
    "cpp": ["cpp", "embedded", "game"],
    "c": ["embedded", "firmware"],
    "javascript": ["javascript", "frontend", "web", "react", "angular", "vue", "nodejs", "fullstack"],
    "typescript": ["typescript", "frontend", "react", "angular", "fullstack"],
    "web-basics": ["frontend", "web", "html", "css", "wordpress"],
    "react-next": ["react", "next", "frontend", "fullstack"],
    "backend": ["backend", "server", "api", "django", "flask", "fastapi", "spring", "nodejs", "fullstack", "microservice"],
    "rest-api": ["api", "backend", "fullstack", "integration", "mobile", "android", "ios"],
    "authentication": ["security", "identity", "iam", "auth"],
    "databases": ["database", "dba", "data engineer"],
    "dsa": ["software", "swe", "sde", "coding"],
    "oop": ["java", "cpp", "csharp", "android", "ios", "mobile", "software"],
    "os": ["linux", "system admin", "sysadmin", "systems", "devops", "sre", "reliability", "embedded", "infrastructure"],
    "networks": ["network", "devops", "sre", "infrastructure", "security", "cyber"],
    "git": ["devops", "software", "sre"],
    "testing": ["qa", "test", "sdet", "automation"],
    "qa-practices": ["qa", "quality assurance", "tester", "sdet", "test"],
    "software-engineering": ["software", "architect", "mobile", "android", "ios"],
    "cybersecurity": ["security", "cyber", "infosec", "soc", "pentest", "penetration", "ethical hacker", "threat", "malware", "forensic"],
    "cloud-computing": ["cloud", "aws", "azure", "gcp", "solutions architect", "infrastructure", "sre", "devops", "platform"],
    "devops-practices": ["devops", "sre", "reliability", "platform", "release", "cicd", "infrastructure"],
    "ux-design": ["ux", "ui", "user experience", "design", "interaction", "visual"],
    "product-management": ["product manager", "product management", "product owner", "program manager", "scrum", "business analyst"],
}


class InvalidRole(ValueError):
    """The title cannot be used as a job role."""


@dataclass
class RoleProfile:
    title: str  # the student's wording (cleaned only)
    key: str  # normalised, for matching/grouping progress per role
    family: Optional[str]
    domains: List[str]  # topic slugs (round "technical"), priority order
    match: str  # catalog | similar | keywords | none
    matched_title: Optional[str] = None
    level_hint: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    @property
    def mapped(self) -> bool:
        return bool(self.domains)

    def domain_labels(self) -> List[str]:
        return [topic_label_for(d) for d in self.domains]


def topic_label_for(slug: str) -> str:
    return TOPIC_INDEX.get(f"technical:{slug}", {}).get("label", slug.replace("-", " ").title())


def clean_role_title(raw: object) -> str:
    """Preserve the student's wording; strip markup/control characters and collapse whitespace."""
    title = re.sub(r"\s+", " ", clean_text(raw, 200)).strip()
    if len(title) < 2:
        raise InvalidRole("Enter a job title of at least 2 characters.")
    if len(title) > MAX_TITLE:
        raise InvalidRole(f"A job title can be at most {MAX_TITLE} characters.")
    if _URL.search(title) or not _ALLOWED.match(title) or not re.search(r"[^\W\d_]{2,}", title, re.UNICODE):
        raise InvalidRole("Use letters, numbers and simple punctuation only (for example 'Cloud Security Engineer').")
    return title


def _rewrite(text: str) -> str:
    low = text.lower()
    for a, b in _REWRITES:
        low = low.replace(a, f" {b} ")
    return low


def _tokens(title: str, drop_seniority: bool = True) -> List[str]:
    out = []
    for t in re.findall(r"[a-z0-9]+", _rewrite(title)):
        if t in _FILLER or (drop_seniority and t in _SENIORITY):
            continue
        out.append(_SYNONYMS.get(t, t))
    return out


def role_key(title: str) -> str:
    return "-".join(sorted(set(_tokens(title)))) or "role"


def _entry_keys(entry: Dict) -> List[str]:
    return [role_key(entry["title"]), *[role_key(a) for a in entry.get("aliases", [])]]


def _catalog_index() -> Dict[str, Dict]:
    index: Dict[str, Dict] = {}
    for e in ROLE_CATALOG:
        for k in _entry_keys(e):
            index.setdefault(k, e)
    return index


_INDEX = _catalog_index()


def _infer_domains(title: str) -> List[str]:
    padded = f" {' '.join(re.findall(r'[a-z0-9]+', _rewrite(title)))} "
    scored = []
    for order, (slug, words) in enumerate(DOMAIN_KEYWORDS.items()):
        hits = sum(1 for w in words if re.search(rf"\b{re.escape(w)}", padded))
        if hits:
            scored.append((-hits, -len(words), order, slug))  # ties: the topic with the broader keyword list is the main domain
    return [s[-1] for s in sorted(scored)][:6]


def resolve_role(raw_title: str) -> RoleProfile:
    title = clean_role_title(raw_title)
    key = role_key(title)
    toks = set(_tokens(title))
    hint = next((_LEVEL_HINT[t] for t in re.findall(r"[a-z]+", title.lower()) if t in _LEVEL_HINT), None)

    if key in _INDEX:
        e = _INDEX[key]
        return RoleProfile(title, key, e["family"], list(e["domains"]), "catalog", e["title"], hint)

    # a catalog entry whose tokens are all contained in the title ("Senior React Frontend Developer")
    best, best_size = None, 0
    for e in ROLE_CATALOG:
        for k in _entry_keys(e):
            kt = set(k.split("-"))
            if kt and kt <= toks and len(kt) > best_size:
                best, best_size = e, len(kt)
    if best is not None and best_size >= 2:
        # Extra words in the title ("Cloud *Security* Specialist") bring their own topics to the front.
        known = set(role_key(best["title"]).split("-")) | {t for a in best.get("aliases", []) for t in role_key(a).split("-")}
        extra = [t for t in _tokens(title) if t not in known]
        promoted = _infer_domains(" ".join(extra)) if extra else []
        domains = list(dict.fromkeys([*promoted[:3], *best["domains"]]))
        return RoleProfile(title, key, best["family"], domains, "similar", best["title"], hint,
                           [f"Matched to the closest known role: {best['title']}."])

    inferred = _infer_domains(title)
    if inferred:
        return RoleProfile(title, key, None, inferred, "keywords", None, hint,
                           ["Topics were inferred from the words in your job title."])
    return RoleProfile(title, key, None, [], "none", None, hint,
                       ["No reviewed topics are known for this job title yet."])


def search_roles(query: str, limit: int = 12) -> List[Dict]:
    """Catalog roles matching a free-text query (title, alias or word), best first. Empty query lists all."""
    q = (query or "").strip().lower()
    qtok = set(_tokens(q, drop_seniority=False)) if q else set()
    scored = []
    for i, e in enumerate(ROLE_CATALOG):
        names = [e["title"], *e.get("aliases", [])]
        if not q:
            score = 1.0 - i / 1000
        else:
            score = 0.0
            for n in names:
                nl = n.lower()
                if nl == q:
                    score = max(score, 3.0)
                elif nl.startswith(q):
                    score = max(score, 2.0)
                elif q in nl:
                    score = max(score, 1.5)
                else:
                    ntok = set(_tokens(n, drop_seniority=False))
                    overlap = len(qtok & ntok)
                    if overlap:
                        score = max(score, 0.5 + overlap / max(len(ntok), 1))
        if score > 0:
            scored.append((-score, i, e))
    return [e for _, _, e in sorted(scored)[:limit]]


def vocabulary_for(profile: RoleProfile) -> set:
    """Words that make a generated question plausibly about this role (used to reject off-topic output)."""
    vocab = set(_tokens(profile.title, drop_seniority=True))
    for d in profile.domains:
        for kw in DOMAIN_KEYWORDS.get(d, []):
            vocab.update(re.findall(r"[a-z0-9]+", kw))
        vocab.update(re.findall(r"[a-z0-9]+", topic_label_for(d).lower()))
    return {w for w in vocab if len(w) > 2} - {"and", "the", "engineer", "software", "data", "developer"}
