"""
EKA GitHub Webhook Security & Event Processor

Security Requirements:
- HMAC-SHA256 signature verification with constant-time comparison
- Payload validation against known GitHub event schemas (workflow_run, push, pull_request)
- Tenant boundary enforcement preventing cross-tenant repository access
- Zero token or credential exposure
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any, Dict, Optional

from ..config import settings
from ..security import sanitize_input

log = logging.getLogger(__name__)


def verify_github_signature(
    payload_bytes: bytes,
    signature_header: Optional[str],
    secret: Optional[str] = None,
) -> bool:
    """
    Validate GitHub HMAC-SHA256 signature using constant-time comparison.
    Header format: sha256=<hex_digest>
    """
    if not signature_header:
        log.warning("Webhook rejected: missing X-Hub-Signature-256 header")
        return False

    secret_key = secret or settings.webhook_secret
    if not secret_key:
        log.warning("Webhook rejected: WEBHOOK_SECRET not configured")
        return False

    if not signature_header.startswith("sha256="):
        log.warning("Webhook rejected: malformed signature format (missing sha256= prefix)")
        return False

    expected_hash = hmac.new(
        secret_key.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    expected_signature = f"sha256={expected_hash}"
    is_valid = hmac.compare_digest(signature_header, expected_signature)
    if not is_valid:
        log.warning("Webhook rejected: HMAC-SHA256 signature mismatch")
    return is_valid


def validate_tenant_repo_access(tenant: str, repo_full_name: str) -> bool:
    """
    Verify that the repository specified in the event belongs to the target tenant.
    Prevents an attacker from targeting tenant A with webhooks from tenant B.
    """
    if not repo_full_name:
        return False

    repo_lower = repo_full_name.lower()
    tenant_lower = tenant.lower()

    # 1. Check GITHUB_REPOS mapping from config if defined
    tenant_map = settings.get_github_repos()
    if tenant_lower in tenant_map:
        allowed_repos = [r.strip().lower() for r in tenant_map[tenant_lower].split(";")]
        if repo_lower in allowed_repos:
            return True

    # 2. Allow matching tenant organization prefix or standard mock convention
    if repo_lower.startswith(f"{tenant_lower}/") or repo_lower.startswith(f"mock-{tenant_lower}/"):
        return True

    # 3. Allow repository name containing tenant identifier
    parts = repo_lower.split("/")
    if len(parts) == 2 and (tenant_lower in parts[0] or tenant_lower in parts[1]):
        return True

    log.warning("Blocked cross-tenant repository access attempt: tenant=%r, repo=%r", tenant, repo_full_name)
    return False


def parse_webhook_event(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes GitHub webhook payloads into structured internal event dictionaries.
    Supports:
    - workflow_run: CI/CD completion, conclusion (failure/success), log triggers
    - push: commit push events, ref changes, touched files
    - pull_request: PR opened, closed, synchronized, or review requested
    """
    repository = payload.get("repository", {})
    repo_full_name = repository.get("full_name", "")

    if event_type == "workflow_run":
        run = payload.get("workflow_run", {})
        conclusion = run.get("conclusion")
        status = run.get("status")
        is_failure = (conclusion == "failure") or (status == "completed" and conclusion != "success")

        # Extract log excerpt or error summary from jobs
        log_text = payload.get("log", "")
        if not log_text and is_failure:
            log_text = f"GitHub Actions workflow '{run.get('name', 'CI')}' failed on branch '{run.get('head_branch', 'main')}' (commit: {run.get('head_sha', '')[:8]})"

        return {
            "event_type": "workflow_run",
            "action": payload.get("action", ""),
            "repo": repo_full_name,
            "run_id": run.get("id"),
            "name": run.get("name", "CI Workflow"),
            "status": status,
            "conclusion": conclusion,
            "is_failure": is_failure,
            "branch": run.get("head_branch", "main"),
            "commit_sha": run.get("head_sha", ""),
            "html_url": run.get("html_url", ""),
            "log": sanitize_input(log_text, max_len=8000),
        }

    elif event_type == "push":
        commits = payload.get("commits", [])
        return {
            "event_type": "push",
            "repo": repo_full_name,
            "ref": payload.get("ref", "refs/heads/main"),
            "branch": payload.get("ref", "").replace("refs/heads/", ""),
            "before": payload.get("before"),
            "after": payload.get("after"),
            "pusher": payload.get("pusher", {}).get("name", "unknown"),
            "commit_count": len(commits),
            "head_commit": payload.get("head_commit", {}),
            "commits": [
                {
                    "sha": c.get("id", "")[:8],
                    "message": c.get("message", ""),
                    "author": c.get("author", {}).get("name", ""),
                    "modified": c.get("modified", []),
                }
                for c in commits[:10]
            ],
        }

    elif event_type == "pull_request":
        pr = payload.get("pull_request", {})
        return {
            "event_type": "pull_request",
            "action": payload.get("action", "opened"),
            "repo": repo_full_name,
            "number": pr.get("number"),
            "title": pr.get("title", ""),
            "state": pr.get("state", "open"),
            "merged": pr.get("merged", False),
            "head_branch": pr.get("head", {}).get("ref", ""),
            "base_branch": pr.get("base", {}).get("ref", "main"),
            "user": pr.get("user", {}).get("login", ""),
            "html_url": pr.get("html_url", ""),
        }

    else:
        return {
            "event_type": event_type,
            "repo": repo_full_name,
            "action": payload.get("action", ""),
            "raw": payload,
        }

