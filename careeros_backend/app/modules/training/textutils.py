import hashlib
import re
from typing import Iterable

_TAG = re.compile(r"<[^>]*>")
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_STOP = {"the", "a", "an", "of", "to", "in", "is", "are", "and", "or", "what", "which", "how", "do", "does", "you", "your", "for", "on", "with", "that", "this"}


def clean_text(value: object, limit: int = 5000) -> str:
    """Strip markup/control characters from untrusted text (user or model output)."""
    s = str(value or "")
    s = _TAG.sub("", s)
    s = _CTRL.sub("", s)
    return s.strip()[:limit]


def normalize(text: str) -> str:
    return _NON_ALNUM.sub(" ", text.lower()).strip()


def fingerprint(text: str) -> str:
    return hashlib.sha1(normalize(text).encode("utf-8")).hexdigest()


def tokens(text: str) -> set:
    return {t for t in normalize(text).split() if t not in _STOP}


def jaccard(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def is_near_duplicate(candidate: str, existing: Iterable[str], threshold: float = 0.8) -> bool:
    fp = fingerprint(candidate)
    for other in existing:
        if fingerprint(other) == fp or jaccard(candidate, other) >= threshold:
            return True
    return False
