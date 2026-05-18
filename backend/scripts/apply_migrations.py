"""
Apply Supabase migrations in order.

Reads .sql files from ../supabase/migrations/ sorted by filename,
executes them against SUPABASE_DB_URL.

Idempotency: relies on `IF NOT EXISTS` / `CREATE OR REPLACE` in migrations.
For destructive changes, document rollback in the migration file's
'-- Rollback:' comment header.
"""
import sys
from pathlib import Path

import psycopg

# Ensure parent (backend/) is on sys.path so `app.core.config` imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings  # noqa: E402


def main() -> int:
    settings = get_settings()
    migrations_dir = Path(__file__).parent.parent.parent / "supabase" / "migrations"

    if not migrations_dir.exists():
        print(f"Migrations directory not found: {migrations_dir}")
        return 1

    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        print("No migration files found.")
        return 0

    print(f"Applying {len(files)} migrations to {settings.supabase_url}")

    with psycopg.connect(settings.supabase_db_url) as conn:
        with conn.cursor() as cur:
            for f in files:
                print(f"  → {f.name}")
                sql = f.read_text()
                cur.execute(sql)
        conn.commit()

    print("Migrations applied successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
