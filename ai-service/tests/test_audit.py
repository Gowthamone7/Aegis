"""
Unit tests for Hash-Chained Audit Trail Integrity
"""
from eka.db import SessionLocal, append_audit, verify_audit_chain, init_db, AuditLog


def test_audit_hash_chain_append_and_verify():
    init_db()
    with SessionLocal() as db:
        db.query(AuditLog).delete()
        db.commit()
        # Append 3 audit events
        append_audit(db, "acme", "dev@acme", "TEST_ACTION_1", "Detail 1")
        append_audit(db, "acme", "dev@acme", "TEST_ACTION_2", "Detail 2")
        append_audit(db, "globex", "mgr@globex", "TEST_ACTION_3", "Detail 3")

        valid, broken = verify_audit_chain(db)
        assert valid is True
        assert len(broken) == 0


def test_audit_hash_chain_detects_tampering():
    init_db()
    with SessionLocal() as db:
        append_audit(db, "acme", "actor", "ACTION_A", "Authentic")
        append_audit(db, "acme", "actor", "ACTION_B", "Authentic")

        # Tamper with an existing record
        entry = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        entry.detail = "TAMPERED_BY_ATTACKER"
        db.commit()

        valid, broken = verify_audit_chain(db)
        assert valid is False
        assert len(broken) > 0
        # Clean up tampered rows so subsequent tests start fresh
        db.query(AuditLog).delete()
        db.commit()
