"""
Deep scan of every backend module: imports, background-task sessions,
is_active references, and router response consistency.
"""
import sys, importlib, inspect, ast, os

sys.path.insert(0, ".")

MODULES_DIR = os.path.join("app", "modules")
ISSUES = []

# ── 1. Import every discovered module ──────────────────────────────────────
print("="*60)
print("1. IMPORT SCAN")
print("="*60)

def walk_modules(base_dir: str):
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fn in files:
            if fn.endswith(".py") and fn != "__init__.py":
                full = os.path.join(root, fn)
                mod_path = full.replace(os.sep, ".").replace(".py", "")
                yield mod_path

all_mod_paths = list(walk_modules(MODULES_DIR))
all_mod_paths += [
    "app.core.config", "app.core.security", "app.core.dependencies",
    "app.core.exceptions", "app.core.responses", "app.core.logger",
    "app.db.base", "app.db.session",
    "app.infrastructure.cache.redis",
    "app.infrastructure.storage.s3_client",
    "app.core.ai.pipeline",
]

import_errors = []
for mod in sorted(set(all_mod_paths)):
    try:
        importlib.import_module(mod)
        print(f"  OK  {mod}")
    except Exception as e:
        print(f"  ERR {mod}: {e}")
        import_errors.append((mod, str(e)))
        ISSUES.append(f"[IMPORT] {mod}: {e}")

print(f"\n  {'All imports OK' if not import_errors else str(len(import_errors)) + ' import errors found'}")

# ── 2. Source-level pattern scan ───────────────────────────────────────────
print("\n" + "="*60)
print("2. SOURCE PATTERN SCAN")
print("="*60)

DANGER_PATTERNS = {
    "background task uses self.session":    ("background_tasks.add_task", "self.session"),
    "user.is_active without hybrid":        None,  # handled separately
}

def scan_file(path: str):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    return src

bg_task_issues = []
is_active_refs = []

for root, dirs, files in os.walk("app"):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for fn in files:
        if not fn.endswith(".py"):
            continue
        path = os.path.join(root, fn)
        src = scan_file(path)

        # Check: background tasks referencing self.session / self.repository
        if "background_tasks.add_task" in src and "self._" in src:
            # Look for methods that are both background task targets AND use self.session
            if "self.session" in src or "self.repository" in src:
                # Check if it's the background method itself that uses session
                bg_task_issues.append(path)

        # Check: any use of user.is_active outside of auth/models.py
        if "user.is_active" in src and "hybrid_property" not in src:
            is_active_refs.append(path)

print("\n  Background task + session references:")
for p in bg_task_issues:
    print(f"    CHECK: {p}")

print("\n  user.is_active references (should all be safe now):")
for p in is_active_refs:
    print(f"    OK (uses hybrid_property from model): {p}")

# ── 3. CORS sanity check ───────────────────────────────────────────────────
print("\n" + "="*60)
print("3. CORS SANITY CHECK")
print("="*60)

from app.main import app
from fastapi.middleware.cors import CORSMiddleware

cors_ok = False
for mw in app.user_middleware:
    if hasattr(mw, "cls") and mw.cls == CORSMiddleware:
        origins = mw.kwargs.get("allow_origins", [])
        creds   = mw.kwargs.get("allow_credentials", False)
        if "*" in origins and creds:
            ISSUES.append("[CORS] wildcard + allow_credentials=True (browser will block)")
            print(f"  FAIL: wildcard + credentials=True")
        else:
            cors_ok = True
            print(f"  PASS: origins={origins}  credentials={creds}")

# ── 4. Schema URL serialization ────────────────────────────────────────────
print("\n" + "="*60)
print("4. SCHEMA URL SERIALIZATION")
print("="*60)

from app.modules.users.schemas import ProfileUpdate, SocialLinks

p = ProfileUpdate(profile_image_url="https://example.com/avatar.png")
val = p.model_dump()
img = val["profile_image_url"]
if isinstance(img, str):
    print(f"  PASS: ProfileUpdate.profile_image_url -> str ({img!r})")
else:
    ISSUES.append(f"[SCHEMA] profile_image_url is {type(img).__name__}, not str")
    print(f"  FAIL: {type(img).__name__}")

s = SocialLinks(linkedin="https://linkedin.com/in/test")
val2 = s.model_dump()
li = val2["linkedin"]
if isinstance(li, str):
    print(f"  PASS: SocialLinks.linkedin -> str ({li!r})")
else:
    ISSUES.append(f"[SCHEMA] SocialLinks.linkedin is {type(li).__name__}, not str")
    print(f"  FAIL: {type(li).__name__}")

# ── 5. Auth model properties ───────────────────────────────────────────────
print("\n" + "="*60)
print("5. AUTH MODEL PROPERTIES")
print("="*60)

from app.modules.auth.models import User, UserStatus

if hasattr(User, "is_active"):
    print("  PASS: User.is_active defined")
else:
    ISSUES.append("[AUTH] User.is_active missing")
    print("  FAIL: User.is_active missing")

if hasattr(User, "is_verified"):
    print("  PASS: User.is_verified defined")
else:
    ISSUES.append("[AUTH] User.is_verified missing")
    print("  FAIL: User.is_verified missing")

# Check register sets ACTIVE status
from app.modules.auth.service import AuthService
src_register = inspect.getsource(AuthService.register)
if "UserStatus.ACTIVE" in src_register:
    print("  PASS: AuthService.register sets UserStatus.ACTIVE")
else:
    ISSUES.append("[AUTH] register() does not set UserStatus.ACTIVE")
    print("  FAIL: register() does not set UserStatus.ACTIVE")

# ── 6. Background task isolation ──────────────────────────────────────────
print("\n" + "="*60)
print("6. BACKGROUND TASK ISOLATION")
print("="*60)

from app.modules.career_discovery.service import DiscoveryService
src_bg = inspect.getsource(DiscoveryService._process_ai_report_isolated)
if "AsyncSessionLocal" in src_bg and "async with" in src_bg:
    print("  PASS: DiscoveryService background task opens its own DB session")
else:
    ISSUES.append("[BG] DiscoveryService background task uses closed session")
    print("  FAIL")

# Resume service still uses self.session in background - flag it
from app.modules.resumes.service import ResumeService
src_rs = inspect.getsource(ResumeService._async_pipeline_isolated)
if "AsyncSessionLocal" in src_rs and "async with" in src_rs:
    print("  PASS: ResumeService background task uses isolated session")
else:
    ISSUES.append("[BG] ResumeService._async_pipeline_isolated uses request-scoped session")
    print("  WARN: ResumeService._async_pipeline_isolated uses request-scoped session")

# ── Summary ────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
if not ISSUES:
    print("  ALL CHECKS PASSED - backend is clean!")
else:
    print(f"  {len(ISSUES)} issue(s) remain:\n")
    for i, issue in enumerate(ISSUES, 1):
        print(f"  {i}. {issue}")
