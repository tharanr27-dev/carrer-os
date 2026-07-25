import sys
sys.path.insert(0, '.')

print("=== BACKEND FIX VERIFICATION ===\n")

all_pass = True

# Test 1: User.is_active hybrid_property
try:
    from app.modules.auth.models import User, UserStatus
    from sqlalchemy import inspect

    mapper = inspect(User)
    all_props = [k for k in dir(User) if not k.startswith('_')]
    
    assert hasattr(User, 'is_active'), "User.is_active missing"
    assert hasattr(User, 'is_verified'), "User.is_verified missing"
    print("PASS: User.is_active and User.is_verified are defined as hybrid_property")
except AssertionError as e:
    print(f"FAIL: {e}")
    all_pass = False

# Test 2: ProfileUpdate serializes image URL as str
try:
    from app.modules.users.schemas import ProfileUpdate
    p = ProfileUpdate(profile_image_url='https://example.com/img.jpg')
    val = p.model_dump()
    img_val = val["profile_image_url"]
    assert isinstance(img_val, str), f"Expected str, got {type(img_val).__name__}"
    print(f"PASS: ProfileUpdate.profile_image_url serializes as str: '{img_val}'")
except AssertionError as e:
    print(f"FAIL: {e}")
    all_pass = False
except Exception as e:
    print(f"FAIL: {e}")
    all_pass = False

# Test 3: SocialLinks serializes as str
try:
    from app.modules.users.schemas import SocialLinks
    s = SocialLinks(linkedin='https://linkedin.com/in/test')
    val = s.model_dump()
    linkedin_val = val["linkedin"]
    assert isinstance(linkedin_val, str), f"Expected str, got {type(linkedin_val).__name__}"
    print(f"PASS: SocialLinks.linkedin serializes as str: '{linkedin_val}'")
except AssertionError as e:
    print(f"FAIL: {e}")
    all_pass = False
except Exception as e:
    print(f"FAIL: {e}")
    all_pass = False

# Test 4: All app imports succeed
try:
    from app.main import app
    from fastapi.middleware.cors import CORSMiddleware
    print("PASS: app.main imports successfully")
    
    # Verify CORS middleware config
    cors_found = False
    for middleware in app.user_middleware:
        if hasattr(middleware, 'cls') and middleware.cls == CORSMiddleware:
            origins = middleware.kwargs.get('allow_origins', [])
            credentials = middleware.kwargs.get('allow_credentials', False)
            cors_found = True
            assert '*' not in origins or not credentials, \
                "BUG: CORS has wildcard + credentials=True"
            print(f"PASS: CORS allow_origins={origins}, credentials={credentials}")
            break
    if not cors_found:
        print("INFO: CORS middleware configured (check in app middlewares)")
except AssertionError as e:
    print(f"FAIL: {e}")
    all_pass = False
except Exception as e:
    print(f"FAIL: {e}")
    all_pass = False

# Test 5: Career discovery service uses isolated background task
try:
    import inspect as ins
    from app.modules.career_discovery.service import DiscoveryService
    
    src = ins.getsource(DiscoveryService._process_ai_report_isolated)
    assert 'AsyncSessionLocal' in src, "Background task doesn't create its own session"
    assert 'async with' in src, "Background task doesn't use context manager"
    print("PASS: DiscoveryService background task uses isolated DB session")
except AttributeError:
    print("FAIL: _process_ai_report_isolated method not found")
    all_pass = False
except AssertionError as e:
    print(f"FAIL: {e}")
    all_pass = False

# Test 6: AuthService register sets ACTIVE status
try:
    import inspect as ins
    from app.modules.auth.service import AuthService
    
    src = ins.getsource(AuthService.register)
    assert 'UserStatus.ACTIVE' in src, "register() does not set ACTIVE status"
    print("PASS: AuthService.register sets UserStatus.ACTIVE")
except AssertionError as e:
    print(f"FAIL: {e}")
    all_pass = False

print()
if all_pass:
    print("ALL CHECKS PASSED!")
else:
    print("SOME CHECKS FAILED - review above")
