"""Mocked tests for GET /api/v1/jobs/recommended (Himalayas). No live network calls."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.main import app
from app.modules.jobs.service import (
    HimalayasService,
    compute_match,
    get_himalayas_service,
    html_to_text,
    is_safe_himalayas_url,
    map_job,
    parse_unix_timestamp,
)

URL = "/api/v1/jobs/recommended"
REQ = httpx.Request("GET", "https://himalayas.app/jobs/api/search")

UPSTREAM_JOB = {
    "title": "Senior Python Developer",
    "excerpt": "Short excerpt",
    "companyName": "TechCorp",
    "companySlug": "techcorp",
    "companyLogo": "https://cdn-images.himalayas.app/logo",
    "employmentType": "Full Time",
    "minSalary": 85000,
    "maxSalary": 120000,
    "salaryPeriod": "annual",
    "seniority": ["Senior"],
    "currency": "USD",
    "locationRestrictions": ["India"],
    "timezoneRestrictions": [5.5],
    "categories": ["Python-Developer"],
    "parentCategories": ["Developer"],
    "description": "<h3>Role</h3><p>Build APIs with <strong>Python</strong> &amp; SQL.</p>"
    "<ul><li>FastAPI</li></ul><script>alert(1)</script>",
    "pubDate": 1792414811,
    "expiryDate": 1797363319,
    "applicationLink": "https://himalayas.app/companies/techcorp/jobs/senior-python-developer?utm_source=api",
    "guid": "https://himalayas.app/companies/techcorp/jobs/senior-python-developer",
}


def upstream(jobs, total=None):
    return httpx.Response(
        200,
        json={"jobs": jobs, "totalCount": len(jobs) if total is None else total, "limit": 20},
        request=REQ,
    )


@pytest.fixture
def fresh_service():
    service = HimalayasService()
    app.dependency_overrides[get_himalayas_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_himalayas_service, None)


@pytest.fixture(autouse=True)
def auth_and_db():
    fake_user = type("U", (), {"id": "00000000-0000-0000-0000-000000000001"})()
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_db] = lambda: None
    with patch("app.modules.jobs.router.load_student_skills", new=AsyncMock(return_value=[])) as m:
        yield m
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


async def call(path=URL, mock_response=None, side_effect=None):
    mock_client = AsyncMock()
    if side_effect:
        mock_client.get.side_effect = side_effect
    else:
        mock_client.get.return_value = mock_response
    cm = AsyncMock()
    cm.__aenter__.return_value = mock_client
    cm.__aexit__.return_value = None
    with patch("app.modules.jobs.service.httpx.AsyncClient", return_value=cm):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get(path)
    return resp, mock_client


# 1. success + mapping from the real upstream schema
@pytest.mark.asyncio
async def test_success_maps_real_schema(fresh_service):
    resp, client = await call(f"{URL}?q=python&country=in&page=1", upstream([UPSTREAM_JOB], total=41))
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] and body["source"] == "Himalayas"
    assert body["attribution"]["url"] == "https://himalayas.app"
    assert body["total"] == 41 and body["page_size"] == 20 and body["total_pages"] == 3
    assert body["filters"]["country"] == "IN" and body["filters"]["query"] == "python"
    job = body["jobs"][0]
    assert job["id"] == UPSTREAM_JOB["guid"]
    assert job["title"] == "Senior Python Developer" and job["company"] == "TechCorp"
    assert job["remote"] is True and job["location"] == "Remote"
    assert job["eligible_countries"] == ["India"]
    assert job["salary_min"] == 85000 and job["salary_currency"] == "USD"
    assert job["apply_url"] == UPSTREAM_JOB["applicationLink"]
    assert job["posted_at"].startswith("2026-")
    assert "<" not in job["description"] and "alert" not in job["description"]
    assert "Python & SQL" in job["description"] and "• FastAPI" in job["description"]
    assert client.get.call_args.kwargs["params"] == {"q": "python", "country": "IN", "page": 1}


# 2. empty results
@pytest.mark.asyncio
async def test_empty_results(fresh_service):
    resp, _ = await call(URL, upstream([], total=0))
    body = resp.json()
    assert resp.status_code == 200 and body["jobs"] == [] and body["total"] == 0 and body["total_pages"] == 0


# 3. missing optional fields; listings without a valid apply link are dropped
@pytest.mark.asyncio
async def test_missing_optional_fields(fresh_service):
    minimal = {"title": "Dev", "applicationLink": "https://himalayas.app/companies/x/jobs/dev"}
    bad_link = {"title": "Evil", "applicationLink": "https://evil.example.com/apply"}
    js_link = {"title": "JS", "applicationLink": "javascript:alert(1)"}
    resp, _ = await call(URL, upstream([minimal, bad_link, js_link, "junk", None], total=5))
    jobs = resp.json()["jobs"]
    assert len(jobs) == 1
    j = jobs[0]
    assert j["company"] == "Company not listed" and j["company_logo"] is None
    assert j["employment_type"] is None and j["salary_min"] is None and j["posted_at"] is None
    assert j["seniority"] == [] and j["eligible_countries"] == [] and j["description"] == ""


# 4. invalid upstream payloads
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="<html>nope</html>", request=REQ),
        httpx.Response(200, json={"nojobs": True}, request=REQ),
        httpx.Response(200, json=["x"], request=REQ),
        httpx.Response(200, json={"jobs": "x"}, request=REQ),
        httpx.Response(404, text="gone", request=REQ),
    ],
)
async def test_invalid_upstream_response(fresh_service, response):
    resp, _ = await call(URL, response)
    assert resp.status_code == 502
    assert "html" not in resp.text.lower() and "Traceback" not in resp.text


# 5. timeout / network failure
@pytest.mark.asyncio
async def test_upstream_timeout(fresh_service):
    resp, _ = await call(URL, side_effect=httpx.ReadTimeout("slow", request=REQ))
    assert resp.status_code == 504


@pytest.mark.asyncio
async def test_upstream_network_error_hides_internals(fresh_service):
    resp, _ = await call(URL, side_effect=httpx.ConnectError("dns secret-host", request=REQ))
    assert resp.status_code == 502 and "secret-host" not in resp.text


# 6. rate limit
@pytest.mark.asyncio
async def test_rate_limited(fresh_service):
    resp, _ = await call(URL, httpx.Response(429, headers={"Retry-After": "30"}, request=REQ))
    assert resp.status_code == 429 and resp.headers.get("Retry-After") == "30"


# 7. upstream server error
@pytest.mark.asyncio
@pytest.mark.parametrize("code", [500, 503])
async def test_upstream_server_error(fresh_service, code):
    resp, _ = await call(URL, httpx.Response(code, text="boom", request=REQ))
    assert resp.status_code == 502 and "boom" not in resp.text


# 8. invalid query parameters never reach the upstream
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "qs",
    [
        "page=0",
        "page=abc",
        "page=251",
        "country=IND",
        "country=1!",
        "seniority=lead",
        "employment_type=weird",
        "q=" + "x" * 101,
    ],
)
async def test_invalid_query_params(fresh_service, qs):
    resp, client = await call(f"{URL}?{qs}", upstream([]))
    assert resp.status_code == 422
    client.get.assert_not_called()


# 9. pagination and filters forwarded
@pytest.mark.asyncio
async def test_pagination(fresh_service):
    resp, client = await call(
        f"{URL}?page=3&seniority=entry-level&exclude_worldwide=true&country=IN",
        upstream([UPSTREAM_JOB], total=61),
    )
    body = resp.json()
    assert body["page"] == 3 and body["total_pages"] == 4
    assert client.get.call_args.kwargs["params"] == {
        "country": "IN",
        "page": 3,
        "seniority": "entry-level",
        "exclude_worldwide": "true",
    }


# authentication is enforced
@pytest.mark.asyncio
async def test_requires_authentication(fresh_service):
    app.dependency_overrides.pop(get_current_user, None)
    resp, client = await call(URL, upstream([]))
    assert resp.status_code == 401
    client.get.assert_not_called()


# caching
@pytest.mark.asyncio
async def test_repeated_requests_are_cached(fresh_service):
    _, c1 = await call(f"{URL}?q=python", upstream([UPSTREAM_JOB]))
    _, c2 = await call(f"{URL}?q=PYTHON", upstream([UPSTREAM_JOB]))
    assert c1.get.call_count == 1 and c2.get.call_count == 0


@pytest.mark.asyncio
async def test_errors_are_not_cached(fresh_service):
    await call(URL, httpx.Response(500, request=REQ))
    resp, _ = await call(URL, upstream([UPSTREAM_JOB]))
    assert resp.status_code == 200


# skill matching
@pytest.mark.asyncio
async def test_match_estimate_when_skills_exist(fresh_service, auth_and_db):
    auth_and_db.return_value = ["Python", "SQL", "Rust"]
    resp, _ = await call(URL, upstream([UPSTREAM_JOB]))
    body = resp.json()
    match = body["jobs"][0]["match"]
    assert match["matched_skills"] == ["Python", "SQL"]
    assert match["score"] == 67 and match["reason"] == "Matches your Python and SQL skills."
    assert "not a hiring probability" in body["match_method"]


@pytest.mark.asyncio
async def test_no_match_without_skills(fresh_service):
    resp, _ = await call(URL, upstream([UPSTREAM_JOB]))
    body = resp.json()
    assert body["jobs"][0]["match"] is None and body["match_method"] is None


def test_compute_match_symbol_skills_and_word_boundaries():
    job = map_job({**UPSTREAM_JOB, "description": "We use C++ and Java daily.", "title": "Dev"})
    m = compute_match(job, ["C++", "Java", "JavaScript", "Go"])
    assert m.matched_skills == ["C++", "Java"]
    assert compute_match(job, []) is None


def test_helpers():
    assert parse_unix_timestamp(None) is None and parse_unix_timestamp("abc") is None
    assert parse_unix_timestamp(0) == "1970-01-01T00:00:00+00:00"
    assert html_to_text("<p>a&nbsp;b</p><style>x{}</style>") == "a b"
    assert is_safe_himalayas_url("https://himalayas.app/x")
    assert is_safe_himalayas_url("https://www.himalayas.app/x")
    for bad in [
        "http://himalayas.app/x",
        "https://himalayas.app.evil.com/x",
        "https://user@himalayas.app/x",
        "https://evilhimalayas.app/x",
        "",
        None,
    ]:
        assert not is_safe_himalayas_url(bad)
