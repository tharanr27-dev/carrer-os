import asyncio
import io
import json
import uuid
from datetime import date, datetime, timezone
import httpx

from sqlalchemy import select

from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.modules.admin.models import ModerationQueue
from app.modules.auth.models import Permission, Role, User, UserStatus
from app.modules.career_discovery.models import AssessmentQuestion, AssessmentTemplate
from app.modules.learning.models import Course, LearningModule, LearningRoadmap, LearningTask
from app.modules.placements.models import College, PlacementOfficer
from app.modules.recommendations.models import Recommendation
from endpoint_integrations_map import FRONTEND_INTEGRATIONS

BASE_URL = "http://127.0.0.1:8000"

async def setup_test_users():
    async with AsyncSessionLocal() as session:
        # 1. Admin Role & Permissions
        all_perms = [
            "admin:read", "admin:write", "manage:users", "manage:roles", "manage:settings",
            "view:audit_logs", "view:health", "view:metrics", "admin:moderator"
        ]
        created_perms = []
        for p_name in all_perms:
            res = await session.execute(select(Permission).where(Permission.name == p_name))
            p = res.scalars().first()
            if not p:
                p = Permission(name=p_name, description=f"Permission for {p_name}")
                session.add(p)
                await session.flush()
            created_perms.append(p)

        res = await session.execute(select(Role).where(Role.name == "admin_super"))
        admin_role = res.scalars().first()
        if not admin_role:
            admin_role = Role(name="admin_super", description="Super Admin Role", permissions=created_perms)
            session.add(admin_role)
            await session.flush()
        else:
            for p in created_perms:
                if p not in admin_role.permissions:
                    admin_role.permissions.append(p)
            await session.flush()

        for r_name in ["student", "recruiter", "placement_officer", "admin"]:
            res = await session.execute(select(Role).where(Role.name == r_name))
            if not res.scalars().first():
                session.add(Role(name=r_name, description=f"{r_name} role"))
        await session.flush()

        res = await session.execute(select(User).where(User.email == "admin_test@careeros.ai"))
        admin_user = res.scalars().first()
        if not admin_user:
            admin_user = User(
                email="admin_test@careeros.ai",
                hashed_password=get_password_hash("AdminPass123!"),
                status=UserStatus.ACTIVE,
                roles=[admin_role]
            )
            session.add(admin_user)
            await session.flush()

        # 2. Recruiter User
        res = await session.execute(select(User).where(User.email == "recruiter_test@stripe.com"))
        recruiter_user = res.scalars().first()
        if not recruiter_user:
            recruiter_user = User(
                email="recruiter_test@stripe.com",
                hashed_password=get_password_hash("RecruiterPass123!"),
                status=UserStatus.ACTIVE,
            )
            session.add(recruiter_user)
            await session.flush()

        # 3. Placement Officer User
        res = await session.execute(select(User).where(User.email == "officer_test@university.edu"))
        officer_user = res.scalars().first()
        if not officer_user:
            officer_user = User(
                email="officer_test@university.edu",
                hashed_password=get_password_hash("OfficerPass123!"),
                status=UserStatus.ACTIVE,
            )
            session.add(officer_user)
            await session.flush()

        # 4. Student User
        res = await session.execute(select(User).where(User.email == "student_test@university.edu"))
        student_user = res.scalars().first()
        if not student_user:
            student_user = User(
                email="student_test@university.edu",
                hashed_password=get_password_hash("StudentPass123!"),
                status=UserStatus.ACTIVE,
            )
            session.add(student_user)
            await session.flush()

        # 5. Assessment Template & Question for Discovery
        res = await session.execute(select(AssessmentTemplate).where(AssessmentTemplate.title == "General Tech Career Assessment"))
        template = res.scalars().first()
        if not template:
            template = AssessmentTemplate(
                title="General Tech Career Assessment",
                description="Evaluates technical and interpersonal interests"
            )
            session.add(template)
            await session.flush()

        res = await session.execute(select(AssessmentQuestion).where(AssessmentQuestion.template_id == template.id))
        question = res.scalars().first()
        if not question:
            question = AssessmentQuestion(
                template_id=template.id,
                question_text="What programming languages do you enjoy?",
                question_type="TEXT",
                order_index=1
            )
            session.add(question)
            await session.flush()

        # 6. Sample Roadmap & Task for Learning test
        res = await session.execute(select(LearningRoadmap).where(LearningRoadmap.user_id == student_user.id))
        existing_roadmap = res.scalars().first()
        if existing_roadmap:
            existing_roadmap.status = "ACTIVE"
            roadmap = existing_roadmap
        else:
            roadmap = LearningRoadmap(
                user_id=student_user.id,
                title="Fullstack Developer Roadmap",
                target_role="Fullstack Engineer",
                status="ACTIVE"
            )
            session.add(roadmap)
        await session.flush()

        res = await session.execute(select(LearningModule).where(LearningModule.roadmap_id == roadmap.id))
        module = res.scalars().first()
        if not module:
            module = LearningModule(
                roadmap_id=roadmap.id,
                title="Backend Foundations",
                order_index=1,
                status="ACTIVE"
            )
            session.add(module)
            await session.flush()

        res = await session.execute(select(LearningTask).where(LearningTask.module_id == module.id))
        task = res.scalars().first()
        if not task:
            task = LearningTask(
                module_id=module.id,
                title="Build REST API with FastAPI",
                difficulty="INTERMEDIATE",
                status="IN_PROGRESS"
            )
            session.add(task)
            await session.flush()

        # 7. Sample Recommendation (reset to ACTIVE)
        res = await session.execute(select(Recommendation).where(Recommendation.user_id == student_user.id))
        sample_rec = res.scalars().first()
        if not sample_rec:
            sample_rec = Recommendation(
                user_id=student_user.id,
                category="SKILL",
                title="Learn Docker & Kubernetes",
                confidence_score=0.9,
                estimated_impact=0.8,
                difficulty="MEDIUM",
                status="ACTIVE"
            )
            session.add(sample_rec)
            await session.flush()
        else:
            sample_rec.status = "ACTIVE"
            await session.flush()

        # 8. Sample Moderation Queue item
        res = await session.execute(select(ModerationQueue).where(ModerationQueue.status == "pending"))
        mod_item = res.scalars().first()
        if not mod_item:
            mod_item = ModerationQueue(
                entity_type="post",
                entity_id=student_user.id,
                reason="Suspicious activity reported",
                status="pending"
            )
            session.add(mod_item)
            await session.flush()

        await session.commit()

        tokens = {
            "admin": create_access_token(admin_user.id),
            "recruiter": create_access_token(recruiter_user.id),
            "officer": create_access_token(officer_user.id),
            "student": create_access_token(student_user.id),
            "student_refresh": create_refresh_token(student_user.id),
        }
        ids = {
            "admin_user_id": str(admin_user.id),
            "student_user_id": str(student_user.id),
            "recruiter_user_id": str(recruiter_user.id),
            "officer_user_id": str(officer_user.id),
            "template_id": str(template.id),
            "question_id": str(question.id),
            "roadmap_id": str(roadmap.id),
            "task_id": str(task.id),
            "rec_id": str(sample_rec.id),
            "mod_item_id": str(mod_item.id),
        }
        return tokens, ids

async def run_all_tests():
    tokens, ids = await setup_test_users()

    admin_hdr = {"Authorization": f"Bearer {tokens['admin']}"}
    student_hdr = {"Authorization": f"Bearer {tokens['student']}"}
    recruiter_hdr = {"Authorization": f"Bearer {tokens['recruiter']}"}
    officer_hdr = {"Authorization": f"Bearer {tokens['officer']}"}

    results = []

    async with httpx.AsyncClient(base_url=BASE_URL, headers={"x-bypass-rate-limit": "test-suite"}, timeout=15.0) as client:
        def record(num, method, endpoint, purpose, status_code, expected_status, body=None):
            passed = (status_code == expected_status) or (isinstance(expected_status, list) and status_code in expected_status)
            test_res = "PASS" if passed else f"FAIL ({status_code})"
            meta = FRONTEND_INTEGRATIONS.get((method, endpoint), {})

            status = "CONNECTED_AND_TESTED" if passed else "FAILED"
            results.append({
                "num": num,
                "method": method,
                "endpoint": endpoint,
                "purpose": purpose,
                "status_code": status_code,
                "expected": expected_status,
                "test_result": test_res,
                "status": status,
                "auth_required": meta.get("auth", "Bearer JWT"),
                "frontend_client": meta.get("client", "api client"),
                "frontend_location": meta.get("location", "frontend UI"),
                "ui_state_handling": meta.get("states", "Loading, Error, Success"),
                "test_evidence": f"HTTP {status_code} ({test_res})"
            })
            print(f"[{test_res}] {method:6} {endpoint:52} -> {status_code}")

        n = 1
        dummy_id = str(uuid.uuid4())

        def extract_id(resp):
            try:
                j = resp.json()
                if isinstance(j, dict):
                    if "data" in j and isinstance(j["data"], dict) and "id" in j["data"]:
                        return str(j["data"]["id"])
                    if "id" in j:
                        return str(j["id"])
            except Exception:
                pass
            return str(uuid.uuid4())

        # ── 1. SYSTEM, HEALTH & DOCS (7) ────────────────────────────────────
        r = await client.get("/health")
        record(n, "GET", "/health", "System health check", r.status_code, 200); n += 1

        r = await client.get("/health/live")
        record(n, "GET", "/health/live", "Liveness probe", r.status_code, 200); n += 1

        r = await client.get("/health/ready")
        record(n, "GET", "/health/ready", "Readiness probe", r.status_code, 200); n += 1

        r = await client.get("/metrics")
        record(n, "GET", "/metrics", "Prometheus metrics exposition", r.status_code, 200); n += 1

        r = await client.get("/docs")
        record(n, "GET", "/docs", "Swagger UI interactive documentation", r.status_code, 200); n += 1

        r = await client.get("/docs/oauth2-redirect")
        record(n, "GET", "/docs/oauth2-redirect", "Swagger OAuth2 redirect helper", r.status_code, 200); n += 1

        r = await client.get("/redoc")
        record(n, "GET", "/redoc", "ReDoc OpenAPI documentation", r.status_code, 200); n += 1

        # ── 2. OPENAPI SPECIFICATION (1) ────────────────────────────────────
        r = await client.get("/api/v1/openapi.json")
        record(n, "GET", "/api/v1/openapi.json", "OpenAPI JSON schema specification", r.status_code, 200); n += 1

        # ── 3. AUTHENTICATION (4) ───────────────────────────────────────────
        unique_email = f"user_{uuid.uuid4().hex[:6]}@domain.com"
        r = await client.post("/api/v1/auth/register", json={"email": unique_email, "password": "Password123!"})
        record(n, "POST", "/api/v1/auth/register", "User account registration", r.status_code, 201); n += 1

        r = await client.post("/api/v1/auth/login", json={"email": unique_email, "password": "Password123!"})
        record(n, "POST", "/api/v1/auth/login", "User login & JWT token issuance", r.status_code, 200); n += 1

        r = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["student_refresh"]})
        record(n, "POST", "/api/v1/auth/refresh", "Refresh access token transparently", r.status_code, 200); n += 1

        r = await client.get("/api/v1/auth/me", headers=student_hdr)
        record(n, "GET", "/api/v1/auth/me", "Get current user session & RBAC roles", r.status_code, 200); n += 1

        # ── 4. USERS & PROFILE (2) ──────────────────────────────────────────
        r = await client.get("/api/v1/users/me/profile", headers=student_hdr)
        record(n, "GET", "/api/v1/users/me/profile", "Fetch user profile details", r.status_code, 200); n += 1

        r = await client.put("/api/v1/users/me/profile", headers=student_hdr, json={
            "first_name": "Student", "last_name": "User", "headline": "Junior Dev"
        })
        record(n, "PUT", "/api/v1/users/me/profile", "Update user profile details", r.status_code, 200); n += 1

        # ── 5. CAREER DISCOVERY (3) ─────────────────────────────────────────
        r = await client.get("/api/v1/discovery/templates", headers=student_hdr)
        record(n, "GET", "/api/v1/discovery/templates", "List career assessment templates", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/discovery/assessments/{ids['template_id']}/submit", headers=student_hdr, json={
            "answers": [{"question_id": ids['question_id'], "answer_text": "Python and TypeScript"}]
        })
        record(n, "POST", "/api/v1/discovery/assessments/{template_id}/submit", "Submit assessment answers", r.status_code, 200); n += 1

        r = await client.get(f"/api/v1/discovery/reports/{dummy_id}", headers=student_hdr)
        record(n, "GET", "/api/v1/discovery/reports/{report_id}", "Get career report (404/200 handled)", r.status_code, [200, 404]); n += 1

        # ── 6. RESUMES (4) ──────────────────────────────────────────────────
        r = await client.get("/api/v1/resumes", headers=student_hdr)
        record(n, "GET", "/api/v1/resumes", "List user resumes", r.status_code, 200); n += 1

        pdf_content = b"%PDF-1.4 test resume mock content"
        files = {"file": ("resume.pdf", pdf_content, "application/pdf")}
        r = await client.post("/api/v1/resumes/upload", headers=student_hdr, files=files)
        record(n, "POST", "/api/v1/resumes/upload", "Upload resume file", r.status_code, 202)
        resume_id = extract_id(r)
        n += 1

        r = await client.get(f"/api/v1/resumes/{resume_id}/analysis", headers=student_hdr)
        record(n, "GET", "/api/v1/resumes/{resume_id}/analysis", "Get resume ATS analysis", r.status_code, [200, 404]); n += 1

        r = await client.get(f"/api/v1/resumes/{resume_id}/download", headers=student_hdr)
        record(n, "GET", "/api/v1/resumes/{resume_id}/download", "Get signed resume download URL", r.status_code, 200); n += 1

        # ── 7. MENTOR (5) ───────────────────────────────────────────────────
        r = await client.get("/api/v1/mentor/goals", headers=student_hdr)
        record(n, "GET", "/api/v1/mentor/goals", "List student career goals", r.status_code, 200); n += 1

        r = await client.post("/api/v1/mentor/goals", headers=student_hdr, json={
            "title": "Master Backend Systems", "description": "Learn FastAPI & Databases"
        })
        record(n, "POST", "/api/v1/mentor/goals", "Create career goal", r.status_code, 200); n += 1

        r = await client.post("/api/v1/mentor/sessions", headers=student_hdr)
        record(n, "POST", "/api/v1/mentor/sessions", "Create mentor session", r.status_code, 200)
        mentor_session_id = extract_id(r)
        n += 1

        r = await client.get("/api/v1/mentor/sessions/latest", headers=student_hdr)
        record(n, "GET", "/api/v1/mentor/sessions/latest", "Get latest mentor session conversation", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/mentor/sessions/{mentor_session_id}/message", headers=student_hdr, json={
            "content": "How do I prepare for system design interviews?"
        })
        record(n, "POST", "/api/v1/mentor/sessions/{session_id}/message", "Send message to AI mentor", r.status_code, 200); n += 1

        # ── 8. INTERVIEWS (2) ───────────────────────────────────────────────
        r = await client.post("/api/v1/interviews/sessions", headers=student_hdr, json={
            "interview_type": "TECHNICAL", "company": "Google", "difficulty": "MEDIUM"
        })
        record(n, "POST", "/api/v1/interviews/sessions", "Initialize AI interview session", r.status_code, 200)
        interview_session_id = extract_id(r)
        n += 1

        r = await client.get(f"/api/v1/interviews/sessions/{interview_session_id}/report", headers=student_hdr)
        record(n, "GET", "/api/v1/interviews/sessions/{session_id}/report", "Get interview performance report", r.status_code, [200, 404]); n += 1

        # ── 9. COMMUNICATION (2) ────────────────────────────────────────────
        r = await client.post("/api/v1/communication/sessions", headers=student_hdr, json={"mode": "WORKPLACE"})
        record(n, "POST", "/api/v1/communication/sessions", "Initialize communication session", r.status_code, 200)
        comm_session_id = extract_id(r)
        n += 1

        r = await client.get(f"/api/v1/communication/sessions/{comm_session_id}/report", headers=student_hdr)
        record(n, "GET", "/api/v1/communication/sessions/{session_id}/report", "Get communication session report", r.status_code, [200, 404]); n += 1

        # ── 10. LEARNING ACADEMY (3) ────────────────────────────────────────
        r = await client.get("/api/v1/learning/roadmaps/active", headers=student_hdr)
        record(n, "GET", "/api/v1/learning/roadmaps/active", "Get active learning roadmap", r.status_code, 200); n += 1

        r = await client.post("/api/v1/learning/roadmaps/generate", headers=student_hdr, json={
            "target_role": "Backend Engineer", "target_company": "Amazon"
        })
        record(n, "POST", "/api/v1/learning/roadmaps/generate", "Generate learning roadmap", r.status_code, 202); n += 1

        r = await client.post("/api/v1/learning/tasks/complete", headers=student_hdr, json={"task_id": ids['task_id']})
        record(n, "POST", "/api/v1/learning/tasks/complete", "Complete learning roadmap task", r.status_code, 200); n += 1

        # ── 11. RECOMMENDATIONS (3) ─────────────────────────────────────────
        # Note: Testing GET feed before refresh retrieves the active seeded recommendation
        r = await client.get("/api/v1/recommendations/feed", headers=student_hdr)
        record(n, "GET", "/api/v1/recommendations/feed", "Get personalized recommendation feed", r.status_code, [200, 404]); n += 1

        r = await client.post("/api/v1/recommendations/refresh", headers=student_hdr)
        record(n, "POST", "/api/v1/recommendations/refresh", "Refresh recommendation cycle", r.status_code, 202); n += 1

        r = await client.post("/api/v1/recommendations/feedback", headers=student_hdr, json={
            "recommendation_id": ids['rec_id'], "action": "ACCEPT", "feedback_text": "Very useful"
        })
        record(n, "POST", "/api/v1/recommendations/feedback", "Submit recommendation feedback", r.status_code, 200); n += 1

        # ── 12. ANALYTICS (3) ───────────────────────────────────────────────
        r = await client.get("/api/v1/analytics/dashboard/student", headers=student_hdr)
        record(n, "GET", "/api/v1/analytics/dashboard/student", "Fetch student readiness analytics", r.status_code, 200); n += 1

        r = await client.post("/api/v1/analytics/events", headers=student_hdr, json={
            "event_type": "PAGE_VIEW", "module": "dashboard", "payload": {"source": "navigation"}
        })
        record(n, "POST", "/api/v1/analytics/events", "Ingest domain analytics event", r.status_code, 202); n += 1

        r = await client.post("/api/v1/analytics/ai-usage", headers=student_hdr, json={
            "module": "mentor", "provider": "openai", "model": "gpt-4o", "total_tokens": 150, "prompt_tokens": 80, "completion_tokens": 70
        })
        record(n, "POST", "/api/v1/analytics/ai-usage", "Log AI pipeline token usage & telemetry", r.status_code, 201); n += 1

        # ── 13. COMMUNITY (8) ───────────────────────────────────────────────
        r = await client.post("/api/v1/community/posts", headers=student_hdr, json={
            "title": "Tips for Technical Interviews", "content": "Practice data structures and LeetCode daily.", "category": "CAREER_ADVICE"
        })
        record(n, "POST", "/api/v1/community/posts", "Create community discussion post", r.status_code, 201)
        post_id = extract_id(r)
        n += 1

        r = await client.get(f"/api/v1/community/posts/{post_id}", headers=student_hdr)
        record(n, "GET", "/api/v1/community/posts/{post_id}", "Get community post details", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/community/posts/{post_id}/comments", headers=student_hdr, json={
            "content": "Great advice! Consistent practice makes a huge difference."
        })
        record(n, "POST", "/api/v1/community/posts/{post_id}/comments", "Comment on community post", r.status_code, 201); n += 1

        r = await client.get(f"/api/v1/community/posts/{post_id}/comments", headers=student_hdr)
        record(n, "GET", "/api/v1/community/posts/{post_id}/comments", "List comments on community post", r.status_code, 200); n += 1

        r = await client.post("/api/v1/community/reactions", headers=student_hdr, json={
            "entity_type": "post", "entity_id": post_id, "reaction_type": "LIKE"
        })
        record(n, "POST", "/api/v1/community/reactions", "React (Like) to community post", r.status_code, 201); n += 1

        r = await client.get("/api/v1/community/feed/latest", headers=student_hdr)
        record(n, "GET", "/api/v1/community/feed/latest", "Fetch latest community posts feed", r.status_code, 200); n += 1

        r = await client.get("/api/v1/community/feed/trending", headers=student_hdr)
        record(n, "GET", "/api/v1/community/feed/trending", "Fetch trending community posts feed", r.status_code, 200); n += 1

        r = await client.get("/api/v1/community/search?q=Interviews", headers=student_hdr)
        record(n, "GET", "/api/v1/community/search", "Search community posts", r.status_code, 200); n += 1

        # ── 14. RECRUITERS (8) ──────────────────────────────────────────────
        rec_domain = f"stripe-{uuid.uuid4().hex[:6]}.com"
        r = await client.post("/api/v1/recruiters/company", headers=recruiter_hdr, json={
            "name": "Stripe Payments", "domain": rec_domain
        })
        record(n, "POST", "/api/v1/recruiters/company", "Register recruiter company", r.status_code, 201); n += 1

        r = await client.post("/api/v1/recruiters/jobs", headers=recruiter_hdr, json={
            "title": "Software Engineer II", "description": "Backend API engineer"
        })
        record(n, "POST", "/api/v1/recruiters/jobs", "Post new job opening", r.status_code, 201)
        job_id = extract_id(r)
        n += 1

        r = await client.get("/api/v1/recruiters/jobs", headers=recruiter_hdr)
        record(n, "GET", "/api/v1/recruiters/jobs", "List company posted jobs", r.status_code, 200); n += 1

        r = await client.get("/api/v1/recruiters/jobs/open", headers=student_hdr)
        record(n, "GET", "/api/v1/recruiters/jobs/open", "List open jobs for candidates", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/recruiters/jobs/{job_id}/apply", headers=student_hdr)
        record(n, "POST", "/api/v1/recruiters/jobs/{job_id}/apply", "Apply for job opening", r.status_code, 201)
        application_id = extract_id(r)
        n += 1

        r = await client.get("/api/v1/recruiters/applications/mine", headers=student_hdr)
        record(n, "GET", "/api/v1/recruiters/applications/mine", "List candidate submitted applications", r.status_code, 200); n += 1

        r = await client.get(f"/api/v1/recruiters/jobs/{job_id}/applications", headers=recruiter_hdr)
        record(n, "GET", "/api/v1/recruiters/jobs/{job_id}/applications", "View job applications for recruiter", r.status_code, 200); n += 1

        r = await client.patch(f"/api/v1/recruiters/applications/{application_id}", headers=recruiter_hdr, json={
            "status": "Shortlisted"
        })
        record(n, "PATCH", "/api/v1/recruiters/applications/{application_id}", "Update application status", r.status_code, 200); n += 1

        # ── 15. PLACEMENTS (12) ─────────────────────────────────────────────
        clg_domain = f"univ-{uuid.uuid4().hex[:6]}.edu"
        r = await client.post("/api/v1/placements/colleges", headers=officer_hdr, json={
            "name": "State University", "domain": clg_domain
        })
        record(n, "POST", "/api/v1/placements/colleges", "Register college institution", r.status_code, 201); n += 1

        r = await client.post("/api/v1/placements/drives", headers=officer_hdr, json={
            "title": "Amazon Fall Hiring Drive", "drive_type": "CAMPUS", "date_of_drive": str(date.today())
        })
        record(n, "POST", "/api/v1/placements/drives", "Create placement drive", r.status_code, 201)
        drive_id = extract_id(r)
        n += 1

        r = await client.get("/api/v1/placements/drives", headers=officer_hdr)
        record(n, "GET", "/api/v1/placements/drives", "List college placement drives", r.status_code, 200); n += 1

        r = await client.get("/api/v1/placements/drives/available", headers=student_hdr)
        record(n, "GET", "/api/v1/placements/drives/available", "List available drives for student", r.status_code, 200); n += 1

        r = await client.get(f"/api/v1/placements/drives/{drive_id}", headers=officer_hdr)
        record(n, "GET", "/api/v1/placements/drives/{drive_id}", "Get placement drive details", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/placements/drives/{drive_id}/calculate-eligibility", headers=officer_hdr)
        record(n, "POST", "/api/v1/placements/drives/{drive_id}/calculate-eligibility", "Run drive eligibility calculation", r.status_code, 202); n += 1

        r = await client.post(f"/api/v1/placements/drives/{drive_id}/register", headers=student_hdr)
        record(n, "POST", "/api/v1/placements/drives/{drive_id}/register", "Student registers for placement drive", r.status_code, 201)
        registration_id = extract_id(r)
        n += 1

        r = await client.get("/api/v1/placements/registrations/mine", headers=student_hdr)
        record(n, "GET", "/api/v1/placements/registrations/mine", "List student drive registrations", r.status_code, 200); n += 1

        r = await client.get(f"/api/v1/placements/drives/{drive_id}/registrations", headers=officer_hdr)
        record(n, "GET", "/api/v1/placements/drives/{drive_id}/registrations", "List all registrations for drive", r.status_code, 200); n += 1

        r = await client.patch(f"/api/v1/placements/registrations/{registration_id}", headers=officer_hdr, json={
            "status": "SHORTLISTED"
        })
        record(n, "PATCH", "/api/v1/placements/registrations/{registration_id}", "Update student drive registration status", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/placements/registrations/{registration_id}/offer", headers=officer_hdr, json={
            "package_details": "18 LPA Base + Stocks"
        })
        record(n, "POST", "/api/v1/placements/registrations/{registration_id}/offer", "Issue placement offer letter", r.status_code, 201); n += 1

        r = await client.post(f"/api/v1/placements/drives/{drive_id}/rank", headers=officer_hdr)
        record(n, "POST", "/api/v1/placements/drives/{drive_id}/rank", "Run AI candidate ranking for drive", r.status_code, 202); n += 1

        # ── 16. ADMIN GOVERNANCE (27) ───────────────────────────────────────
        r = await client.get("/api/v1/admin/dashboard/summary", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/dashboard/summary", "Admin dashboard system metrics summary", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/health/check", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/health/check", "Admin deep system dependencies health check", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/health/snapshots", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/health/snapshots", "Admin system health snapshots history", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/audit/logs", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/audit/logs", "Admin security & action audit logs", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/roles", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/roles", "List system RBAC roles", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/permissions", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/permissions", "List system RBAC permissions", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/users", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/users", "List all platform users for administration", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/admin/users/{ids['student_user_id']}/roles/assign", headers=admin_hdr, json={"role_name": "student"})
        record(n, "POST", "/api/v1/admin/users/{user_id}/roles/assign", "Assign role to user account", r.status_code, 200); n += 1

        r = await client.put(f"/api/v1/admin/users/{ids['student_user_id']}/status", headers=admin_hdr, json={"status": "ACTIVE"})
        record(n, "PUT", "/api/v1/admin/users/{user_id}/status", "Update user account status (ACTIVE/SUSPENDED)", r.status_code, 200); n += 1

        flag_key = f"feature_ai_mentor_{uuid.uuid4().hex[:6]}"
        r = await client.post("/api/v1/admin/flags", headers=admin_hdr, json={
            "key": flag_key, "is_enabled": True, "description": "Enable AI Mentor"
        })
        record(n, "POST", "/api/v1/admin/flags", "Create feature flag", r.status_code, 200)
        flag_id = extract_id(r)
        n += 1

        r = await client.get("/api/v1/admin/flags", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/flags", "List all feature flags", r.status_code, 200); n += 1

        r = await client.put(f"/api/v1/admin/flags/{flag_id}", headers=admin_hdr, json={
            "is_enabled": False
        })
        record(n, "PUT", "/api/v1/admin/flags/{flag_id}", "Update feature flag state", r.status_code, 200); n += 1

        setting_key = f"platform_rate_limit_{uuid.uuid4().hex[:6]}"
        r = await client.post("/api/v1/admin/settings", headers=admin_hdr, json={
            "key": setting_key, "value": "120", "value_type": "integer"
        })
        record(n, "POST", "/api/v1/admin/settings", "Create system configuration setting", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/settings", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/settings", "List all system settings", r.status_code, 200); n += 1

        r = await client.put(f"/api/v1/admin/settings/{setting_key}", headers=admin_hdr, json={
            "value": "200"
        })
        record(n, "PUT", "/api/v1/admin/settings/{key}", "Update system configuration setting", r.status_code, 200); n += 1

        prov_name = f"openai-{uuid.uuid4().hex[:6]}"
        r = await client.post("/api/v1/admin/ai/providers", headers=admin_hdr, json={
            "name": prov_name, "priority": 1, "is_active": True
        })
        record(n, "POST", "/api/v1/admin/ai/providers", "Register AI LLM provider", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/ai/providers", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/ai/providers", "List configured AI LLM providers", r.status_code, 200); n += 1

        r = await client.put(f"/api/v1/admin/ai/providers/{prov_name}", headers=admin_hdr, json={
            "priority": 2
        })
        record(n, "PUT", "/api/v1/admin/ai/providers/{name}", "Update AI LLM provider configuration", r.status_code, 200); n += 1

        model_name = f"gpt-4o-custom-{uuid.uuid4().hex[:6]}"
        r = await client.post("/api/v1/admin/ai/models", headers=admin_hdr, json={
            "provider_name": prov_name, "model_name": model_name, "temperature": 0.7
        })
        record(n, "POST", "/api/v1/admin/ai/models", "Register AI model configuration", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/ai/models", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/ai/models", "List configured AI models", r.status_code, 200); n += 1

        r = await client.put(f"/api/v1/admin/ai/models/{model_name}", headers=admin_hdr, json={
            "temperature": 0.5
        })
        record(n, "PUT", "/api/v1/admin/ai/models/{model_name}", "Update AI model hyperparameters", r.status_code, 200); n += 1

        module_prompt = f"mentor_module_{uuid.uuid4().hex[:6]}"
        r = await client.post("/api/v1/admin/ai/prompts", headers=admin_hdr, json={
            "module": module_prompt, "description": "Mentor prompt module"
        })
        record(n, "POST", "/api/v1/admin/ai/prompts", "Create AI prompt template container", r.status_code, 200); n += 1

        r = await client.post("/api/v1/admin/ai/prompts/versions", headers=admin_hdr, json={
            "module": module_prompt, "version": "1.0.0", "prompt_text": "You are CareerOS expert."
        })
        record(n, "POST", "/api/v1/admin/ai/prompts/versions", "Publish new version of AI prompt", r.status_code, 200); n += 1

        r = await client.post("/api/v1/admin/ai/prompts/rollback", headers=admin_hdr, params={
            "module": module_prompt, "version": "1.0.0", "target_version": "1.0.0"
        })
        record(n, "POST", "/api/v1/admin/ai/prompts/rollback", "Rollback AI prompt version", r.status_code, 200); n += 1

        r = await client.get(f"/api/v1/admin/ai/prompts/{module_prompt}/versions", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/ai/prompts/{module}/versions", "List versions of module AI prompt", r.status_code, 200); n += 1

        r = await client.post("/api/v1/admin/ai/testing/test", headers=admin_hdr, json={
            "provider_name": prov_name, "model_name": model_name, "prompt_text": "Hello CareerOS"
        })
        record(n, "POST", "/api/v1/admin/ai/testing/test", "Live test AI LLM provider endpoint", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/moderation/queue", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/moderation/queue", "Get moderation queue pending items", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/admin/moderation/queue/{ids['mod_item_id']}/decision", headers=admin_hdr, json={
            "decision": "dismiss"
        })
        record(n, "POST", "/api/v1/admin/moderation/queue/{item_id}/decision", "Execute moderation item decision", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/monitoring/jobs", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/monitoring/jobs", "List background asynchronous tasks & jobs", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/monitoring/resources", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/monitoring/resources", "Get server resource utilisation metrics", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/maintenance/status", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/maintenance/status", "Check system maintenance mode status", r.status_code, 200); n += 1

        r = await client.post("/api/v1/admin/maintenance/schedule", headers=admin_hdr, json={
            "start_time": "2026-11-01T02:00:00Z", "end_time": "2026-11-01T04:00:00Z", "description": "Database upgrade"
        })
        record(n, "POST", "/api/v1/admin/maintenance/schedule", "Schedule planned maintenance window", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/announcements/active", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/announcements/active", "List active system announcements", r.status_code, 200); n += 1

        r = await client.post("/api/v1/admin/announcements", headers=admin_hdr, json={
            "title": "New Features Released", "content": "Explore the new AI interview coach!"
        })
        record(n, "POST", "/api/v1/admin/announcements", "Create system announcement", r.status_code, 200); n += 1

        r = await client.post("/api/v1/admin/broadcast", headers=admin_hdr, json={
            "title": "Platform Maintenance Tonight", "content": "Brief maintenance window at 2 AM UTC.", "recipient_type": "all"
        })
        record(n, "POST", "/api/v1/admin/broadcast", "Broadcast push notification to users", r.status_code, 200); n += 1

        # ── 17. NEGATIVE & ERROR VALIDATION TESTS (5) ───────────────────────
        r = await client.get("/api/v1/users/me/profile")
        record(n, "GET", "/api/v1/users/me/profile", "Error check: unauthenticated request -> 401 Unauthorized", r.status_code, 401); n += 1

        r = await client.post("/api/v1/auth/login", json={"email": "incomplete@user.com"})
        record(n, "POST", "/api/v1/auth/login", "Error check: missing password -> 422 Validation Error", r.status_code, 422); n += 1

        r = await client.post("/api/v1/auth/register", content=b"invalid json", headers={"Content-Type": "application/json"})
        record(n, "POST", "/api/v1/auth/register", "Error check: malformed json -> 422 Unprocessable Entity", r.status_code, 422); n += 1

        r = await client.get(f"/api/v1/placements/drives/{uuid.uuid4()}", headers=officer_hdr)
        record(n, "GET", "/api/v1/placements/drives/{drive_id}", "Error check: non-existent drive -> 404 Not Found", r.status_code, 404); n += 1

        r = await client.post("/api/v1/resumes/upload", headers=student_hdr, files={"file": ("malicious.exe", b"binary", "application/x-msdownload")})
        record(n, "POST", "/api/v1/resumes/upload", "Error check: invalid file type -> 400 Bad Request", r.status_code, 400); n += 1

    print("\n" + "="*80)
    total = len(results)
    passed = sum(1 for r in results if r["test_result"] == "PASS")
    failed = total - passed
    print(f"VERIFICATION COMPLETE: {total} tests run, {passed} PASSED, {failed} FAILED")
    print("="*80)

    with open("endpoint_verification_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
