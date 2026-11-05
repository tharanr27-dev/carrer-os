# Career OS - Complete API Endpoint Inventory (124 routes)

Extracted from the running FastAPI application object (paths, methods and authentication dependencies are the real ones). Prefix `/api/v1` applies to all except health and metrics.

| Method | Path | Authentication |
|---|---|---|
| POST | `/api/v1/auth/login` | Public |
| POST | `/api/v1/auth/register` | Public |
| POST | `/api/v1/auth/refresh` | Public |
| GET | `/api/v1/auth/me` | Login (JWT) |
| GET | `/api/v1/users/me/profile` | Login (JWT) |
| PUT | `/api/v1/users/me/profile` | Login (JWT) |
| GET | `/api/v1/discovery/templates` | Login (JWT) |
| POST | `/api/v1/discovery/assessments/{template_id}/submit` | Login (JWT) |
| GET | `/api/v1/discovery/reports/{report_id}` | Login (JWT) |
| GET | `/api/v1/resumes` | Login (JWT) |
| POST | `/api/v1/resumes/upload` | Login (JWT) |
| GET | `/api/v1/resumes/{resume_id}/analysis` | Login (JWT) |
| GET | `/api/v1/resumes/{resume_id}/download` | Login (JWT) |
| POST | `/api/v1/mentor/sessions` | Login (JWT) |
| GET | `/api/v1/mentor/sessions/latest` | Login (JWT) |
| GET | `/api/v1/mentor/status` | Login (JWT) |
| GET | `/api/v1/mentor/suggestions` | Login (JWT) |
| GET | `/api/v1/mentor/goals` | Login (JWT) |
| POST | `/api/v1/mentor/sessions/{session_id}/message` | Login (JWT) |
| POST | `/api/v1/mentor/goals` | Login (JWT) |
| POST | `/api/v1/interviews/sessions` | Login (JWT) |
| GET | `/api/v1/interviews/sessions/{session_id}/report` | Login (JWT) |
| WS | `/api/v1/interviews/ws/{session_id}` | Token in ?token= |
| POST | `/api/v1/communication/sessions` | Login (JWT) |
| GET | `/api/v1/communication/sessions/{session_id}/report` | Login (JWT) |
| WS | `/api/v1/communication/ws/{session_id}` | Token in ?token= |
| POST | `/api/v1/learning/roadmaps/generate` | Login (JWT) |
| GET | `/api/v1/learning/roadmaps/active` | Login (JWT) |
| POST | `/api/v1/learning/tasks/complete` | Login (JWT) |
| POST | `/api/v1/recommendations/refresh` | Login (JWT) |
| GET | `/api/v1/recommendations/feed` | Login (JWT) |
| POST | `/api/v1/recommendations/feedback` | Login (JWT) |
| POST | `/api/v1/analytics/events` | Login (JWT) |
| POST | `/api/v1/analytics/ai-usage` | Login (JWT) |
| GET | `/api/v1/analytics/dashboard/student` | Login (JWT) |
| POST | `/api/v1/community/posts` | Login (JWT) |
| GET | `/api/v1/community/posts/{post_id}` | Login (JWT) |
| POST | `/api/v1/community/posts/{post_id}/comments` | Login (JWT) |
| GET | `/api/v1/community/posts/{post_id}/comments` | Login (JWT) |
| POST | `/api/v1/community/reactions` | Login (JWT) |
| GET | `/api/v1/community/feed/trending` | Login (JWT) |
| GET | `/api/v1/community/feed/latest` | Login (JWT) |
| GET | `/api/v1/community/search` | Login (JWT) |
| POST | `/api/v1/recruiters/company` | Login (JWT) |
| POST | `/api/v1/recruiters/jobs` | Login + recruiter (company member) |
| GET | `/api/v1/recruiters/jobs/open` | Login (JWT) |
| GET | `/api/v1/recruiters/applications/mine` | Login (JWT) |
| GET | `/api/v1/recruiters/jobs` | Login + recruiter (company member) |
| POST | `/api/v1/recruiters/jobs/{job_id}/apply` | Login (JWT) |
| GET | `/api/v1/recruiters/jobs/{job_id}/applications` | Login + recruiter (company member) |
| PATCH | `/api/v1/recruiters/applications/{application_id}` | Login + recruiter (company member) |
| POST | `/api/v1/placements/colleges` | Login (JWT) |
| POST | `/api/v1/placements/drives` | Login + placement officer (college member) |
| GET | `/api/v1/placements/drives` | Login + placement officer (college member) |
| GET | `/api/v1/placements/drives/available` | Login (JWT) |
| GET | `/api/v1/placements/registrations/mine` | Login (JWT) |
| GET | `/api/v1/placements/drives/{drive_id}` | Login + placement officer (college member) |
| POST | `/api/v1/placements/drives/{drive_id}/calculate-eligibility` | Login + placement officer (college member) |
| POST | `/api/v1/placements/drives/{drive_id}/register` | Login (JWT) |
| GET | `/api/v1/placements/drives/{drive_id}/registrations` | Login + placement officer (college member) |
| PATCH | `/api/v1/placements/registrations/{registration_id}` | Login + placement officer (college member) |
| POST | `/api/v1/placements/registrations/{registration_id}/offer` | Login + placement officer (college member) |
| POST | `/api/v1/placements/drives/{drive_id}/rank` | Login + placement officer (college member) |
| GET | `/api/v1/jobs/recommended` | Login (JWT) |
| GET | `/api/v1/training/meta` | Login (JWT) |
| GET | `/api/v1/training/profile` | Login (JWT) |
| PUT | `/api/v1/training/profile` | Login (JWT) |
| GET | `/api/v1/training/questions` | Login (JWT) |
| POST | `/api/v1/training/attempts` | Login (JWT) |
| GET | `/api/v1/training/attempts` | Login (JWT) |
| GET | `/api/v1/training/attempts/{attempt_id}` | Login (JWT) |
| POST | `/api/v1/training/attempts/{attempt_id}/answer` | Login (JWT) |
| POST | `/api/v1/training/attempts/{attempt_id}/next` | Login (JWT) |
| POST | `/api/v1/training/attempts/{attempt_id}/finish` | Login (JWT) |
| GET | `/api/v1/training/progress` | Login (JWT) |
| GET | `/api/v1/training/roles` | Login (JWT) |
| POST | `/api/v1/training/roles/resolve` | Login (JWT) |
| GET | `/api/v1/training/roles/progress` | Login (JWT) |
| POST | `/api/v1/training/role-sessions` | Login (JWT) |
| GET | `/api/v1/training/role-sessions` | Login (JWT) |
| GET | `/api/v1/training/role-sessions/{session_id}` | Login (JWT) |
| POST | `/api/v1/training/role-sessions/{session_id}/answer` | Login (JWT) |
| POST | `/api/v1/training/role-sessions/{session_id}/finish` | Login (JWT) |
| GET | `/api/v1/training/role-sessions/{session_id}/review` | Login (JWT) |
| POST | `/api/v1/training/role-sessions/{session_id}/again` | Login (JWT) |
| POST | `/api/v1/admin/settings` | Login + permission admin:write |
| PUT | `/api/v1/admin/settings/{key}` | Login + permission admin:write |
| GET | `/api/v1/admin/settings` | Login + permission admin:read |
| POST | `/api/v1/admin/flags` | Login + permission admin:write |
| PUT | `/api/v1/admin/flags/{flag_id}` | Login + permission admin:write |
| GET | `/api/v1/admin/flags` | Login + permission admin:read |
| POST | `/api/v1/admin/ai/providers` | Login + permission admin:write |
| PUT | `/api/v1/admin/ai/providers/{name}` | Login + permission admin:write |
| GET | `/api/v1/admin/ai/providers` | Login + permission admin:read |
| POST | `/api/v1/admin/ai/prompts` | Login + permission admin:write |
| POST | `/api/v1/admin/ai/prompts/versions` | Login + permission admin:write |
| POST | `/api/v1/admin/ai/prompts/rollback` | Login + permission admin:write |
| GET | `/api/v1/admin/moderation/queue` | Login + permission admin:moderator |
| POST | `/api/v1/admin/moderation/queue/{item_id}/decision` | Login + permission admin:moderator |
| POST | `/api/v1/admin/announcements` | Login + permission admin:write |
| POST | `/api/v1/admin/broadcast` | Login + permission admin:write |
| GET | `/api/v1/admin/health/check` | Login + permission admin:read |
| GET | `/api/v1/admin/users` | Login + permission admin:read |
| PUT | `/api/v1/admin/users/{user_id}/status` | Login + permission admin:write |
| POST | `/api/v1/admin/maintenance/schedule` | Login + permission admin:write |
| GET | `/api/v1/admin/dashboard/summary` | Login + permission admin:read |
| POST | `/api/v1/admin/ai/testing/test` | Login + permission admin:write |
| GET | `/api/v1/admin/audit/logs` | Login + permission admin:read |
| GET | `/api/v1/admin/health/snapshots` | Login + permission admin:read |
| GET | `/api/v1/admin/monitoring/resources` | Login + permission admin:read |
| GET | `/api/v1/admin/monitoring/jobs` | Login + permission admin:read |
| GET | `/api/v1/admin/roles` | Login + permission admin:read |
| GET | `/api/v1/admin/permissions` | Login + permission admin:read |
| POST | `/api/v1/admin/users/{user_id}/roles/assign` | Login + permission admin:write |
| POST | `/api/v1/admin/ai/models` | Login + permission admin:write |
| PUT | `/api/v1/admin/ai/models/{model_name}` | Login + permission admin:write |
| GET | `/api/v1/admin/ai/models` | Login + permission admin:read |
| GET | `/api/v1/admin/announcements/active` | Login (JWT) |
| GET | `/api/v1/admin/maintenance/status` | Login + permission admin:read |
| GET | `/api/v1/admin/ai/prompts/{module}/versions` | Login + permission admin:read |
| GET | `/health` | Public |
| GET | `/health/live` | Public |
| GET | `/health/ready` | Public |
| GET | `/metrics` | Public |
