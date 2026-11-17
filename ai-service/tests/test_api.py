"""
Direct unit tests for EKA FastAPI endpoint handlers
"""
from unittest.mock import patch
import pytest
from fastapi import HTTPException
from eka.api import (
    health,
    login,
    list_scenarios,
    simulate_incident,
    list_incidents,
    verify_audit,
    get_metrics,
    LoginRequest,
    SimulateRequest,
)
from eka.auth import UserContext, DEVELOPER, MANAGER, VIEWER
from eka.db import init_db

init_db()


def test_health_endpoint():
    res = health()
    assert res["status"] == "healthy"
    assert "version" in res
    assert "total_users" in res


def test_login_success():
    req = LoginRequest(username="dev@acme", password="demo123")
    res = login(req)
    assert "access_token" in res
    assert res["role"] == "developer"
    assert res["tenant"] == "acme"


def test_login_invalid_credentials():
    req = LoginRequest(username="dev@acme", password="wrongpassword")
    with pytest.raises(HTTPException) as exc:
        login(req)
    assert exc.value.status_code == 401


def test_scenarios_listing():
    user = UserContext(username="dev@acme", tenant="acme", role=DEVELOPER)
    scenarios = list_scenarios(current_user=user)
    assert len(scenarios) >= 5


def test_simulate_as_developer():
    user = UserContext(username="dev@acme", tenant="acme", role=DEVELOPER)
    req = SimulateRequest(scenario_id="oom", tenant="acme")
    res = simulate_incident(req, current_user=user)
    assert "incident_id" in res
    assert "events" in res
    assert res["status"] in ("AWAITING_APPROVAL", "PR_OPENED")


def test_simulate_as_viewer_is_forbidden():
    user = UserContext(username="viewer@acme", tenant="acme", role=VIEWER)
    req = SimulateRequest(scenario_id="oom", tenant="acme")
    with pytest.raises(HTTPException) as exc:
        simulate_incident(req, current_user=user)
    assert exc.value.status_code == 403


def test_incidents_listing():
    user = UserContext(username="dev@acme", tenant="acme", role=DEVELOPER)
    incidents = list_incidents(current_user=user)
    assert isinstance(incidents, list)


def test_audit_verify_endpoint():
    user = UserContext(username="dev@acme", tenant="acme", role=DEVELOPER)
    res = verify_audit(current_user=user)
    assert "valid" in res
    assert res["valid"] is True


def test_metrics_endpoint():
    user = UserContext(username="dev@acme", tenant="acme", role=DEVELOPER)
    res = get_metrics(current_user=user)
    assert "total_incidents" in res
    assert "pr_opened" in res
    assert "success_rate_percent" in res


def test_dashboard_static_serving():
    from eka.api import serve_dashboard
    resp = serve_dashboard("")
    assert hasattr(resp, "path")
    assert str(resp.path).endswith("index.html")


def test_developer_cannot_approve_action():
    from eka.api import approve_action
    dev_user = UserContext(username="dev@acme", tenant="acme", role=DEVELOPER)
    with pytest.raises(HTTPException) as exc:
        approve_action(approval_id=1, current_user=dev_user)
    assert exc.value.status_code == 403


def test_manager_approve_action_flow():
    from eka.api import approve_action
    from eka.db import SessionLocal, Incident, Approval
    mgr_user = UserContext(username="mgr@acme", tenant="acme", role=MANAGER)
    
    with SessionLocal() as db:
        inc = Incident(
            tenant="acme",
            source="github_actions",
            title="CI Failure Heap Space",
            status="AWAITING_APPROVAL",
            result_json='{"events": []}',
        )
        db.add(inc)
        db.commit()
        db.refresh(inc)

        appr = Approval(
            tenant="acme",
            incident_id=inc.id,
            tool="create_github_pr",
            payload_json="diff --git a/src b/src",
            status="pending",
        )
        db.add(appr)
        db.commit()
        db.refresh(appr)
        appr_id = appr.id

    with patch("eka.github.client.GitHubClient.create_remediation_pr_flow_sync") as mock_flow:
        mock_flow.return_value = {
            "success": True,
            "number": 110,
            "url": "https://github.com/Gowthamone7/EKA-DevGuard/pull/110",
            "branch": "eka/incident-1",
            "is_mock": False,
        }
        res = approve_action(approval_id=appr_id, current_user=mgr_user)
        assert res["status"] == "approved"
        assert res["github_success"] is True
        assert res["pr_number"] == 110
        assert "110" in res["pr_url"]


