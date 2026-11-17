"""
demo_reset.py — Reset the demo state to a clean starting point.

Actions:
  1. Deletes eka.db (SQLite database)
  2. Re-creates the DB with demo users (dev/mgr/viewer for acme, dev/mgr for globex)
  3. Clears the mock_github folder (removes all mock PR files)

Usage:
    python -m scripts.demo_reset
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from eka.config import get_settings


def main() -> None:
    settings = get_settings()

    repo_root = Path(__file__).resolve().parent.parent.parent
    ai_service_root = Path(__file__).resolve().parent.parent

    # ── 1. Delete eka.db ────────────────────────────────────────────────────
    db_path = ai_service_root / "eka.db"
    if db_path.exists():
        db_path.unlink()
        print(f"[RESET] ✓ Deleted {db_path}")
    else:
        print(f"[RESET]   No DB file found at {db_path} (already clean)")

    # ── 2. Re-create DB with demo users ─────────────────────────────────────
    try:
        from sqlalchemy import create_engine
        from eka.db import init_db, seed_demo_users
        from sqlalchemy.orm import Session

        engine = create_engine(settings.DATABASE_URL, echo=False)
        init_db(engine)
        with Session(engine) as session:
            seed_demo_users(session)
            session.commit()
        print(f"[RESET] ✓ Re-created DB at {db_path} with demo users:")
        print(f"           dev@acme / demo123     (role: DEVELOPER)")
        print(f"           mgr@acme / demo123     (role: MANAGER)")
        print(f"           viewer@acme / demo123  (role: VIEWER)")
        print(f"           dev@globex / demo123   (role: DEVELOPER)")
        print(f"           mgr@globex / demo123   (role: MANAGER)")
    except Exception as exc:
        print(f"[RESET] ✗ Failed to re-create DB: {exc}")
        sys.exit(1)

    # ── 3. Clear mock_github folder ──────────────────────────────────────────
    mock_github_dir = repo_root / "data" / "mock_github"
    if not mock_github_dir.exists():
        mock_github_dir.mkdir(parents=True, exist_ok=True)
        print(f"[RESET] ✓ Created empty mock_github dir: {mock_github_dir}")
    else:
        # Remove all files inside but keep the directory
        removed = 0
        for item in mock_github_dir.iterdir():
            if item.is_file():
                item.unlink()
                removed += 1
            elif item.is_dir():
                shutil.rmtree(item)
                removed += 1
        print(f"[RESET] ✓ Cleared mock_github dir ({removed} item(s) removed): {mock_github_dir}")

    print()
    print("[RESET] ✓ Demo state reset complete. Ready for demo.")
    print("         Start services:  docker-compose up -d")
    print("         Start AI service: uvicorn eka.main:app --reload --port 8000")
    print("         Start gateway:   cd gateway && mvn spring-boot:run")


if __name__ == "__main__":
    main()
