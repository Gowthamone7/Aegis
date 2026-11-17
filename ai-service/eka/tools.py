"""
EKA Tools Registry & Implementations

Tools:
- GitHubTool: create_pr (real or mock to data/mock_github/)
- SlackTool: send_alert (real or mock to data/mock_slack.log)
- RepoReader: fetch_files safely (path traversal prevented)
- Destructive tools: restart_service, delete_branch, merge_pr (always blocked)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from .config import settings

log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
MOCK_GITHUB_DIR = DATA_DIR / "mock_github"
MOCK_SLACK_LOG = DATA_DIR / "mock_slack.log"
REPOS_DIR = DATA_DIR / "repos"

# Ensure mock directories exist
MOCK_GITHUB_DIR.mkdir(parents=True, exist_ok=True)
REPOS_DIR.mkdir(parents=True, exist_ok=True)


class PRResult:
    def __init__(
        self,
        url: Optional[str],
        number: Optional[int],
        branch: str,
        mock: bool = True,
        success: bool = True,
        error: Optional[str] = None,
        duplicate: bool = False,
    ):
        self.url = url or ""
        self.number = number
        self.branch = branch
        self.mock = mock
        self.success = success
        self.error = error
        self.duplicate = duplicate

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "number": self.number,
            "branch": self.branch,
            "mock": self.mock,
            "success": self.success,
            "error": self.error,
            "duplicate": self.duplicate,
        }


class GitHubTool:
    """GitHub integration for opening cited Pull Requests with real branch/commit orchestration."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.github_token
        self.is_mock = not bool(self.token)

    def create_pr_sync(
        self,
        tenant: str,
        incident_id: int | str,
        title: str,
        diagnosis: str,
        fix: str,
        citations: List[str],
        repo: Optional[str] = None,
    ) -> PRResult:
        from .github.client import GitHubClient

        target_repo = repo or settings.get_github_repos().get(tenant)
        if not target_repo:
            target_repo = f"{tenant}/incident-repo"

        client = GitHubClient(token=self.token)
        res = client.create_remediation_pr_flow_sync(
            owner_repo=target_repo,
            tenant=tenant,
            incident_id=incident_id,
            title=title,
            diagnosis=diagnosis,
            fix=fix,
            citations=citations,
        )
        return PRResult(
            url=res.get("url"),
            number=res.get("number") if not res.get("is_mock") else res.get("mock_number"),
            branch=res.get("branch", f"eka/incident-{incident_id}"),
            mock=res.get("is_mock", True),
            success=res.get("success", False),
            error=res.get("error"),
            duplicate=res.get("duplicate", False),
        )

    async def create_pr(
        self,
        tenant: str,
        incident_id: int | str,
        title: str,
        diagnosis: str,
        fix: str,
        citations: List[str],
        repo: Optional[str] = None,
    ) -> PRResult:
        from .github.client import GitHubClient

        target_repo = repo or settings.get_github_repos().get(tenant)
        if not target_repo:
            target_repo = f"{tenant}/incident-repo"

        client = GitHubClient(token=self.token)
        res = await client.create_remediation_pr_flow(
            owner_repo=target_repo,
            tenant=tenant,
            incident_id=incident_id,
            title=title,
            diagnosis=diagnosis,
            fix=fix,
            citations=citations,
        )
        return PRResult(
            url=res.get("url"),
            number=res.get("number") if not res.get("is_mock") else res.get("mock_number"),
            branch=res.get("branch", f"eka/incident-{incident_id}"),
            mock=res.get("is_mock", True),
            success=res.get("success", False),
            error=res.get("error"),
            duplicate=res.get("duplicate", False),
        )


class SlackTool:
    """Slack integration for alerting engineering teams."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.slack_webhook_url
        self.is_mock = not bool(self.webhook_url)

    async def send_alert(
        self,
        tenant: str,
        incident_id: int | str,
        title: str,
        diagnosis: str,
        pr_url: str,
        citations: Optional[List[str]] = None,
    ) -> bool:
        citations = citations or []
        msg = {
            "text": f"🚨 *[EKA Incident Alert]* Incident #{incident_id} ({tenant})",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🚨 *[EKA Alert]* Build Failure Detected for *{tenant}*\n*Issue*: {title}\n*Diagnosis*: {diagnosis[:300]}...",
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Pull Request"},
                            "url": pr_url,
                            "style": "primary",
                        }
                    ],
                },
            ],
        }

        if self.is_mock:
            with open(MOCK_SLACK_LOG, "a", encoding="utf-8") as f:
                f.write(f"[{tenant}] Incident #{incident_id}: {title} | PR: {pr_url}\n")
            log.info("Mock Slack alert appended to %s", MOCK_SLACK_LOG)
            return True

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(self.webhook_url, json=msg)
            return resp.status_code == 200


class RepoReader:
    """Reads repository files safely with path traversal protection."""

    @staticmethod
    def fetch_files(tenant: str, file_paths: List[str]) -> Dict[str, str]:
        repo_dir = (REPOS_DIR / tenant).resolve()
        results: Dict[str, str] = {}
        if not repo_dir.exists():
            return results

        for rel_path in file_paths:
            # Prevent path traversal
            if ".." in rel_path or rel_path.startswith("/") or rel_path.startswith("\\"):
                log.warning("Blocked path traversal attempt: %r", rel_path)
                continue
            target_path = (repo_dir / rel_path).resolve()
            if not str(target_path).startswith(str(repo_dir)):
                log.warning("Blocked escaping path: %r", rel_path)
                continue

            if target_path.exists() and target_path.is_file():
                try:
                    results[rel_path] = target_path.read_text(encoding="utf-8", errors="replace")
                except Exception as e:
                    log.warning("Could not read %s: %s", rel_path, e)
        return results


# Tool class mapping for the policy engine
TOOL_CLASSES = {
    "search_patterns": "READ",
    "fetch_code_snippet": "READ",
    "create_github_pr": "WRITE",
    "send_slack_alert": "WRITE",
    "restart_service": "DESTRUCTIVE",
    "delete_branch": "DESTRUCTIVE",
    "merge_pr": "DESTRUCTIVE",
    "force_push": "DESTRUCTIVE",
}
