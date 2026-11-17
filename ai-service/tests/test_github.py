"""
Unit tests for EKA Secure GitHub Integration & Webhooks (Phase 3)
Tests HMAC verification, path traversal prevention, event parsing, client operations, and webhooks.
"""
import hashlib
import hmac
import json
import pytest
from fastapi import HTTPException

from eka.github import (
    GitHubClient,
    get_github_client,
    verify_github_signature,
    validate_tenant_repo_access,
    parse_webhook_event,
)
from eka.config import settings
from eka.api import process_github_webhook
from eka.db import init_db

init_db()


def _compute_sig(payload: dict, secret: str = settings.webhook_secret) -> str:
    body = json.dumps(payload).encode("utf-8")
    h = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={h}"


# ─────────────────────────────────────────────────────────────────────────────
# 1. Signature Verification Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_verify_signature_valid():
    payload = b'{"action": "completed"}'
    secret = "test-secret"
    h = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    assert verify_github_signature(payload, f"sha256={h}", secret) is True


def test_verify_signature_invalid():
    payload = b'{"action": "completed"}'
    assert verify_github_signature(payload, "sha256=invalidhash123", "test-secret") is False


def test_verify_signature_missing_header():
    assert verify_github_signature(b"data", None, "secret") is False


def test_verify_signature_malformed_header():
    assert verify_github_signature(b"data", "nothashprefix", "secret") is False


# ─────────────────────────────────────────────────────────────────────────────
# 2. Tenant Boundary Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_tenant_repo_validation_allows_tenant_owned_repo():
    assert validate_tenant_repo_access("acme", "acme/payment-service") is True
    assert validate_tenant_repo_access("acme", "mock-acme/web-app") is True
    assert validate_tenant_repo_access("globex", "globex/billing-engine") is True


def test_tenant_repo_validation_blocks_cross_tenant_access():
    assert validate_tenant_repo_access("acme", "globex/billing-engine") is False
    assert validate_tenant_repo_access("globex", "acme/payment-service") is False
    assert validate_tenant_repo_access("acme", "stranger/unknown-repo") is False


# ─────────────────────────────────────────────────────────────────────────────
# 3. Webhook Event Parsing Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_parse_workflow_run_failure():
    payload = {
        "action": "completed",
        "repository": {"full_name": "acme/web-app"},
        "workflow_run": {
            "id": 12345,
            "name": "CI / Test",
            "status": "completed",
            "conclusion": "failure",
            "head_branch": "main",
            "head_sha": "abc123456",
        },
        "log": "java.lang.OutOfMemoryError: Java heap space",
    }
    event = parse_webhook_event("workflow_run", payload)
    assert event["is_failure"] is True
    assert event["run_id"] == 12345
    assert "heap space" in event["log"]


def test_parse_push_event():
    payload = {
        "ref": "refs/heads/feature/login",
        "repository": {"full_name": "acme/web-app"},
        "pusher": {"name": "alice"},
        "commits": [{"id": "abcdef12", "message": "fix bug", "author": {"name": "Alice"}}],
    }
    event = parse_webhook_event("push", payload)
    assert event["branch"] == "feature/login"
    assert event["commit_count"] == 1
    assert event["pusher"] == "alice"


def test_parse_pull_request_event():
    payload = {
        "action": "opened",
        "repository": {"full_name": "acme/web-app"},
        "pull_request": {
            "number": 42,
            "title": "Update JVM limits",
            "state": "open",
            "merged": False,
            "user": {"login": "bob"},
        },
    }
    event = parse_webhook_event("pull_request", payload)
    assert event["number"] == 42
    assert event["action"] == "opened"
    assert event["user"] == "bob"


# ─────────────────────────────────────────────────────────────────────────────
# 4. GitHubClient Operations Tests (Synchronous)
# ─────────────────────────────────────────────────────────────────────────────

def test_github_client_repo_info():
    gh = get_github_client()
    info = gh.get_repo_info_sync("acme/payment-service")
    assert info["name"] == "payment-service"
    assert "default_branch" in info


def test_github_client_file_inspection_prevents_traversal():
    gh = get_github_client()
    with pytest.raises(ValueError) as exc:
        gh.get_file_contents_sync("acme/repo", "../../../etc/passwd", tenant="acme")
    assert "Path traversal" in str(exc.value)


def test_github_client_file_inspection_safe_read():
    gh = get_github_client()
    content = gh.get_file_contents_sync("acme/repo", "package.json", tenant="acme")
    assert "name" in content or "package" in content


def test_github_client_workflow_runs_and_logs():
    gh = get_github_client()
    runs = gh.get_workflow_runs_sync("acme/repo")
    assert len(runs) >= 1

    logs = gh.get_workflow_run_logs_sync("acme/repo", runs[0]["id"])
    assert len(logs) > 0


def test_github_client_pr_creation_and_status():
    gh = get_github_client()
    pr = gh.create_pull_request_sync(
        owner_repo="acme/web-app",
        title="[EKA Fix] Out of Memory Fix",
        body="Remediation patch",
        head="eka/fix-oom-1",
        tenant="acme",
        incident_id=99,
    )
    assert "url" in pr
    assert pr["number"] >= 40

    status = gh.get_pull_request_status_sync("acme/web-app", pr["number"])
    assert "state" in status
    assert status["mergeable"] is True


# ─────────────────────────────────────────────────────────────────────────────
# 5. Full Webhook Processing Integration Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_webhook_processing_rejects_invalid_signature():
    payload = {"repository": {"full_name": "acme/web-app"}}
    with pytest.raises(HTTPException) as exc:
        process_github_webhook(
            tenant="acme",
            event_type="workflow_run",
            payload=payload,
            signature_header="sha256=invalid",
        )
    assert exc.value.status_code == 401


def test_webhook_processing_rejects_unauthorized_cross_tenant_repo():
    payload = {"repository": {"full_name": "globex/billing-service"}}
    sig = _compute_sig(payload)
    with pytest.raises(HTTPException) as exc:
        process_github_webhook(
            tenant="acme",
            event_type="push",
            payload=payload,
            signature_header=sig,
        )
    assert exc.value.status_code == 403


def test_webhook_processing_handles_workflow_failure():
    payload = {
        "action": "completed",
        "repository": {"full_name": "acme/web-app"},
        "workflow_run": {
            "id": 8801,
            "name": "CI Build",
            "status": "completed",
            "conclusion": "failure",
            "head_branch": "main",
            "head_sha": "deadbeef123",
        },
        "log": "ERROR: java.lang.OutOfMemoryError: Java heap space",
    }
    sig = _compute_sig(payload)
    data = process_github_webhook(
        tenant="acme",
        event_type="workflow_run",
        payload=payload,
        signature_header=sig,
    )
    assert data["status"] == "processed"
    assert "incident_id" in data
    assert "decision" in data


def test_webhook_processing_handles_workflow_success():
    payload = {
        "action": "completed",
        "repository": {"full_name": "acme/web-app"},
        "workflow_run": {
            "id": 8802,
            "name": "CI Build",
            "status": "completed",
            "conclusion": "success",
        },
    }
    sig = _compute_sig(payload)
    data = process_github_webhook(
        tenant="acme",
        event_type="workflow_run",
        payload=payload,
        signature_header=sig,
    )
    assert data["status"] == "recorded"
    assert data["conclusion"] == "success"


def test_webhook_processing_handles_push_event():
    payload = {
        "ref": "refs/heads/main",
        "repository": {"full_name": "acme/web-app"},
        "pusher": {"name": "alice"},
        "commits": [{"id": "abc1", "message": "commit 1", "author": {"name": "Alice"}}],
    }
    sig = _compute_sig(payload)
    data = process_github_webhook(
        tenant="acme",
        event_type="push",
        payload=payload,
        signature_header=sig,
    )
    assert data["status"] == "recorded"
    assert data["event"] == "push"
    assert data["commits"] == 1


def test_webhook_processing_handles_pr_event():
    payload = {
        "action": "opened",
        "repository": {"full_name": "acme/web-app"},
        "pull_request": {"number": 105, "title": "New feature", "user": {"login": "charlie"}},
    }
    sig = _compute_sig(payload)
    data = process_github_webhook(
        tenant="acme",
        event_type="pull_request",
        payload=payload,
        signature_header=sig,
    )
    assert data["status"] == "recorded"
    assert data["event"] == "pull_request"
    assert data["action"] == "opened"


# ─────────────────────────────────────────────────────────────────────────────
# 6. Real GitHub Operations Tests (Phase 6 Automated Suite with Mocked API)
# ─────────────────────────────────────────────────────────────────────────────

from unittest.mock import MagicMock, patch
import httpx


def test_successful_branch_creation():
    client = GitHubClient(token="mock-pat-token")
    with patch("httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.post.return_value = httpx.Response(
            201,
            json={"ref": "refs/heads/eka/incident-99", "object": {"sha": "sha9999"}},
        )
        res = client.create_branch_sync("Gowthamone7/EKA-DevGuard", "eka/incident-99", "base123")
        assert res["created"] is True
        assert res["sha"] == "sha9999"


def test_successful_commit_creation():
    client = GitHubClient(token="mock-pat-token")
    with patch("httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.get.return_value = httpx.Response(404)  # file doesn't exist yet
        mock_instance.put.return_value = httpx.Response(
            201,
            json={"content": {"name": "patch.diff", "sha": "blob123"}, "commit": {"sha": "commit123"}},
        )
        res = client.commit_file_sync(
            "Gowthamone7/EKA-DevGuard",
            "eka/incident-99",
            "remediations/patch.diff",
            "diff --git a/b b/b",
            "fix: automated patch",
        )
        assert res["commit"]["sha"] == "commit123"


def test_successful_pr_creation():
    client = GitHubClient(token="mock-pat-token")
    with patch("httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.post.return_value = httpx.Response(
            201,
            json={
                "number": 105,
                "title": "[EKA Fix] Out of Memory",
                "html_url": "https://github.com/Gowthamone7/EKA-DevGuard/pull/105",
                "state": "open",
            },
        )
        res = client.create_pull_request_sync(
            "Gowthamone7/EKA-DevGuard",
            "[EKA Fix] Out of Memory",
            "Body text",
            "eka/incident-99",
            "main",
            "acme",
            99,
        )
        assert res["number"] == 105
        assert res["html_url"] == "https://github.com/Gowthamone7/EKA-DevGuard/pull/105"
        assert res["mock"] is False


def test_github_auth_failure_401():
    client = GitHubClient(token="invalid-pat-token")
    with patch("httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        # 401 Bad credentials on base branch inspection
        mock_instance.get.return_value = httpx.Response(401, text='{"message": "Bad credentials"}')
        res = client.create_remediation_pr_flow_sync(
            "Gowthamone7/EKA-DevGuard",
            "acme",
            99,
            "OOM error",
            "Diagnosis",
            "Patch fix",
            ["citation-1"],
        )
        assert res["success"] is False
        assert "401" in res["error"]
        assert res["number"] is None


def test_insufficient_permissions_403():
    client = GitHubClient(token="read-only-token")
    with patch("httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        # Existing PR check returns empty, base branch ref, branch existence check returns 404
        mock_instance.get.side_effect = [
            httpx.Response(200, json=[]),  # list PRs
            httpx.Response(200, json={"object": {"sha": "basesha123"}}),  # base branch ref
            httpx.Response(404),  # branch existence check (branch does not exist yet)
        ]
        # Branch creation returns 403 Forbidden
        mock_instance.post.return_value = httpx.Response(
            403,
            text='{"message": "Resource not accessible by personal access token"}',
        )
        res = client.create_remediation_pr_flow_sync(
            "Gowthamone7/EKA-DevGuard",
            "acme",
            99,
            "OOM error",
            "Diagnosis",
            "Patch fix",
            ["citation-1"],
        )
        assert res["success"] is False
        assert "403" in res["error"]
        assert res["number"] is None


def test_repository_not_found_404():
    client = GitHubClient(token="mock-pat-token")
    with patch("httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.get.return_value = httpx.Response(404, text='{"message": "Not Found"}')
        res = client.create_remediation_pr_flow_sync(
            "nonexistent/repo",
            "acme",
            99,
            "OOM error",
            "Diagnosis",
            "Patch fix",
            ["citation-1"],
        )
        assert res["success"] is False
        assert "404" in res["error"]


def test_branch_creation_failure_422():
    client = GitHubClient(token="mock-pat-token")
    with patch("httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.get.side_effect = [
            httpx.Response(200, json=[]),  # list PRs
            httpx.Response(200, json={"object": {"sha": "basesha123"}}),  # base sha
            httpx.Response(404),  # branch existence check (branch does not exist yet)
        ]
        mock_instance.post.return_value = httpx.Response(
            422,
            text='{"message": "Validation Failed: branch name invalid"}',
        )
        res = client.create_remediation_pr_flow_sync(
            "Gowthamone7/EKA-DevGuard",
            "acme",
            99,
            "Title",
            "Diagnosis",
            "Fix",
            ["cit"],
        )
        assert res["success"] is False
        assert "422" in res["error"]


def test_pull_request_creation_failure():
    client = GitHubClient(token="mock-pat-token")
    with patch("httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.get.side_effect = [
            httpx.Response(200, json=[]),  # list PRs
            httpx.Response(200, json={"object": {"sha": "basesha123"}}),  # base sha
            httpx.Response(404),  # branch existence check (branch does not exist yet)
            httpx.Response(404),  # commit file check
        ]
        # Branch create success, commit success, but PR create fails 422
        mock_instance.post.side_effect = [
            httpx.Response(201, json={"ref": "refs/heads/eka/incident-99", "object": {"sha": "bsha"}}),  # branch
            httpx.Response(422, text='{"message": "No commits between main and eka/incident-99"}'),  # PR
        ]
        mock_instance.put.return_value = httpx.Response(201, json={"commit": {"sha": "c1"}})  # file commit

        res = client.create_remediation_pr_flow_sync(
            "Gowthamone7/EKA-DevGuard",
            "acme",
            99,
            "Title",
            "Diagnosis",
            "Fix",
            ["cit"],
        )
        assert res["success"] is False
        assert "422" in res["error"]


def test_merge_failure_guardrail():
    client = GitHubClient(token="mock-pat-token")
    with patch("httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.put.return_value = httpx.Response(
            405,
            text='{"message": "Pull Request is not mergeable"}',
        )
        res = client.merge_pull_request_sync("Gowthamone7/EKA-DevGuard", 105)
        assert res["merged"] is False
        assert "405" in res["error"]


def test_duplicate_pr_prevention():
    client = GitHubClient(token="mock-pat-token")
    with patch("httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        # List open PRs returns existing PR for eka/incident-99
        mock_instance.get.return_value = httpx.Response(
            200,
            json=[
                {
                    "number": 88,
                    "title": "[EKA Fix] Out of Memory",
                    "html_url": "https://github.com/Gowthamone7/EKA-DevGuard/pull/88",
                    "state": "open",
                    "head": {"ref": "eka/incident-99"},
                }
            ],
        )
        res = client.create_remediation_pr_flow_sync(
            "Gowthamone7/EKA-DevGuard",
            "acme",
            99,
            "Title",
            "Diagnosis",
            "Fix",
            ["cit"],
        )
        assert res["success"] is True
        assert res["number"] == 88
        assert res["duplicate"] is True
        # Verify no duplicate POST was sent
        mock_instance.post.assert_not_called()
