import logging
import re
import time
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, status

from app.modules.jobs.schemas import (
    JobFilters,
    JobMatch,
    RecommendedJobItem,
    RecommendedJobsResponse,
)

logger = logging.getLogger("careeros")

# Documented public search endpoint: https://himalayas.app/docs/remote-jobs-api
HIMALAYAS_SEARCH_API_URL = "https://himalayas.app/jobs/api/search"
HIMALAYAS_HOST = "himalayas.app"
PAGE_SIZE = 20  # fixed by the upstream search endpoint (no limit parameter)
MAX_PAGE = 250  # upstream caps totalCount at 5000
DEFAULT_TIMEOUT_SECONDS = 10.0
CONNECT_TIMEOUT_SECONDS = 5.0
MAX_DESCRIPTION_CHARS = 4000

# Himalayas refreshes its data every 24h, so a short cache loses nothing and spares the
# shared, unauthenticated rate limit.
CACHE_TTL_SECONDS = 900
CACHE_MAX_ENTRIES = 256

# Values the upstream API accepted when probed ("lead", "junior", ... return HTTP 400).
ALLOWED_SENIORITY = {"entry-level", "mid-level", "senior", "manager", "director", "executive"}
ALLOWED_EMPLOYMENT_TYPES = {"full-time", "part-time", "contractor", "temporary", "intern"}

MATCH_METHOD = (
    "Estimate: share of your saved skills (up to 6) that appear in the job title or "
    "description. It is a keyword overlap, not a hiring probability."
)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def parse_unix_timestamp(val: Any) -> Optional[str]:
    """Converts a Unix timestamp (seconds) or ISO string into ISO 8601; None if unusable."""
    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        try:
            return datetime.fromtimestamp(val, tz=timezone.utc).isoformat()
        except (ValueError, OverflowError, OSError):
            return None
    if isinstance(val, str) and val.strip():
        s = val.strip()
        try:
            return datetime.fromtimestamp(float(s), tz=timezone.utc).isoformat()
        except (ValueError, OverflowError, OSError):
            try:
                return datetime.fromisoformat(s).isoformat()
            except ValueError:
                return None
    return None


class _TextExtractor(HTMLParser):
    _BLOCK = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr"}
    _SKIP = {"script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag in self._SKIP:
            self._skip_depth += 1
        elif tag == "li":
            self.parts.append("\n• ")
        elif tag in self._BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag in self._BLOCK:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)


def html_to_text(raw: Any, limit: int = MAX_DESCRIPTION_CHARS) -> str:
    """Strips upstream HTML to plain text so the frontend never injects third-party markup."""
    if not isinstance(raw, str) or not raw.strip():
        return ""
    parser = _TextExtractor()
    try:
        parser.feed(raw)
        parser.close()
        text = "".join(parser.parts)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", raw)
    text = unescape(text).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0].rstrip() + "…"
    return text


def is_safe_himalayas_url(url: Any, *, https_only: bool = True) -> bool:
    """Apply links must be https URLs on himalayas.app (the docs require applicationLink)."""
    if not isinstance(url, str) or not url.strip():
        return False
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return False
    return host == HIMALAYAS_HOST or host.endswith("." + HIMALAYAS_HOST)


def _safe_https_url(url: Any) -> Optional[str]:
    if isinstance(url, str) and url.strip():
        try:
            if urlparse(url.strip()).scheme == "https":
                return url.strip()
        except ValueError:
            pass
    return None


def _to_float(val: Any) -> Optional[float]:
    if val is None or isinstance(val, bool):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _str_list(val: Any) -> List[str]:
    if isinstance(val, list):
        return [str(v).strip() for v in val if v and str(v).strip()]
    if isinstance(val, str) and val.strip():
        return [val.strip()]
    return []


def map_job(raw: Dict[str, Any]) -> Optional[RecommendedJobItem]:
    """Maps one Himalayas job. Returns None when it lacks a title or a valid apply link."""
    title = str(raw.get("title") or "").strip()
    apply_url = str(raw.get("applicationLink") or "").strip()
    if not title or not is_safe_himalayas_url(apply_url):
        return None

    # The search payload has no numeric id; `guid` is the job's canonical URL.
    job_id = str(raw.get("guid") or raw.get("id") or apply_url).strip()
    description = html_to_text(raw.get("description")) or html_to_text(raw.get("excerpt"))

    return RecommendedJobItem(
        id=job_id,
        title=title,
        company=str(raw.get("companyName") or "").strip() or "Company not listed",
        company_slug=(str(raw["companySlug"]).strip() or None) if raw.get("companySlug") else None,
        company_logo=_safe_https_url(raw.get("companyLogo")),
        eligible_countries=_str_list(raw.get("locationRestrictions")),
        employment_type=(str(raw["employmentType"]).strip() or None) if raw.get("employmentType") else None,
        seniority=_str_list(raw.get("seniority")),
        salary_min=_to_float(raw.get("minSalary")),
        salary_max=_to_float(raw.get("maxSalary")),
        salary_currency=(str(raw["currency"]).strip() or None) if raw.get("currency") else None,
        salary_period=(str(raw["salaryPeriod"]).strip() or None) if raw.get("salaryPeriod") else None,
        description=description,
        posted_at=parse_unix_timestamp(raw.get("pubDate")),
        expires_at=parse_unix_timestamp(raw.get("expiryDate")),
        apply_url=apply_url,
    )


# ─── Skill matching ───────────────────────────────────────────────────────────


def _skill_pattern(skill: str) -> "re.Pattern[str]":
    # Boundaries that tolerate symbols in names such as "C++" or "Node.js".
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(skill) + r"(?![A-Za-z0-9])", re.IGNORECASE)


def _human_join(items: List[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def compute_match(job: RecommendedJobItem, skills: Iterable[str]) -> Optional[JobMatch]:
    """Keyword overlap between a student's skills and the job text. None if no skills known."""
    clean: List[str] = []
    seen = set()
    for s in skills:
        name = str(s).strip()
        if name and name.lower() not in seen and len(name) <= 60:
            seen.add(name.lower())
            clean.append(name)
    if not clean:
        return None
    haystack = f"{job.title}\n{job.description}"
    matched = [s for s in clean if _skill_pattern(s).search(haystack)]
    denominator = min(len(clean), 6)
    score = min(100, round(100 * len(matched) / denominator))
    if matched:
        shown = matched[:4]
        reason = f"Matches your {_human_join(shown)} skill{'s' if len(shown) > 1 else ''}."
    else:
        reason = "None of your saved skills appear in this listing."
    return JobMatch(score=score, matched_skills=matched, reason=reason)


def apply_matches(response: RecommendedJobsResponse, skills: List[str]) -> RecommendedJobsResponse:
    """Returns a copy of the response with per-job match estimates (cache stays user-neutral)."""
    if not skills:
        return response
    jobs = [j.model_copy(update={"match": compute_match(j, skills)}) for j in response.jobs]
    return response.model_copy(update={"jobs": jobs, "match_method": MATCH_METHOD})


# ─── Upstream client ──────────────────────────────────────────────────────────


class HimalayasService:
    """Async client + mapper for the Himalayas Remote Jobs public search API."""

    def __init__(
        self,
        base_url: str = HIMALAYAS_SEARCH_API_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        cache_ttl: float = CACHE_TTL_SECONDS,
    ):
        self.base_url = base_url
        self.timeout = httpx.Timeout(timeout, connect=CONNECT_TIMEOUT_SECONDS)
        self.cache_ttl = cache_ttl
        self._cache: Dict[Tuple, Tuple[float, RecommendedJobsResponse]] = {}

    def clear_cache(self) -> None:
        self._cache.clear()

    def _build_params(
        self,
        q: Optional[str] = None,
        country: Optional[str] = None,
        page: int = 1,
        employment_type: Optional[str] = None,
        seniority: Optional[str] = None,
        worldwide: Optional[bool] = None,
        exclude_worldwide: Optional[bool] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if q and q.strip():
            params["q"] = q.strip()
        if country and country.strip():
            params["country"] = country.strip().upper()
        if page and page > 0:
            params["page"] = page
        if employment_type and employment_type.strip():
            params["employment_type"] = employment_type.strip()
        if seniority and seniority.strip():
            params["seniority"] = seniority.strip()
        if worldwide is True:
            params["worldwide"] = "true"
        if exclude_worldwide is True:
            params["exclude_worldwide"] = "true"
        return params

    async def _request(self, params: Dict[str, Any], client: Optional[httpx.AsyncClient]) -> httpx.Response:
        headers = {
            "User-Agent": "CareerOS/1.0 (student job recommendations)",
            "Accept": "application/json",
        }
        try:
            if client is not None:
                return await client.get(self.base_url, params=params, headers=headers)
            async with httpx.AsyncClient(timeout=self.timeout) as local_client:
                return await local_client.get(self.base_url, params=params, headers=headers)
        except httpx.TimeoutException as exc:
            logger.warning("Himalayas request timed out: %s", type(exc).__name__)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="The job source took too long to respond. Please try again.",
            )
        except httpx.HTTPError as exc:
            logger.error("Himalayas request failed: %s", type(exc).__name__)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to reach the job source right now. Please try again.",
            )

    @staticmethod
    def _bad_gateway(detail: str = "The job source returned an unexpected response.") -> HTTPException:
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)

    async def fetch_recommended_jobs(
        self,
        q: Optional[str] = None,
        country: Optional[str] = None,
        page: int = 1,
        employment_type: Optional[str] = None,
        seniority: Optional[str] = None,
        worldwide: Optional[bool] = None,
        exclude_worldwide: Optional[bool] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> RecommendedJobsResponse:
        params = self._build_params(q, country, page, employment_type, seniority, worldwide, exclude_worldwide)

        cache_key = tuple(sorted((k, str(v).lower()) for k, v in params.items()))
        cached = self._cache.get(cache_key)
        if cached and cached[0] > time.monotonic():
            return cached[1]

        resp = await self._request(params, client)

        if resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            logger.warning("Himalayas rate limit hit (429)")
            headers = {}
            retry_after = resp.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                headers["Retry-After"] = retry_after
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="The job source is rate limiting requests. Please try again in a minute.",
                headers=headers or None,
            )
        if resp.status_code != status.HTTP_200_OK:
            logger.error("Himalayas returned HTTP %s", resp.status_code)
            raise self._bad_gateway(
                "The job source is temporarily unavailable. Please try again."
                if resp.status_code >= 500
                else "The job source rejected the request."
            )

        try:
            data = resp.json()
        except ValueError:
            logger.error("Himalayas returned non-JSON content")
            raise self._bad_gateway()

        raw_jobs = data.get("jobs") if isinstance(data, dict) else None
        if not isinstance(raw_jobs, list):
            logger.error("Himalayas payload missing a 'jobs' list")
            raise self._bad_gateway()

        total_raw = data.get("totalCount")
        try:
            total = max(0, int(total_raw)) if total_raw is not None else len(raw_jobs)
        except (TypeError, ValueError):
            total = len(raw_jobs)

        jobs: List[RecommendedJobItem] = []
        for raw_job in raw_jobs:
            if not isinstance(raw_job, dict):
                continue
            try:
                mapped = map_job(raw_job)
            except Exception:  # one bad listing must not hide the rest
                logger.debug("Skipping unmappable Himalayas listing", exc_info=True)
                continue
            if mapped:
                jobs.append(mapped)

        result = RecommendedJobsResponse(
            filters=JobFilters(
                query=params.get("q"),
                country=params.get("country"),
                page=page,
                seniority=params.get("seniority"),
                employment_type=params.get("employment_type"),
                worldwide=True if worldwide else None,
                exclude_worldwide=True if exclude_worldwide else None,
            ),
            total=total,
            page=page,
            page_size=PAGE_SIZE,
            total_pages=-(-total // PAGE_SIZE),
            jobs=jobs,
        )

        if len(self._cache) >= CACHE_MAX_ENTRIES:
            now = time.monotonic()
            self._cache = {k: v for k, v in self._cache.items() if v[0] > now}
            if len(self._cache) >= CACHE_MAX_ENTRIES:
                self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = (time.monotonic() + self.cache_ttl, result)
        return result


_himalayas_service = HimalayasService()


def get_himalayas_service() -> HimalayasService:
    """Dependency provider for HimalayasService."""
    return _himalayas_service
