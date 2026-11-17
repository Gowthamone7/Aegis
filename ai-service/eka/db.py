"""
EKA Database Models — SQLAlchemy 2.x + hash-chained audit log.

Models
------
User         — authentication & tenant membership
Incident     — a resolved (or in-progress) log incident
Approval     — pending human-approval records
AuditLog     — append-only, SHA-256 hash-chained audit trail

Functions
---------
init_db(engine)                   — create all tables
seed_demo_users(session)          — insert demo users if absent
append_audit(...)                 — append a new AuditLog entry
verify_audit_chain(session)       — check chain integrity
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Tuple

from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, String, Text, create_engine, event,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from .config import settings

log = logging.getLogger(__name__)


# ─────────────────────────── base ─────────────────────────────────────────────

class Base(DeclarativeBase):
    __allow_unmapped__ = True


# ─────────────────────────── models ───────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(120), unique=True, nullable=False, index=True)
    pw_hash = Column(String(256), nullable=False)
    tenant = Column(String(80), nullable=False, index=True)
    role = Column(String(32), nullable=False, default="developer")

    def __repr__(self) -> str:
        return f"<User {self.username!r} tenant={self.tenant!r} role={self.role!r}>"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant = Column(String(80), nullable=False, index=True)
    source = Column(String(80), nullable=False, default="api")
    title = Column(String(256), nullable=False)
    status = Column(String(32), nullable=False, default="open")
    result_json = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<Incident id={self.id} tenant={self.tenant!r} status={self.status!r}>"
        )


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant = Column(String(80), nullable=False, index=True)
    incident_id = Column(Integer, nullable=False, index=True)
    tool = Column(String(80), nullable=False)
    payload_json = Column(Text, nullable=True)
    # pending / approved / rejected
    status = Column(String(32), nullable=False, default="pending")
    decided_by = Column(String(120), nullable=True)

    # Repository & Execution associations (Phase 3 & Phase 5)
    repo = Column(String(160), nullable=True)
    source_branch = Column(String(120), nullable=True)
    target_branch = Column(String(120), nullable=True, default="main")
    pr_number = Column(Integer, nullable=True)
    pr_url = Column(String(255), nullable=True)
    execution_status = Column(String(64), nullable=True, default="Awaiting Approval")

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<Approval id={self.id} incident_id={self.incident_id} "
            f"status={self.status!r} execution_status={self.execution_status!r} pr_number={self.pr_number}>"
        )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    tenant = Column(String(80), nullable=False, index=True)
    actor = Column(String(120), nullable=False)
    action = Column(String(120), nullable=False)
    detail = Column(Text, nullable=True)
    prev_hash = Column(String(64), nullable=False, default="0" * 64)
    hash = Column(String(64), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} tenant={self.tenant!r} "
            f"action={self.action!r} actor={self.actor!r}>"
        )


# ─────────────────────────── engine / session factory ─────────────────────────

def build_engine(database_url: str | None = None):
    url = database_url or settings.database_url
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
        echo=(settings.env == "dev"),
    )
    # Enable WAL mode for SQLite
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _set_wal(dbapi_conn, _record):
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
            dbapi_conn.execute("PRAGMA foreign_keys=ON")
    return engine


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = build_engine()
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(), autocommit=False, autoflush=False
        )
    return _SessionLocal


class _SessionLocalProxy:
    """Callable proxy so SessionLocal() invokes get_session_factory()()"""
    def __call__(self, *args, **kwargs):
        factory = get_session_factory()
        return factory(*args, **kwargs)

SessionLocal = _SessionLocalProxy()


def get_db():
    """FastAPI dependency — yields a DB session."""
    factory = get_session_factory()
    db: Session = factory()
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────── init / seed ──────────────────────────────────────

def _migrate_approvals_schema(eng) -> None:
    """Ensure newly added columns exist in approvals table for existing sqlite db."""
    try:
        from sqlalchemy import text
        with eng.connect() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(approvals)")).fetchall()]
            new_cols = {
                "repo": "VARCHAR(160)",
                "source_branch": "VARCHAR(120)",
                "target_branch": "VARCHAR(120)",
                "pr_number": "INTEGER",
                "pr_url": "VARCHAR(255)",
                "execution_status": "VARCHAR(64)",
            }
            for col_name, col_type in new_cols.items():
                if col_name not in cols:
                    conn.execute(text(f"ALTER TABLE approvals ADD COLUMN {col_name} {col_type}"))
            conn.commit()
    except Exception as e:
        log.warning("Approvals table migration check notice: %s", e)


def init_db(engine=None) -> None:
    """Create all tables and seed demo users."""
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)
    _migrate_approvals_schema(eng)
    log.info("Database tables created/verified.")
    with SessionLocal() as db:
        seed_demo_users(db)


def seed_demo_users(session: Session) -> None:
    """Insert demo users if they don't already exist."""
    from .auth import hash_password  # local import to avoid circular

    demo_users = [
        ("dev@acme", "acme", "developer"),
        ("mgr@acme", "acme", "manager"),
        ("viewer@acme", "acme", "viewer"),
        ("dev@globex", "globex", "developer"),
        ("mgr@globex", "globex", "manager"),
    ]
    for username, tenant, role in demo_users:
        exists = session.query(User).filter_by(username=username).first()
        if not exists:
            user = User(
                username=username,
                pw_hash=hash_password("demo123"),
                tenant=tenant,
                role=role,
            )
            session.add(user)
    session.commit()
    log.info("Demo users seeded.")


# ─────────────────────────── audit helpers ────────────────────────────────────

def _compute_hash(
    prev_hash: str,
    ts: str,
    tenant: str,
    actor: str,
    action: str,
    detail: str,
) -> str:
    payload = f"{prev_hash}|{ts}|{tenant}|{actor}|{action}|{detail}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _format_ts(dt: Any) -> str:
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    return str(dt)


def append_audit(
    session: Session,
    tenant: str,
    actor: str,
    action: str,
    detail: str,
) -> AuditLog:
    """
    Append a new audit entry and chain it to the last one.
    Returns the created AuditLog row (not yet committed — caller commits).
    """
    # Get the previous entry for this tenant (or global chain)
    last = (
        session.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .first()
    )
    prev_hash = last.hash if last else "0" * 64
    now = datetime.now(timezone.utc)
    ts_str = _format_ts(now)

    new_hash = _compute_hash(prev_hash, ts_str, tenant, actor, action, detail or "")
    entry = AuditLog(
        ts=now,
        tenant=tenant,
        actor=actor,
        action=action,
        detail=detail,
        prev_hash=prev_hash,
        hash=new_hash,
    )
    session.add(entry)
    session.commit()
    return entry


def verify_audit_chain(session: Session) -> Tuple[bool, List[int]]:
    """
    Verify the hash chain across all audit log entries ordered by id.
    Returns (is_valid, list_of_broken_entry_ids).
    """
    entries: List[AuditLog] = (
        session.query(AuditLog).order_by(AuditLog.id.asc()).all()
    )
    broken: list[int] = []
    expected_prev = "0" * 64

    for entry in entries:
        # Check prev_hash linkage
        if entry.prev_hash != expected_prev:
            broken.append(entry.id)

        # Recompute hash
        ts_str = _format_ts(entry.ts) if entry.ts else ""
        expected_hash = _compute_hash(
            entry.prev_hash,
            ts_str,
            entry.tenant,
            entry.actor,
            entry.action,
            entry.detail or "",
        )
        if entry.hash != expected_hash:
            if entry.id not in broken:
                broken.append(entry.id)

        expected_prev = entry.hash

    return (len(broken) == 0, broken)
