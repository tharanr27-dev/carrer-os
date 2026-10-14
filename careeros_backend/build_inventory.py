import os
import re
import json

frontend_dir = "../frontend"

# Read frontend/lib/api.ts
with open(os.path.join(frontend_dir, "lib", "api.ts"), "r", encoding="utf-8") as f:
    api_ts = f.read()

# Read all UI files
ui_files = {}
for root, dirs, files in os.walk(frontend_dir):
    if "node_modules" in root or ".next" in root:
        continue
    for file in files:
        if file.endswith((".ts", ".tsx")) and not file.endswith("api.ts"):
            full_p = os.path.join(root, file)
            with open(full_p, "r", encoding="utf-8", errors="ignore") as f:
                ui_files[os.path.relpath(full_p, frontend_dir)] = f.read()

print(f"Loaded api.ts and {len(ui_files)} frontend UI files.")
