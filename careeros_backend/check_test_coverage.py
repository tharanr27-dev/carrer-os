import re
import sys

sys.path.insert(0, ".")
from app.main import app

backend_routes = []
for r in app.routes:
    methods = getattr(r, "methods", None)
    path = getattr(r, "path", None)
    if methods and path:
        for m in methods:
            if m not in ("HEAD", "OPTIONS"):
                backend_routes.append((m, path))

with open("verify_all_endpoints.py", "r", encoding="utf-8") as f:
    verify_code = f.read()

# Find all client.<method>("<path>" or record(..., "<method>", "<path>")
tested = set()
for m in re.finditer(r'record\(\s*[^,]+,\s*["\']([A-Z]+)["\'],\s*["\']([^"\']+)["\']', verify_code):
    method, path = m.group(1), m.group(2)
    # clean parameterized paths: e.g. /discovery/reports/{report_id}
    tested.add((method, path))

print(f"Total backend routes: {len(backend_routes)}")
print(f"Tested in verify_all_endpoints.py: {len(tested)}")

not_tested = []
for m, p in backend_routes:
    # check exact match or regex
    # replace {param} with {.*}
    matched = False
    for tm, tp in tested:
        if m == tm:
            norm_p = re.sub(r"\{[^}]+\}", "*", p)
            norm_tp = re.sub(r"\{[^}]+\}", "*", tp)
            if norm_p == norm_tp:
                matched = True
                break
    if not matched:
        not_tested.append((m, p))

print(f"\nRoutes NOT yet in verify_all_endpoints.py: {len(not_tested)}")
for m, p in sorted(not_tested):
    print(f"  [{m:<6}] {p}")
