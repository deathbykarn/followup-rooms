"""
Apply Supabase migrations in order.

Reads .sql files from ../supabase/migrations/ sorted by filename, executes
them against SUPABASE_DB_URL, and records each applied filename in a
public._migrations tracking table so re-runs skip already-applied files.

For destructive changes, document rollback in the migration file's
'-- Rollback:' comment header.
"""
import sys
from pathlib import Path

import psycopg

# Ensure parent (backend/) is on sys.path so `app.core.config` imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings  # noqa: E402

TRACKING_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS public._migrations (
    filename TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


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

    print(f"Connecting to {settings.supabase_url}")

    with psycopg.connect(settings.supabase_db_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            # Ensure tracking table exists
            cur.execute(TRACKING_TABLE_DDL)

            # Fetch already-applied migrations
            cur.execute("SELECT filename FROM public._migrations")
            applied = {row[0] for row in cur.fetchall()}

            to_apply = [f for f in files if f.name not in applied]
            if not to_apply:
                print(f"All {len(files)} migrations already applied. Nothing to do.")
                return 0

            print(f"Applying {len(to_apply)} new migration(s) (of {len(files)} total):")
            for f in to_apply:
                print(f"  → {f.name}")
                sql = f.read_text()
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO public._migrations (filename) VALUES (%s)",
                    (f.name,),
                )

    print("Migrations applied successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
