import asyncio
import io
import json
import uuid
from datetime import date, datetime, timezone
import httpx

from sqlalchemy import select

from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.modules.admin.models import ModerationQueue
from app.modules.auth.models import Permission, Role, User, UserStatus
from app.modules.career_discovery.models import AssessmentQuestion, AssessmentTemplate
from app.modules.learning.models import Course, LearningModule, LearningRoadmap, LearningTask
from app.modules.placements.models import College, PlacementOfficer
from app.modules.recommendations.models import Recommendation

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

        # 5. Career Discovery Template & Question
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
        res = await session.execute(select(LearningRoadmap).where(LearningRoadmap.user_id == student_user.id, LearningRoadmap.status == "ACTIVE"))
        roadmap = res.scalars().first()
        if not roadmap:
            res_any = await session.execute(select(LearningRoadmap).where(LearningRoadmap.user_id == student_user.id))
            existing_roadmap = res_any.scalars().first()
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

        # Generate access tokens
        tokens = {
            "admin": create_access_token(admin_user.id),
            "recruiter": create_access_token(recruiter_user.id),
            "officer": create_access_token(officer_user.id),
            "student": create_access_token(student_user.id),
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

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # Helper recorder
        def record(num, method, endpoint, purpose, status_code, expected_status, body=None):
            passed = (status_code == expected_status) or (isinstance(expected_status, list) and status_code in expected_status)
            status_text = "PASS" if passed else f"FAIL ({status_code})"
            results.append({
                "num": num,
                "method": method,
                "endpoint": endpoint,
                "purpose": purpose,
                "status_code": status_code,
                "expected": expected_status,
                "status": status_text,
                "frontend_connected": "YES" if endpoint in ["/health", "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/users/me/profile"] else "Available"
            })
            print(f"[{status_text}] {method:6} {endpoint:45} -> {status_code}")

        n = 1

        # ── 1. SYSTEM & HEALTH ──────────────────────────────────────────────
        r = await client.get("/health")
        record(n, "GET", "/health", "System health check", r.status_code, 200); n += 1

        r = await client.get("/health/live")
        record(n, "GET", "/health/live", "Liveness probe", r.status_code, 200); n += 1

        r = await client.get("/health/ready")
        record(n, "GET", "/health/ready", "Readiness probe", r.status_code, 200); n += 1

        r = await client.get("/metrics")
        record(n, "GET", "/metrics", "Prometheus metrics", r.status_code, 200); n += 1

        r = await client.get("/api/v1/openapi.json")
        record(n, "GET", "/api/v1/openapi.json", "OpenAPI schema", r.status_code, 200); n += 1

        # ── 2. AUTH ─────────────────────────────────────────────────────────
        unique_email = f"new_user_{uuid.uuid4().hex[:6]}@domain.com"
        r = await client.post("/api/v1/auth/register", json={"email": unique_email, "password": "Password123!"})
        record(n, "POST", "/api/v1/auth/register", "User registration", r.status_code, 201); n += 1

        r = await client.post("/api/v1/auth/login", json={"email": unique_email, "password": "Password123!"})
        record(n, "POST", "/api/v1/auth/login", "User login", r.status_code, 200); n += 1

        # ── 3. USERS ────────────────────────────────────────────────────────
        r = await client.get("/api/v1/users/me/profile", headers=student_hdr)
        record(n, "GET", "/api/v1/users/me/profile", "Fetch user profile", r.status_code, 200); n += 1

        r = await client.put("/api/v1/users/me/profile", headers=student_hdr, json={
            "first_name": "Student", "last_name": "User", "headline": "Junior Dev"
        })
        record(n, "PUT", "/api/v1/users/me/profile", "Update user profile", r.status_code, 200); n += 1

        # ── 4. CAREER DISCOVERY ─────────────────────────────────────────────
        r = await client.post(f"/api/v1/discovery/assessments/{ids['template_id']}/submit", headers=student_hdr, json={
            "answers": [{"question_id": ids['question_id'], "answer_text": "Python and TypeScript"}]
        })
        record(n, "POST", "/api/v1/discovery/assessments/{template_id}/submit", "Submit assessment", r.status_code, 200); n += 1

        # Report 404 test (non-existent report check error handling)
        dummy_id = str(uuid.uuid4())
        r = await client.get(f"/api/v1/discovery/reports/{dummy_id}", headers=student_hdr)
        record(n, "GET", "/api/v1/discovery/reports/{report_id}", "Get career report (404 handled)", r.status_code, 404); n += 1

        # ── 5. RESUMES ──────────────────────────────────────────────────────
        pdf_content = b"%PDF-1.4 test resume mock content"
        files = {"file": ("resume.pdf", pdf_content, "application/pdf")}
        r = await client.post("/api/v1/resumes/upload", headers=student_hdr, files=files)
        record(n, "POST", "/api/v1/resumes/upload", "Upload resume", r.status_code, 202)
        resume_id = r.json()["data"]["id"] if r.status_code == 202 else dummy_id
        n += 1

        r = await client.get(f"/api/v1/resumes/{resume_id}/analysis", headers=student_hdr)
        record(n, "GET", "/api/v1/resumes/{resume_id}/analysis", "Get resume analysis (queued/404 handled)", r.status_code, [200, 404]); n += 1

        r = await client.get(f"/api/v1/resumes/{resume_id}/download", headers=student_hdr)
        record(n, "GET", "/api/v1/resumes/{resume_id}/download", "Get resume download URL", r.status_code, 200); n += 1

        # ── 6. MENTOR ───────────────────────────────────────────────────────
        r = await client.post("/api/v1/mentor/goals", headers=student_hdr, json={
            "title": "Master Backend Systems", "description": "Learn FastAPI & Databases"
        })
        record(n, "POST", "/api/v1/mentor/goals", "Create career goal", r.status_code, 200); n += 1

        r = await client.post("/api/v1/mentor/sessions", headers=student_hdr)
        record(n, "POST", "/api/v1/mentor/sessions", "Create mentor session", r.status_code, 200)
        mentor_session_id = r.json()["data"]["id"] if r.status_code == 200 else dummy_id
        n += 1

        r = await client.post(f"/api/v1/mentor/sessions/{mentor_session_id}/message", headers=student_hdr, json={
            "content": "How do I prepare for system design interviews?"
        })
        record(n, "POST", "/api/v1/mentor/sessions/{session_id}/message", "Send message to AI mentor", r.status_code, 200); n += 1

        # ── 7. INTERVIEWS ───────────────────────────────────────────────────
        r = await client.post("/api/v1/interviews/sessions", headers=student_hdr, json={
            "interview_type": "TECHNICAL", "company": "Google", "difficulty": "MEDIUM"
        })
        record(n, "POST", "/api/v1/interviews/sessions", "Initialize AI interview session", r.status_code, 200); n += 1

        # ── 8. COMMUNICATION ────────────────────────────────────────────────
        r = await client.post("/api/v1/communication/sessions", headers=student_hdr, json={"mode": "WORKPLACE"})
        record(n, "POST", "/api/v1/communication/sessions", "Initialize communication session", r.status_code, 200); n += 1

        # ── 9. LEARNING ─────────────────────────────────────────────────────
        r = await client.get("/api/v1/learning/roadmaps/active", headers=student_hdr)
        record(n, "GET", "/api/v1/learning/roadmaps/active", "Get active learning roadmap", r.status_code, 200); n += 1

        r = await client.post("/api/v1/learning/roadmaps/generate", headers=student_hdr, json={
            "target_role": "Backend Engineer", "target_company": "Amazon"
        })
        record(n, "POST", "/api/v1/learning/roadmaps/generate", "Generate learning roadmap", r.status_code, 202); n += 1

        r = await client.post("/api/v1/learning/tasks/complete", headers=student_hdr, json={"task_id": ids['task_id']})
        record(n, "POST", "/api/v1/learning/tasks/complete", "Complete learning task", r.status_code, 200); n += 1

        # ── 10. RECOMMENDATIONS ─────────────────────────────────────────────
        r = await client.post("/api/v1/recommendations/refresh", headers=student_hdr)
        record(n, "POST", "/api/v1/recommendations/refresh", "Refresh recommendations", r.status_code, 202); n += 1

        r = await client.get("/api/v1/recommendations/feed", headers=student_hdr)
        record(n, "GET", "/api/v1/recommendations/feed", "Get recommendation feed", r.status_code, 200); n += 1

        r = await client.post("/api/v1/recommendations/feedback", headers=student_hdr, json={
            "recommendation_id": ids["rec_id"], "action": "ACCEPTED"
        })
        record(n, "POST", "/api/v1/recommendations/feedback", "Submit recommendation feedback", r.status_code, 200); n += 1

        # ── 11. ANALYTICS ───────────────────────────────────────────────────
        r = await client.post("/api/v1/analytics/events", headers=student_hdr, json={
            "event_type": "PAGE_VIEW", "module": "DASHBOARD", "entity_id": "home"
        })
        record(n, "POST", "/api/v1/analytics/events", "Log analytics event", r.status_code, 202); n += 1

        r = await client.get("/api/v1/analytics/dashboard/student", headers=student_hdr)
        record(n, "GET", "/api/v1/analytics/dashboard/student", "Get student dashboard metrics", r.status_code, 200); n += 1

        r = await client.post("/api/v1/analytics/ai-usage", headers=student_hdr, json={
            "module": "mentor", "provider": "openai", "model": "gpt-4", "tokens_prompt": 100, "tokens_completion": 50
        })
        record(n, "POST", "/api/v1/analytics/ai-usage", "Log AI token usage", r.status_code, 201); n += 1

        # ── 12. COMMUNITY ───────────────────────────────────────────────────
        r = await client.post("/api/v1/community/posts", headers=student_hdr, json={
            "title": "Welcome to CareerOS Community!",
            "content": "Excited to share our learning journeys together.",
            "category": "General",
            "tags": ["welcome", "career"]
        })
        record(n, "POST", "/api/v1/community/posts", "Create community post", r.status_code, 201)
        post_id = r.json()["id"] if r.status_code == 201 else dummy_id
        n += 1

        r = await client.get(f"/api/v1/community/posts/{post_id}", headers=student_hdr)
        record(n, "GET", "/api/v1/community/posts/{post_id}", "Get single post", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/community/posts/{post_id}/comments", headers=student_hdr, json={
            "content": "Great initiative!"
        })
        record(n, "POST", "/api/v1/community/posts/{post_id}/comments", "Add comment to post", r.status_code, 201); n += 1

        r = await client.get(f"/api/v1/community/posts/{post_id}/comments", headers=student_hdr)
        record(n, "GET", "/api/v1/community/posts/{post_id}/comments", "Get post comments", r.status_code, 200); n += 1

        r = await client.post("/api/v1/community/reactions", headers=student_hdr, json={
            "entity_type": "post", "entity_id": post_id, "reaction_type": "like"
        })
        record(n, "POST", "/api/v1/community/reactions", "Add reaction to post", r.status_code, [200, 201]); n += 1

        r = await client.get("/api/v1/community/feed/latest", headers=student_hdr)
        record(n, "GET", "/api/v1/community/feed/latest", "Get latest community feed", r.status_code, 200); n += 1

        r = await client.get("/api/v1/community/feed/trending", headers=student_hdr)
        record(n, "GET", "/api/v1/community/feed/trending", "Get trending community feed", r.status_code, 200); n += 1

        r = await client.get("/api/v1/community/search?q=career", headers=student_hdr)
        record(n, "GET", "/api/v1/community/search", "Search posts", r.status_code, 200); n += 1

        # ── 13. RECRUITERS ──────────────────────────────────────────────────
        unique_domain = f"stripe_{uuid.uuid4().hex[:6]}.com"
        r = await client.post("/api/v1/recruiters/company", headers=recruiter_hdr, json={
            "name": f"Stripe Payments {uuid.uuid4().hex[:4]}", "domain": unique_domain, "description": "Global financial infrastructure"
        })
        record(n, "POST", "/api/v1/recruiters/company", "Create company", r.status_code, 201); n += 1

        r = await client.post("/api/v1/recruiters/jobs", headers=recruiter_hdr, json={
            "title": "Software Engineer II", "description": "Backend API engineer"
        })
        record(n, "POST", "/api/v1/recruiters/jobs", "Post new job", r.status_code, 201)
        job_id = r.json()["id"] if r.status_code == 201 else dummy_id
        n += 1

        r = await client.get("/api/v1/recruiters/jobs", headers=recruiter_hdr)
        record(n, "GET", "/api/v1/recruiters/jobs", "List company jobs", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/recruiters/jobs/{job_id}/apply", headers=student_hdr)
        record(n, "POST", "/api/v1/recruiters/jobs/{job_id}/apply", "Apply for job", r.status_code, 201)
        application_id = r.json()["id"] if r.status_code == 201 else dummy_id
        n += 1

        r = await client.get(f"/api/v1/recruiters/jobs/{job_id}/applications", headers=recruiter_hdr)
        record(n, "GET", "/api/v1/recruiters/jobs/{job_id}/applications", "View job applications", r.status_code, 200); n += 1

        r = await client.patch(f"/api/v1/recruiters/applications/{application_id}", headers=recruiter_hdr, json={
            "status": "Shortlisted"
        })
        record(n, "PATCH", "/api/v1/recruiters/applications/{application_id}", "Update application status", r.status_code, 200); n += 1

        # ── 14. PLACEMENTS ──────────────────────────────────────────────────
        unique_college_domain = f"stanford_{uuid.uuid4().hex[:6]}.edu"
        r = await client.post("/api/v1/placements/colleges", headers=officer_hdr, json={
            "name": f"Stanford University {uuid.uuid4().hex[:4]}", "domain": unique_college_domain, "address": "Stanford, CA"
        })
        record(n, "POST", "/api/v1/placements/colleges", "Create college & register officer", r.status_code, 201); n += 1

        r = await client.post("/api/v1/placements/drives", headers=officer_hdr, json={
            "title": "Autumn Tech Placement Drive 2026", "drive_type": "Campus"
        })
        record(n, "POST", "/api/v1/placements/drives", "Create placement drive", r.status_code, 201)
        drive_id = r.json()["id"] if r.status_code == 201 else dummy_id
        n += 1

        r = await client.get("/api/v1/placements/drives", headers=officer_hdr)
        record(n, "GET", "/api/v1/placements/drives", "List college placement drives", r.status_code, 200); n += 1

        r = await client.get(f"/api/v1/placements/drives/{drive_id}", headers=officer_hdr)
        record(n, "GET", "/api/v1/placements/drives/{drive_id}", "Get placement drive details", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/placements/drives/{drive_id}/calculate-eligibility", headers=officer_hdr)
        record(n, "POST", "/api/v1/placements/drives/{drive_id}/calculate-eligibility", "Trigger drive eligibility calculation", r.status_code, [200, 202]); n += 1

        r = await client.post(f"/api/v1/placements/drives/{drive_id}/register", headers=student_hdr)
        record(n, "POST", "/api/v1/placements/drives/{drive_id}/register", "Student registers for drive", r.status_code, 201)
        reg_id = r.json()["id"] if r.status_code == 201 else dummy_id
        n += 1

        r = await client.get(f"/api/v1/placements/drives/{drive_id}/registrations", headers=officer_hdr)
        record(n, "GET", "/api/v1/placements/drives/{drive_id}/registrations", "List drive registrations", r.status_code, 200); n += 1

        r = await client.patch(f"/api/v1/placements/registrations/{reg_id}", headers=officer_hdr, json={"status": "Shortlisted"})
        record(n, "PATCH", "/api/v1/placements/registrations/{registration_id}", "Update student drive registration", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/placements/registrations/{reg_id}/offer", headers=officer_hdr, json={
            "package_details": "Software Engineer at Google - $150,000 CTC"
        })
        record(n, "POST", "/api/v1/placements/registrations/{registration_id}/offer", "Release offer letter", r.status_code, 201); n += 1

        r = await client.post(f"/api/v1/placements/drives/{drive_id}/rank", headers=officer_hdr)
        record(n, "POST", "/api/v1/placements/drives/{drive_id}/rank", "Trigger student ranking background task", r.status_code, 202); n += 1

        # ── 15. ADMIN ───────────────────────────────────────────────────────
        r = await client.get("/api/v1/admin/dashboard/summary", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/dashboard/summary", "Admin dashboard summary", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/health/check", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/health/check", "Admin system health check", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/health/snapshots", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/health/snapshots", "Get health snapshots", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/audit/logs", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/audit/logs", "Get platform audit logs", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/roles", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/roles", "Get all system roles", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/permissions", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/permissions", "Get all system permissions", r.status_code, 200); n += 1

        r = await client.post("/api/v1/admin/flags", headers=admin_hdr, json={
            "key": f"ai_mock_interviews_{uuid.uuid4().hex[:4]}", "description": "Enable V2 interview voice pipeline", "is_enabled": True
        })
        record(n, "POST", "/api/v1/admin/flags", "Create feature flag", r.status_code, 200)
        flag_id = r.json()["id"] if r.status_code == 200 else dummy_id
        n += 1

        r = await client.get("/api/v1/admin/flags", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/flags", "List all feature flags", r.status_code, 200); n += 1

        r = await client.put(f"/api/v1/admin/flags/{flag_id}", headers=admin_hdr, json={"is_enabled": False})
        record(n, "PUT", "/api/v1/admin/flags/{flag_id}", "Update feature flag", r.status_code, 200); n += 1

        setting_key = f"max_upload_size_{uuid.uuid4().hex[:4]}"
        r = await client.post("/api/v1/admin/settings", headers=admin_hdr, json={
            "key": setting_key, "value": "10485760", "description": "Max file upload size in bytes"
        })
        record(n, "POST", "/api/v1/admin/settings", "Create platform setting", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/settings", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/settings", "Get all platform settings", r.status_code, 200); n += 1

        r = await client.put(f"/api/v1/admin/settings/{setting_key}", headers=admin_hdr, json={"value": "20971520"})
        record(n, "PUT", "/api/v1/admin/settings/{key}", "Update platform setting", r.status_code, 200); n += 1

        provider_name = f"openai_provider_{uuid.uuid4().hex[:4]}"
        r = await client.post("/api/v1/admin/ai/providers", headers=admin_hdr, json={
            "name": provider_name, "provider_type": "openai", "api_key": "sk-mock-key"
        })
        record(n, "POST", "/api/v1/admin/ai/providers", "Register AI provider", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/ai/providers", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/ai/providers", "List AI providers", r.status_code, 200); n += 1

        r = await client.put(f"/api/v1/admin/ai/providers/{provider_name}", headers=admin_hdr, json={"is_active": True})
        record(n, "PUT", "/api/v1/admin/ai/providers/{name}", "Update AI provider", r.status_code, 200); n += 1

        model_name = f"gpt-4o-mini_{uuid.uuid4().hex[:4]}"
        r = await client.post("/api/v1/admin/ai/models", headers=admin_hdr, json={
            "model_name": model_name, "provider_name": provider_name, "temperature": 0.7, "max_tokens": 2048
        })
        record(n, "POST", "/api/v1/admin/ai/models", "Register AI model", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/ai/models", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/ai/models", "List AI models", r.status_code, 200); n += 1

        r = await client.put(f"/api/v1/admin/ai/models/{model_name}", headers=admin_hdr, json={"temperature": 0.8})
        record(n, "PUT", "/api/v1/admin/ai/models/{model_name}", "Update AI model config", r.status_code, 200); n += 1

        prompt_module = f"mentor_{uuid.uuid4().hex[:4]}"
        r = await client.post("/api/v1/admin/ai/prompts", headers=admin_hdr, json={
            "module": prompt_module, "prompt_name": "system_prompt", "template": "You are a senior tech mentor."
        })
        record(n, "POST", "/api/v1/admin/ai/prompts", "Create AI prompt template", r.status_code, 200); n += 1

        r = await client.post("/api/v1/admin/ai/prompts/versions", headers=admin_hdr, json={
            "module": prompt_module, "version": "1.1", "prompt_text": "You are an empathetic senior mentor."
        })
        record(n, "POST", "/api/v1/admin/ai/prompts/versions", "Create prompt version", r.status_code, 200); n += 1

        r = await client.post("/api/v1/admin/ai/prompts/rollback", headers=admin_hdr, params={"module": prompt_module, "version": "1.1"})
        record(n, "POST", "/api/v1/admin/ai/prompts/rollback", "Rollback prompt template", r.status_code, 200); n += 1

        r = await client.get(f"/api/v1/admin/ai/prompts/{prompt_module}/versions", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/ai/prompts/{module}/versions", "Get prompt versions", r.status_code, 200); n += 1

        r = await client.post("/api/v1/admin/ai/testing/test", headers=admin_hdr, json={
            "provider_name": "openai", "model_name": "gpt-4", "prompt_text": "Hello world"
        })
        record(n, "POST", "/api/v1/admin/ai/testing/test", "Test AI provider/model", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/moderation/queue", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/moderation/queue", "Get moderation queue", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/admin/moderation/queue/{ids['mod_item_id']}/decision", headers=admin_hdr, json={
            "decision": "approve", "reason": "Content is clean"
        })
        record(n, "POST", "/api/v1/admin/moderation/queue/{item_id}/decision", "Submit moderation decision", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/monitoring/jobs", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/monitoring/jobs", "Get background job history", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/monitoring/resources", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/monitoring/resources", "Get system resource metrics", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/maintenance/status", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/maintenance/status", "Get maintenance window status", r.status_code, 200); n += 1

        r = await client.post("/api/v1/admin/maintenance/schedule", headers=admin_hdr, json={
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "reason": "Scheduled database indexing"
        })
        record(n, "POST", "/api/v1/admin/maintenance/schedule", "Schedule maintenance window", r.status_code, 200); n += 1

        r = await client.get("/api/v1/admin/announcements/active", headers=admin_hdr)
        record(n, "GET", "/api/v1/admin/announcements/active", "Get active announcements", r.status_code, 200); n += 1

        r = await client.post("/api/v1/admin/announcements", headers=admin_hdr, json={
            "title": "Welcome to CareerOS 2.0!", "content": "All backend systems verified and online.", "severity": "info"
        })
        record(n, "POST", "/api/v1/admin/announcements", "Create system announcement", r.status_code, 200); n += 1

        r = await client.post("/api/v1/admin/broadcast", headers=admin_hdr, json={
            "title": "Platform Maintenance Tonight", "content": "Brief maintenance window at 2 AM UTC.", "recipient_type": "all"
        })
        record(n, "POST", "/api/v1/admin/broadcast", "Broadcast push notification", r.status_code, 200); n += 1

        r = await client.post(f"/api/v1/admin/users/{ids['student_user_id']}/roles/assign", headers=admin_hdr, json={"role_name": "student"})
        record(n, "POST", "/api/v1/admin/users/{user_id}/roles/assign", "Assign role to user", r.status_code, 200); n += 1

        r = await client.put(f"/api/v1/admin/users/{ids['student_user_id']}/status", headers=admin_hdr, json={"status": "ACTIVE"})
        record(n, "PUT", "/api/v1/admin/users/{user_id}/status", "Update user account status", r.status_code, 200); n += 1

        # ── 16. ERROR HANDLING VALIDATION ────────────────────────────────────
        # Missing auth
        r = await client.get("/api/v1/users/me/profile")
        record(n, "GET", "/api/v1/users/me/profile", "Error check: unauthenticated -> 401", r.status_code, 401); n += 1

        # Missing required body field
        r = await client.post("/api/v1/auth/login", json={"email": "incomplete@user.com"})
        record(n, "POST", "/api/v1/auth/login", "Error check: missing password -> 422", r.status_code, 422); n += 1

        # Invalid JSON body
        r = await client.post("/api/v1/auth/register", content=b"invalid json", headers={"Content-Type": "application/json"})
        record(n, "POST", "/api/v1/auth/register", "Error check: malformed json -> 422", r.status_code, 422); n += 1

        # Non-existent resource
        r = await client.get(f"/api/v1/placements/drives/{uuid.uuid4()}", headers=officer_hdr)
        record(n, "GET", "/api/v1/placements/drives/{drive_id}", "Error check: non-existent drive -> 404", r.status_code, 404); n += 1

        # Wrong file type
        r = await client.post("/api/v1/resumes/upload", headers=student_hdr, files={"file": ("malicious.exe", b"binary", "application/x-msdownload")})
        record(n, "POST", "/api/v1/resumes/upload", "Error check: invalid file type -> 400", r.status_code, 400); n += 1

    print("\n" + "="*80)
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed
    print(f"VERIFICATION COMPLETE: {total} tests run, {passed} PASSED, {failed} FAILED")
    print("="*80)

    with open("endpoint_verification_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
