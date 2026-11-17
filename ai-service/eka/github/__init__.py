"""
EKA GitHub Package

Exports:
- GitHubClient: API client for repo inspection, workflows, logs, and PRs
- get_github_client: Factory helper
- verify_github_signature: HMAC-SHA256 signature verification
- validate_tenant_repo_access: Multi-tenant repo access validation
- parse_webhook_event: Normalized event parsing
- generate_unified_diff: Standard unified Git diff generator
- validate_unified_diff: Diff syntax and security validator
- DiffValidationResult: Diff validation result dataclass
"""
from __future__ import annotations

from .client import GitHubClient
from .webhook import (
    verify_github_signature,
    validate_tenant_repo_access,
    parse_webhook_event,
)
from .diff import (
    generate_unified_diff,
    validate_unified_diff,
    DiffValidationResult,
)

_client_instance: GitHubClient | None = None


def get_github_client() -> GitHubClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = GitHubClient()
    return _client_instance


__all__ = [
    "GitHubClient",
    "get_github_client",
    "verify_github_signature",
    "validate_tenant_repo_access",
    "parse_webhook_event",
    "generate_unified_diff",
    "validate_unified_diff",
    "DiffValidationResult",
]
