"""Guards for the Supabase provisioning script and the reviewable PostgreSQL DDL. Offline only."""

import subprocess
import sys
from pathlib import Path

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.db.base import Base

ROOT = Path(__file__).parents[2]
NEW = ["training_questions", "training_profiles", "training_attempts", "training_attempt_items"]


def test_provisioning_script_registers_all_103_tables_without_importing_the_app():
    # Fresh interpreter: the script must register the training models by itself (it never imports app.main).
    code = (
        "import importlib.util, sys;"
        "spec = importlib.util.spec_from_file_location('prov', 'scripts/create_supabase_schema.py');"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
        "from app.db.base import Base;"
        "assert 'app.main' not in sys.modules;"
        "t = set(Base.metadata.tables);"
        f"assert {NEW!r} and all(x in t for x in {NEW!r}), 'training tables missing';"
        "print(len(t))"
    )
    out = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, '.'); " + code],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
        env={**__import__("os").environ, "DATABASE_URL": "sqlite+aiosqlite://"},
    )
    assert out.returncode == 0, out.stderr[-800:]
    assert out.stdout.strip().splitlines()[-1] == "103"


def test_provisioning_script_is_non_destructive():
    src = (ROOT / "scripts" / "create_supabase_schema.py").read_text(encoding="utf-8").lower()
    for word in ("drop_all", "drop table", "truncate", "alter table", "delete from"):
        assert word not in src, word
    assert "create_all" in src


def test_deployment_sql_matches_the_current_models_exactly():
    d = postgresql.dialect()
    blocks = []
    for n in NEW:
        t = Base.metadata.tables[n]
        blocks.append(str(CreateTable(t).compile(dialect=d)).strip() + ";")
        blocks += [str(CreateIndex(i).compile(dialect=d)).strip() + ";" for i in sorted(t.indexes, key=lambda i: i.name)]
    body = (ROOT / "deployment" / "training_tables.postgres.sql").read_text(encoding="utf-8").split("\n\n", 1)[1].strip()
    assert body == "\n\n".join(blocks), "deployment/training_tables.postgres.sql is out of date; regenerate it from the models"
