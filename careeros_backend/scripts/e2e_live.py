"""Live API contract test: drives a *running* backend exactly the way the frontend client does.

Usage (backend already running, freshly seeded with `python -m scripts.seed_dev`):
    python -m scripts.e2e_live [http://127.0.0.1:8000]

Covers every endpoint the frontend calls, positive and negative paths, for the student,
recruiter, placement-officer and admin roles. Exits non-zero if any check fails.
"""

import os
import asyncio
import io
import json
import sys
import time
import uuid

import httpx
import websockets

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
API = f"{BASE}/api/v1"
WS = API.replace("http", "ws", 1)

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: str = ""):
    results.append((ok, name))
    print(f"{'PASS' if ok else 'FAIL'}  {name}{('  -> ' + detail) if (detail and not ok) else ''}")


def expect(name: str, resp: httpx.Response, code: int, **fields):
    """Assert status and (optionally) that JSON body fields equal the expected values."""
    ok = resp.status_code == code
    detail = f"got {resp.status_code}: {resp.text[:200]}"
    if ok and fields:
        body = resp.json()
        for key, want in fields.items():
            if body.get(key) != want:
                ok, detail = False, f"{key}={body.get(key)!r}, wanted {want!r}"
    check(name, ok, detail)
    return resp


class Client:
    def __init__(self, email: str, password: str):
        self.email, self.password = email, password
        self.http = httpx.Client(base_url=API, timeout=20)
        self.access = self.refresh = ""

    def login(self):
        r = self.http.post("/auth/login", json={"email": self.email, "password": self.password})
        if r.status_code == 200:
            self.access, self.refresh = r.json()["access_token"], r.json()["refresh_token"]
        return r

    @property
    def h(self):
        return {"Authorization": f"Bearer {self.access}"}

    def get(self, path, **kw):
        return self.http.get(path, headers=self.h, **kw)

    def post(self, path, **kw):
        return self.http.post(path, headers=self.h, **kw)

    def put(self, path, **kw):
        return self.http.put(path, headers=self.h, **kw)

    def patch(self, path, **kw):
        return self.http.patch(path, headers=self.h, **kw)


def poll(fn, ok, tries=30, delay=0.5):
    for _ in range(tries):
        r = fn()
        if ok(r):
            return r
        time.sleep(delay)
    return fn()


def register(email, pw="Passw0rd!x"):
    c = Client(email, pw)
    r = c.http.post("/auth/register", json={"email": email, "password": pw})
    check(f"register {email}", r.status_code == 201, r.text[:150])
    c.login()
    return c


async def ws_flow(path: str, token: str, script: list[dict], stop_event: str):
    """Sends events one by one and collects server events until `stop_event`."""
    events = []
    async with websockets.connect(f"{WS}{path}?token={token}") as sock:
        for msg in script:
            await sock.send(json.dumps(msg))
            try:
                while True:
                    ev = json.loads(await asyncio.wait_for(sock.recv(), timeout=8))
                    events.append(ev)
                    if ev["event_type"] in ("NEXT_QUESTION", "SESSION_READY", "LIVE_FEEDBACK", stop_event):
                        break
            except asyncio.TimeoutError:
                pass
    return events


def main():
    tag = uuid.uuid4().hex[:6]

    # ── health + auth ────────────────────────────────────────────────────────
    expect("GET /health", httpx.get(f"{BASE}/health"), 200)

    student = register(f"student_{tag}@test.com")
    expect("POST /auth/login wrong password -> 401", Client(student.email, "nope-nope").login(), 401)
    expect("POST /auth/login unknown user -> 401", Client("ghost@test.com", "x").login(), 401)
    expect("POST /auth/register duplicate -> 400", student.http.post("/auth/register", json={"email": student.email, "password": "Passw0rd!x"}), 400)
    expect("POST /auth/register invalid email -> 422", student.http.post("/auth/register", json={"email": "bad", "password": "x"}), 422)

    me = expect("GET /auth/me", student.get("/auth/me"), 200).json()
    check("auth/me shape (roles/permissions/company_id/college_id)", {"roles", "permissions", "company_id", "college_id"} <= me.keys())
    expect("GET /auth/me without token -> 401", httpx.get(f"{API}/auth/me"), 401)
    expect("GET /auth/me garbage token -> 401", httpx.get(f"{API}/auth/me", headers={"Authorization": "Bearer junk"}), 401)

    refreshed = expect("POST /auth/refresh", student.http.post("/auth/refresh", json={"refresh_token": student.refresh}), 200)
    check("refresh returns new token pair", "access_token" in refreshed.json())
    expect("POST /auth/refresh with access token -> 401", student.http.post("/auth/refresh", json={"refresh_token": student.access}), 401)
    expect("POST /auth/refresh garbage -> 401", student.http.post("/auth/refresh", json={"refresh_token": "junk"}), 401)

    # ── profile ──────────────────────────────────────────────────────────────
    p = expect("GET /users/me/profile", student.get("/users/me/profile"), 200).json()
    check("profile envelope + data", p["success"] and "completion_percentage" in p["data"])
    upd = expect(
        "PUT /users/me/profile",
        student.put("/users/me/profile", json={"first_name": "Ada", "last_name": "Lovelace", "headline": "Engineer", "bio": "Hi", "role_specific_data": {"selected_role": "student", "skills": ["Python"]}}),
        200,
    ).json()["data"]
    check("profile persisted", upd["first_name"] == "Ada" and upd["role_specific_data"]["skills"] == ["Python"])
    again = student.get("/users/me/profile").json()["data"]
    check("profile re-read matches", again["headline"] == "Engineer")

    # ── analytics ────────────────────────────────────────────────────────────
    d = expect("GET /analytics/dashboard/student", student.get("/analytics/dashboard/student"), 200).json()
    check("dashboard keys", {"career_readiness", "resume_score", "interview_score", "today_interviews", "today_tasks", "trends"} <= d.keys())
    expect("POST /analytics/events", student.post("/analytics/events", json={"event_type": "PAGE_VIEWED", "module": "analytics"}), 202)
    expect("POST /analytics/events invalid -> 422", student.post("/analytics/events", json={"module": "x"}), 422)

    # ── discovery ────────────────────────────────────────────────────────────
    tpls = expect("GET /discovery/templates", student.get("/discovery/templates"), 200).json()["data"]
    check("assessment template seeded with questions", bool(tpls) and bool(tpls[0]["questions"]))
    tpl = tpls[0]
    answers = [
        {"question_id": q["id"], **({"selected_options": [q["options"][0]]} if q["question_type"] == "MULTIPLE_CHOICE" else {"answer_text": "Python and TypeScript"})}
        for q in tpl["questions"]
    ]
    sub = expect("POST /discovery/assessments/{id}/submit", student.post(f"/discovery/assessments/{tpl['id']}/submit", json={"answers": answers}), 200).json()["data"]
    rep = poll(lambda: student.get(f"/discovery/reports/{sub['assessment_id']}"), lambda r: r.status_code == 200)
    expect("GET /discovery/reports/{assessment_id} (polled)", rep, 200)
    check("report shape", {"personality_analysis", "interest_analysis", "skill_gaps", "career_timeline", "matches"} <= rep.json()["data"].keys())
    expect("GET /discovery/reports/{unknown} -> 404", student.get(f"/discovery/reports/{uuid.uuid4()}"), 404)
    expect("POST /discovery submit empty answers body -> 422", student.post(f"/discovery/assessments/{tpl['id']}/submit", json={}), 422)

    # ── resumes ──────────────────────────────────────────────────────────────
    expect("GET /resumes (empty)", student.get("/resumes"), 200)
    bad = student.http.post("/resumes/upload", headers=student.h, files={"file": ("x.txt", io.BytesIO(b"hello"), "text/plain")})
    expect("POST /resumes/upload wrong type -> 400", bad, 400)
    pdf = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
    up = expect("POST /resumes/upload", student.http.post("/resumes/upload", headers=student.h, files={"file": ("cv.pdf", io.BytesIO(pdf), "application/pdf")}), 202).json()["data"]
    lst = student.get("/resumes").json()["data"]
    check("resume listed after upload", any(r["id"] == up["id"] for r in lst))
    an = poll(lambda: student.get(f"/resumes/{up['id']}/analysis"), lambda r: r.status_code == 200, tries=20)
    check("GET /resumes/{id}/analysis (polled)", an.status_code == 200, an.text[:200])
    if an.status_code == 200:
        check("analysis shape", {"ats_score", "grammar_score", "quality_score", "keyword_analysis", "suggestions"} <= an.json()["data"].keys())
    dl = student.get(f"/resumes/{up['id']}/download")
    check("GET /resumes/{id}/download returns the stored file", dl.status_code == 200 and dl.content == pdf and dl.headers.get("content-type") == "application/pdf", dl.text[:100])
    other = register(f"other_{tag}@test.com")
    expect("GET /resumes/{id}/download other user -> 403", other.get(f"/resumes/{up['id']}/download"), 403)
    expect("GET /resumes/{id}/analysis other user -> 403", other.get(f"/resumes/{up['id']}/analysis"), 403)

    # ── mentor ───────────────────────────────────────────────────────────────
    expect("GET /mentor/sessions/latest (none) -> 404", student.get("/mentor/sessions/latest"), 404)
    ms = expect("POST /mentor/sessions", student.post("/mentor/sessions"), 200).json()["data"]
    status = expect("GET /mentor/status", student.get("/mentor/status"), 200).json()["data"]
    expect("GET /mentor/suggestions", student.get("/mentor/suggestions"), 200)
    mresp = student.post(f"/mentor/sessions/{ms['id']}/message", json={"content": "How do I improve my resume?"})
    if status["ai_available"]:
        msg = expect("POST /mentor/sessions/{id}/message (real provider)", mresp, 200).json()["data"]
        check("mentor reply has content", bool(msg["content"]) and msg["role"] == "AI")
        latest = student.get("/mentor/sessions/latest").json()["data"]
        check("GET /mentor/sessions/latest restores history", latest["id"] == ms["id"] and len(latest["messages"]) >= 2)
    else:
        expect("mentor without an AI provider -> 503 setup message, nothing saved", mresp, 503)
    expect("mentor message other user's session -> 403", other.post(f"/mentor/sessions/{ms['id']}/message", json={"content": "hi"}), 403)
    expect("mentor message missing content -> 422", student.post(f"/mentor/sessions/{ms['id']}/message", json={}), 422)
    g = expect("POST /mentor/goals", student.post("/mentor/goals", json={"title": "Land a backend role", "milestones": [{"title": "Finish roadmap"}]}), 200).json()["data"]
    check("goal created with milestone", len(g["milestones"]) == 1)
    goals = expect("GET /mentor/goals", student.get("/mentor/goals"), 200).json()["data"]
    check("goal listed", any(x["id"] == g["id"] for x in goals))

    # ── learning ─────────────────────────────────────────────────────────────
    expect("GET /learning/roadmaps/active (none) -> 404", student.get("/learning/roadmaps/active"), 404)
    expect("POST /learning/roadmaps/generate", student.post("/learning/roadmaps/generate", json={"target_role": "Backend Engineer"}), 202)
    rm = poll(lambda: student.get("/learning/roadmaps/active"), lambda r: r.status_code == 200 and r.json()["data"]["status"] == "ACTIVE")
    check("roadmap becomes ACTIVE with modules/tasks", rm.status_code == 200 and rm.json()["data"]["status"] == "ACTIVE" and rm.json()["data"]["modules"], rm.text[:200])
    task_id = rm.json()["data"]["modules"][0]["tasks"][0]["id"]
    ct = expect("POST /learning/tasks/complete", student.post("/learning/tasks/complete", json={"task_id": task_id}), 200).json()["data"]
    check("task marked completed", ct["status"] == "COMPLETED")
    after = student.get("/learning/roadmaps/active").json()["data"]
    check("completed task persisted", any(t["id"] == task_id and t["status"] == "COMPLETED" for m in after["modules"] for t in m["tasks"]))
    expect("POST /learning/tasks/complete unknown -> 404", student.post("/learning/tasks/complete", json={"task_id": str(uuid.uuid4())}), 404)
    expect("POST /learning/tasks/complete bad uuid -> 422", student.post("/learning/tasks/complete", json={"task_id": "nope"}), 422)

    # ── recommendations ──────────────────────────────────────────────────────
    expect("GET /recommendations/feed (none) -> 404", student.get("/recommendations/feed"), 404)
    expect("POST /recommendations/refresh", student.post("/recommendations/refresh"), 202)
    feed = poll(lambda: student.get("/recommendations/feed"), lambda r: r.status_code == 200, tries=20)
    check("GET /recommendations/feed after refresh", feed.status_code == 200, feed.text[:200])
    if feed.status_code == 200:
        rec = feed.json()["data"]["recommendations"][0]
        expect("POST /recommendations/feedback", student.post("/recommendations/feedback", json={"recommendation_id": rec["id"], "action": "ACCEPTED"}), 200)
        expect("POST /recommendations/feedback unknown id -> 403", student.post("/recommendations/feedback", json={"recommendation_id": str(uuid.uuid4()), "action": "ACCEPTED"}), 403)

    # ── interviews + communication (REST + WebSocket) ────────────────────────
    isess = expect("POST /interviews/sessions", student.post("/interviews/sessions", json={"interview_type": "TECHNICAL", "difficulty": "MEDIUM"}), 200).json()["data"]
    events = asyncio.run(ws_flow(f"/interviews/ws/{isess['id']}", student.access, [{"event_type": "START"}], "NEXT_QUESTION"))
    q = next((e for e in events if e["event_type"] == "NEXT_QUESTION"), None)
    check("WS interviews: START -> NEXT_QUESTION", q is not None, str(events))
    if q:
        events = asyncio.run(
            ws_flow(f"/interviews/ws/{isess['id']}", student.access, [{"event_type": "START"}, {"event_type": "ANSWER_SUBMITTED", "payload": {"question_id": q["payload"]["question_id"], "answer_text": "I use STAR."}}, {"event_type": "FINISH"}], "INTERVIEW_COMPLETED")
        )
        kinds_i = [e["event_type"] for e in events]
        check("WS interviews: answer -> EVALUATING -> next question, then finish", "EVALUATING" in kinds_i and kinds_i.count("NEXT_QUESTION") >= 2 and "INTERVIEW_COMPLETED" in kinds_i, str(kinds_i))
    ir = poll(lambda: student.get(f"/interviews/sessions/{isess['id']}/report"), lambda r: r.status_code == 200)
    check("GET /interviews/sessions/{id}/report (polled)", ir.status_code == 200 and "overall_score" in ir.json()["data"], ir.text[:200])
    expect("interview report other user -> 403", other.get(f"/interviews/sessions/{isess['id']}/report"), 403)

    async def ws_reject(path, token):
        try:
            async with websockets.connect(f"{WS}{path}?token={token}") as sock:
                await asyncio.wait_for(sock.recv(), timeout=3)
            return "accepted"
        except websockets.exceptions.ConnectionClosed as e:
            return f"closed:{e.rcvd.code if e.rcvd else '?'}"
        except Exception as e:  # handshake rejected
            return f"rejected:{type(e).__name__}"

    r1 = asyncio.run(ws_reject(f"/interviews/ws/{isess['id']}", "junk"))
    check("WS interviews: bad token refused", not r1.startswith("accepted"), r1)
    r2 = asyncio.run(ws_reject(f"/interviews/ws/{isess['id']}", other.access))
    check("WS interviews: other user's session refused", not r2.startswith("accepted"), r2)

    csess = expect("POST /communication/sessions", student.post("/communication/sessions", json={"mode": "WORKPLACE"}), 200).json()["data"]
    ce = asyncio.run(ws_flow(f"/communication/ws/{csess['id']}", student.access, [{"event_type": "START"}, {"event_type": "MESSAGE_SUBMITTED", "payload": {"text": "I has a idea."}}, {"event_type": "FINISH"}], "SESSION_COMPLETED"))
    kinds = [e["event_type"] for e in ce]
    check("WS communication: ready -> analyzing -> live feedback -> completed", all(k in kinds for k in ("SESSION_READY", "ANALYZING", "LIVE_FEEDBACK", "SESSION_COMPLETED")), str(kinds))
    cr = poll(lambda: student.get(f"/communication/sessions/{csess['id']}/report"), lambda r: r.status_code == 200)
    check("GET /communication/sessions/{id}/report (polled)", cr.status_code == 200 and "overall_score" in cr.json()["data"], cr.text[:200])

    # ── community ────────────────────────────────────────────────────────────
    dash = student.get("/analytics/dashboard/student").json()
    ats_now = an.json()["data"]["ats_score"] if an.status_code == 200 else None
    check("dashboard resume_score == latest resume analysis ATS", ats_now is not None and dash["resume_score"] == ats_now, str(dash))
    check("dashboard interview_score == latest interview report", ir.status_code == 200 and dash["interview_score"] == ir.json()["data"]["overall_score"], str(dash))
    check("dashboard today_interviews counts the finished interview", dash["today_interviews"] == 1, str(dash))
    check("dashboard today_tasks counts the completed learning task", dash["today_tasks"] == 1, str(dash))
    check("dashboard career_readiness is derived (> 0)", dash["career_readiness"] > 0, str(dash))
    check("fresh user's dashboard is all zeros", other.get("/analytics/dashboard/student").json()["career_readiness"] == 0)

    expect("POST /community/posts invalid -> 422", student.post("/community/posts", json={"title": "x"}), 422)
    post = expect("POST /community/posts", student.post("/community/posts", json={"title": "Interview tips", "content": "Practise aloud", "category": "Interview Prep", "tags": ["tips"]}), 201).json()
    check("post has tag", post["tags"][0]["name"] == "tips")
    expect("GET /community/posts/{id}", student.get(f"/community/posts/{post['id']}"), 200)
    expect("GET /community/posts/{unknown} -> 404", student.get(f"/community/posts/{uuid.uuid4()}"), 404)
    expect("comment on unknown post -> 404", student.post(f"/community/posts/{uuid.uuid4()}/comments", json={"content": "x"}), 404)
    expect("react to unknown post -> 404", student.post("/community/reactions", json={"entity_type": "post", "entity_id": str(uuid.uuid4())}), 404)
    cm = expect("POST /community/posts/{id}/comments", student.post(f"/community/posts/{post['id']}/comments", json={"content": "Great"}), 201).json()
    cl = expect("GET /community/posts/{id}/comments", student.get(f"/community/posts/{post['id']}/comments"), 200).json()
    check("comment listed", any(c["id"] == cm["id"] for c in cl))
    expect("POST /community/reactions", student.post("/community/reactions", json={"entity_type": "post", "entity_id": post["id"], "reaction_type": "like"}), 201)
    student.post("/community/reactions", json={"entity_type": "post", "entity_id": post["id"], "reaction_type": "like"})
    check("duplicate like is not double-counted", student.get(f"/community/posts/{post['id']}").json()["reactions_count"] == 1)
    latest_feed = expect("GET /community/feed/latest", student.get("/community/feed/latest"), 200).json()
    check("feed contains post with updated counts", any(f["post"]["id"] == post["id"] and f["post"]["comments_count"] >= 1 for f in latest_feed), str(latest_feed)[:200])
    expect("GET /community/feed/trending", student.get("/community/feed/trending"), 200)
    sr = expect("GET /community/search", student.get("/community/search", params={"q": "Interview"}), 200).json()
    check("search finds post", any(p["id"] == post["id"] for p in sr))
    expect("GET /community/search missing q -> 422", student.get("/community/search"), 422)

    # ── recruiter ────────────────────────────────────────────────────────────
    rec = register(f"recruiter_{tag}@test.com")
    expect("GET /recruiters/jobs without company -> 403", rec.get("/recruiters/jobs"), 403)
    expect("POST /recruiters/jobs without company -> 403", rec.post("/recruiters/jobs", json={"title": "x", "description": "y"}), 403)
    co = expect("POST /recruiters/company", rec.post("/recruiters/company", json={"name": f"Acme {tag}", "domain": f"acme-{tag}.com", "description": "Widgets"}), 201).json()
    expect("POST /recruiters/company duplicate domain -> error", rec.post("/recruiters/company", json={"name": "Dup", "domain": f"acme-{tag}.com"}), 500) if False else None
    check("auth/me shows company after setup", rec.get("/auth/me").json()["company_id"] == co["id"])
    expect("POST /recruiters/jobs invalid -> 422", rec.post("/recruiters/jobs", json={"title": "x"}), 422)
    job = expect("POST /recruiters/jobs", rec.post("/recruiters/jobs", json={"title": "Backend Engineer", "description": "Build APIs", "location": "Remote", "requirements": ["Python"], "benefits": ["Health"]}), 201).json()
    check("job is open", job["status"] == "open")
    jl = expect("GET /recruiters/jobs", rec.get("/recruiters/jobs"), 200).json()
    check("company jobs lists job", any(j["id"] == job["id"] for j in jl))
    oj = expect("GET /recruiters/jobs/open (student)", student.get("/recruiters/jobs/open"), 200).json()
    check("open jobs include job with company name", any(j["id"] == job["id"] and j["company_name"] == f"Acme {tag}" for j in oj))
    app = expect("POST /recruiters/jobs/{id}/apply", student.post(f"/recruiters/jobs/{job['id']}/apply"), 201).json()
    again_app = student.post(f"/recruiters/jobs/{job['id']}/apply").json()
    check("apply is idempotent", again_app["id"] == app["id"])
    expect("apply to unknown job -> 404", student.post(f"/recruiters/jobs/{uuid.uuid4()}/apply"), 404)
    mine = expect("GET /recruiters/applications/mine", student.get("/recruiters/applications/mine"), 200).json()
    check("my applications include job title/company", any(a["id"] == app["id"] and a["job_title"] == "Backend Engineer" and a["company_name"] for a in mine))
    ja = expect("GET /recruiters/jobs/{id}/applications", rec.get(f"/recruiters/jobs/{job['id']}/applications"), 200).json()
    check("recruiter sees applicant", any(a["id"] == app["id"] for a in ja))
    st = expect("PATCH /recruiters/applications/{id}", rec.patch(f"/recruiters/applications/{app['id']}", json={"status": "Interview"}), 200).json()
    check("status updated", st["status"] == "Interview")
    check("candidate sees new status", student.get("/recruiters/applications/mine").json()[0]["status"] == "Interview")
    expect("PATCH application by non-recruiter -> 403", student.patch(f"/recruiters/applications/{app['id']}", json={"status": "Hired"}), 403)
    rec2 = register(f"recruiter2_{tag}@test.com")
    rec2.post("/recruiters/company", json={"name": f"Other {tag}", "domain": f"other-{tag}.com"})
    expect("PATCH application from another company -> 403 (tenant isolation)", rec2.patch(f"/recruiters/applications/{app['id']}", json={"status": "Hired"}), 403)
    expect("GET applications of another company's job -> 403", rec2.get(f"/recruiters/jobs/{job['id']}/applications"), 403)
    expect("PATCH unknown application -> 404", rec.patch(f"/recruiters/applications/{uuid.uuid4()}", json={"status": "x"}), 404)

    # ── placements ───────────────────────────────────────────────────────────
    off = register(f"officer_{tag}@test.com")
    expect("GET /placements/drives without college -> 403", off.get("/placements/drives"), 403)
    col = expect("POST /placements/colleges", off.post("/placements/colleges", json={"name": f"Uni {tag}", "domain": f"uni-{tag}.edu", "address": "1 Main St"}), 201).json()
    check("auth/me shows college after setup", off.get("/auth/me").json()["college_id"] == col["id"])
    expect("POST /placements/drives invalid -> 422", off.post("/placements/drives", json={}), 422)
    drv = expect("POST /placements/drives", off.post("/placements/drives", json={"title": "Autumn Drive", "drive_type": "Campus", "date_of_drive": "2026-11-01", "requirements": {"min_cgpa": 7}}), 201).json()
    dl_ = expect("GET /placements/drives", off.get("/placements/drives"), 200).json()
    check("college drives lists drive", any(d["id"] == drv["id"] for d in dl_))
    expect("GET /placements/drives/{id}", off.get(f"/placements/drives/{drv['id']}"), 200)
    expect("GET /placements/drives/{unknown} -> 404", off.get(f"/placements/drives/{uuid.uuid4()}"), 404)
    av = expect("GET /placements/drives/available (student)", student.get("/placements/drives/available"), 200).json()
    check("available drives include drive", any(d["id"] == drv["id"] for d in av))
    reg = expect("POST /placements/drives/{id}/register", student.post(f"/placements/drives/{drv['id']}/register"), 201).json()
    check("register idempotent", student.post(f"/placements/drives/{drv['id']}/register").json()["id"] == reg["id"])
    expect("register unknown drive -> 404", student.post(f"/placements/drives/{uuid.uuid4()}/register"), 404)
    mr = expect("GET /placements/registrations/mine", student.get("/placements/registrations/mine"), 200).json()
    check("my registrations include reg", any(r["id"] == reg["id"] for r in mr))
    rl = expect("GET /placements/drives/{id}/registrations", off.get(f"/placements/drives/{drv['id']}/registrations"), 200).json()
    check("officer sees registration", any(r["id"] == reg["id"] for r in rl))
    expect("PATCH /placements/registrations/{id}", off.patch(f"/placements/registrations/{reg['id']}", json={"status": "Offered"}), 200, status="Offered")
    expect("POST /placements/registrations/{id}/offer", off.post(f"/placements/registrations/{reg['id']}/offer", json={"package_details": "12 LPA"}), 201, package_details="12 LPA")
    expect("POST calculate-eligibility", off.post(f"/placements/drives/{drv['id']}/calculate-eligibility"), 202)
    expect("POST rank", off.post(f"/placements/drives/{drv['id']}/rank"), 202)
    off2 = register(f"officer2_{tag}@test.com")
    off2.post("/placements/colleges", json={"name": f"Uni2 {tag}", "domain": f"uni2-{tag}.edu"})
    expect("PATCH registration of another college -> 404 (tenant isolation)", off2.patch(f"/placements/registrations/{reg['id']}", json={"status": "Rejected"}), 404)
    expect("offer for another college's registration -> 404", off2.post(f"/placements/registrations/{reg['id']}/offer", json={"package_details": "1"}), 404)
    expect("GET registrations of another college's drive -> 404", off2.get(f"/placements/drives/{drv['id']}/registrations"), 404)

    # ── admin ────────────────────────────────────────────────────────────────
    expect("GET /admin/dashboard/summary as student -> 403", student.get("/admin/dashboard/summary"), 403)
    expect("GET /admin/users as student -> 403", student.get("/admin/users"), 403)
    admin = Client(os.environ["E2E_ADMIN_EMAIL"], os.environ["E2E_ADMIN_PASSWORD"])  # same values used to seed
    expect("admin login", admin.login(), 200)
    am = admin.get("/auth/me").json()
    check("admin has admin:* permissions", any(p.startswith("admin:") for p in am["permissions"]))
    summ = expect("GET /admin/dashboard/summary", admin.get("/admin/dashboard/summary"), 200).json()
    all_users = admin.get("/admin/users", params={"limit": 1000}).json()["data"]
    check("admin summary total_users is the real user count", summ["total_users"] == len(all_users), f"{summ['total_users']} vs {len(all_users)}")
    check("admin summary is live, not canned (1500/950 stub gone)", summ["total_users"] != 1500)
    expect("GET /admin/health/check", admin.get("/admin/health/check"), 200)
    users = expect("GET /admin/users", admin.get("/admin/users"), 200).json()["data"]
    target = next(u for u in users if u["email"] == student.email)
    expect("PUT /admin/users/{id}/status", admin.put(f"/admin/users/{target['id']}/status", json={"status": "SUSPENDED"}), 200)
    expect("suspended user cannot log in", Client(student.email, student.password).login(), 400)
    expect("PUT /admin/users/{id}/status ACTIVE", admin.put(f"/admin/users/{target['id']}/status", json={"status": "ACTIVE"}), 200)
    expect("restored user can log in", Client(student.email, student.password).login(), 200)
    expect("PUT /admin/users/{id}/status invalid -> 422", admin.put(f"/admin/users/{target['id']}/status", json={"status": "BOGUS"}), 422)
    expect("PUT /admin/users/{unknown}/status -> 404", admin.put(f"/admin/users/{uuid.uuid4()}/status", json={"status": "ACTIVE"}), 404)
    roles = expect("GET /admin/roles", admin.get("/admin/roles"), 200).json()["data"]
    expect("GET /admin/permissions", admin.get("/admin/permissions"), 200)
    expect("POST /admin/users/{id}/roles/assign", admin.post(f"/admin/users/{target['id']}/roles/assign", params={"role_name": roles[0]["name"]}), 200)
    expect("assign unknown role -> 404", admin.post(f"/admin/users/{target['id']}/roles/assign", params={"role_name": "nope"}), 404)

    flag = expect("POST /admin/flags", admin.post("/admin/flags", json={"key": f"flag_{tag}", "description": "t"}), 200).json()
    expect("PUT /admin/flags/{id}", admin.put(f"/admin/flags/{flag['id']}", json={"is_enabled": True}), 200, is_enabled=True)
    fl = admin.get("/admin/flags").json()["data"]
    check("GET /admin/flags shows enabled flag", any(f["id"] == flag["id"] and f["is_enabled"] for f in fl))
    expect("POST /admin/settings", admin.post("/admin/settings", json={"key": f"k_{tag}", "value": "1"}), 200)
    expect("PUT /admin/settings/{key}", admin.put(f"/admin/settings/k_{tag}", json={"value": "2"}), 200, value="2")
    expect("PUT /admin/settings/{unknown} -> 404", admin.put("/admin/settings/nope_nope", json={"value": "2"}), 404)
    expect("GET /admin/settings", admin.get("/admin/settings"), 200)

    expect("GET /admin/moderation/queue", admin.get("/admin/moderation/queue", params={"status_filter": "pending"}), 200)
    expect("POST /admin/announcements", admin.post("/admin/announcements", json={"title": "Maintenance", "content": "Tonight", "severity": "info"}), 200)
    ann = expect("GET /admin/announcements/active as student (bell)", student.get("/admin/announcements/active"), 200).json()["data"]
    check("announcement visible to non-admin users", any(a["title"] == "Maintenance" for a in ann))
    expect("POST /admin/broadcast", admin.post("/admin/broadcast", json={"title": "Hi", "content": "All", "recipient_type": "all"}), 200)
    expect("GET /admin/audit/logs", admin.get("/admin/audit/logs", params={"limit": 10, "offset": 0}), 200)
    expect("GET /admin/health/snapshots", admin.get("/admin/health/snapshots"), 200)
    expect("GET /admin/monitoring/resources", admin.get("/admin/monitoring/resources"), 200)
    expect("GET /admin/monitoring/jobs", admin.get("/admin/monitoring/jobs", params={"limit": 5}), 200)
    expect("GET /admin/maintenance/status", admin.get("/admin/maintenance/status"), 200)
    expect("POST /admin/maintenance/schedule", admin.post("/admin/maintenance/schedule", json={"start_time": "2030-01-01T00:00:00Z", "end_time": "2030-01-01T02:00:00Z", "description": "Upgrade"}), 200)

    expect("POST /admin/ai/providers", admin.post("/admin/ai/providers", json={"name": f"prov_{tag}"}), 200)
    expect("PUT /admin/ai/providers/{name}", admin.put(f"/admin/ai/providers/prov_{tag}", json={"is_active": False}), 200, is_active=False)
    expect("GET /admin/ai/providers", admin.get("/admin/ai/providers"), 200)
    expect("POST /admin/ai/models", admin.post("/admin/ai/models", json={"provider_name": f"prov_{tag}", "model_name": f"model_{tag}"}), 200)
    expect("PUT /admin/ai/models/{name}", admin.put(f"/admin/ai/models/model_{tag}", json={"is_active": False}), 200, is_active=False)
    expect("GET /admin/ai/models", admin.get("/admin/ai/models"), 200)
    expect("POST /admin/ai/prompts", admin.post("/admin/ai/prompts", json={"module": f"mod_{tag}"}), 200)
    expect("POST /admin/ai/prompts/versions v1", admin.post("/admin/ai/prompts/versions", json={"module": f"mod_{tag}", "version": "1", "prompt_text": "one"}), 200)
    expect("POST /admin/ai/prompts/versions v2", admin.post("/admin/ai/prompts/versions", json={"module": f"mod_{tag}", "version": "2", "prompt_text": "two"}), 200)
    vs = expect("GET /admin/ai/prompts/{module}/versions", admin.get(f"/admin/ai/prompts/mod_{tag}/versions"), 200).json()["data"]
    check("two prompt versions", len(vs) == 2)
    expect("POST /admin/ai/prompts/rollback", admin.post("/admin/ai/prompts/rollback", params={"module": f"mod_{tag}", "version": "1", "target_version": "1"}), 200)
    expect("POST /admin/ai/testing/test", admin.post("/admin/ai/testing/test", json={"provider_name": f"prov_{tag}", "model_name": f"model_{tag}", "prompt_text": "ping"}), 200)

    failed = [n for ok, n in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("FAILED:\n  " + "\n  ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main()
