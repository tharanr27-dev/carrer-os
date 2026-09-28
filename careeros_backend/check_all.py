import sys
sys.path.insert(0, '.')

print("=== BACKEND FULL CHECKUP ===\n")

issues = []

# 1. Check User model is_active / is_verified
from app.modules.auth.models import User, UserStatus
from sqlalchemy import inspect

mapper = inspect(User)
col_names = [c.key for c in mapper.mapper.column_attrs]
print(f"[User Model] Columns: {col_names}")

if 'is_active' not in col_names:
    issues.append("CRITICAL: User model has no 'is_active' column. auth/service.py L27 and core/dependencies.py L43 reference user.is_active -> will raise AttributeError")
if 'is_verified' not in col_names:
    issues.append("CRITICAL: User model has no 'is_verified' column. UserResponse schema uses is_verified but it doesn't exist on User model")

# 2. Check ProfileUpdate HttpUrl serialization  
from app.modules.users.schemas import ProfileUpdate

try:
    p = ProfileUpdate(profile_image_url='https://example.com/image.jpg')
    val = p.model_dump()
    img_val = val["profile_image_url"]
    print(f"[ProfileUpdate] profile_image_url serializes as: {img_val} (type: {type(img_val).__name__})")
    if not isinstance(img_val, str):
        issues.append(f"BUG: ProfileUpdate.profile_image_url serializes as {type(img_val).__name__} not str - will fail DB assignment")
    else:
        print("  OK: serializes as str")
except Exception as e:
    issues.append(f"ProfileUpdate error: {e}")

# 3. Check SocialLinks HttpUrl serialization
from app.modules.users.schemas import SocialLinks

try:
    s = SocialLinks(linkedin='https://linkedin.com/in/test')
    val = s.model_dump()
    linkedin_val = val["linkedin"]
    print(f"[SocialLinks] linkedin serializes as: {linkedin_val} (type: {type(linkedin_val).__name__})")
    if not isinstance(linkedin_val, str):
        issues.append(f"BUG: SocialLinks.linkedin serializes as {type(linkedin_val).__name__} not str - will fail JSON serialization to DB JSONB")
    else:
        print("  OK: serializes as str")
except Exception as e:
    issues.append(f"SocialLinks error: {e}")

# 4. Test UserStatus based is_active logic
u = User(status=UserStatus.ACTIVE)
is_active_via_status = u.status == UserStatus.ACTIVE
print(f"[UserStatus] ACTIVE check via status: {is_active_via_status}")

# 5. Check CORS config (wildcard + credentials is incompatible in some browsers)
print(f"\n[CORS] allow_origins=['*'] with allow_credentials=True -> BUG: Browsers reject wildcard with credentials")
issues.append("BUG: CORSMiddleware configured with allow_origins=['*'] AND allow_credentials=True - browsers reject this combination. Must use explicit origins.")

# 6. Check middleware ordering: CORSMiddleware must be outermost for preflight to work
print("[Middleware Order] RateLimitMiddleware added AFTER CORSMiddleware -> middleware execution order in Starlette is LIFO")
issues.append("WARN: Middleware ordering: RateLimitMiddleware wraps CORSMiddleware. Rate limiter blocks preflight requests before CORS headers are set. CORSMiddleware must be the outermost middleware.")

# 7. Check oauth2 tokenUrl for frontend login compatibility  
print("\n[OAuth2] tokenUrl='/api/v1/auth/login' - using JSON not form-data")
print("  The /auth/login endpoint accepts UserLogin (JSON), not OAuth2PasswordRequestForm (form-data)")
print("  This is OK for custom frontend but swagger UI 'Authorize' button won't work directly")

# 8. Check background task session usage
print("\n[BackgroundTasks] DiscoveryService._process_ai_report uses closed session -> will fail after response")
issues.append("CRITICAL: DiscoveryService._process_ai_report runs as background task using the request-scoped DB session that will be CLOSED after the response is sent. Needs its own session.")

# Summary
print("\n" + "="*50)
print("ISSUES FOUND:")
for i, issue in enumerate(issues, 1):
    print(f"  {i}. {issue}")
print(f"\nTotal: {len(issues)} issues")
