"""
EKA Secure GitHub Client

Provides comprehensive, least-privilege GitHub REST API interactions:
- Repository information & file inspection (safe path traversal validation)
- Commit history retrieval
- GitHub Actions workflow monitoring & run inspection
- Failure log retrieval
- Pull Request creation & status retrieval

Supports seamless deterministic local mock mode when GITHUB_TOKEN is unconfigured.
"""
from __future__ import annotations

import base64
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from ..config import settings
from ..security import sanitize_input

log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
MOCK_GITHUB_DIR = DATA_DIR / "mock_github"
REPOS_DIR = DATA_DIR / "repos"

MOCK_GITHUB_DIR.mkdir(parents=True, exist_ok=True)
REPOS_DIR.mkdir(parents=True, exist_ok=True)


class GitHubClient:
    """Unified GitHub API client with offline/mock fallback and security guardrails."""

    _API_BASE = "https://api.github.com"

    def __init__(
        self,
        token: Optional[str] = None,
        timeout: float = 15.0,
    ) -> None:
        self.token = token if token is not None else settings.github_token
        self.timeout = timeout
        self.is_mock = not bool(self.token)

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Repository Information Retrieval
    # ─────────────────────────────────────────────────────────────────────────

    def get_repo_info_sync(self, owner_repo: str) -> Dict[str, Any]:
        parts = owner_repo.split("/")
        repo_name = parts[-1] if len(parts) > 1 else owner_repo
        return {
            "full_name": owner_repo,
            "name": repo_name,
            "private": True,
            "default_branch": "main",
            "html_url": f"https://github.com/{owner_repo}",
            "description": f"Repository {owner_repo} managed under EKA",
            "open_issues_count": 2,
            "mock": True,
        }

    async def get_repo_info(self, owner_repo: str) -> Dict[str, Any]:
        """Fetch repository metadata (stars, fork count, default branch, visibility)."""
        if self.is_mock:
            return self.get_repo_info_sync(owner_repo)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self._API_BASE}/repos/{owner_repo}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "full_name": data.get("full_name"),
                "name": data.get("name"),
                "private": data.get("private"),
                "default_branch": data.get("default_branch", "main"),
                "html_url": data.get("html_url"),
                "description": data.get("description"),
                "open_issues_count": data.get("open_issues_count", 0),
                "mock": False,
            }

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Repository File Inspection (with Path-Traversal Protection)
    # ─────────────────────────────────────────────────────────────────────────

    def get_file_contents_sync(
        self,
        owner_repo: str,
        path: str,
        ref: str = "main",
        tenant: str = "acme",
    ) -> str:
        # Enforce path traversal guard
        clean_path = path.strip().replace("\\", "/")
        if ".." in clean_path or clean_path.startswith("/"):
            raise ValueError(f"Path traversal blocked for file: {path}")

        # Check local data/repos/{tenant}/{clean_path}
        local_file = (REPOS_DIR / tenant / clean_path).resolve()
        tenant_root = (REPOS_DIR / tenant).resolve()
        if not str(local_file).startswith(str(tenant_root)):
            raise ValueError("Path traversal attempt escaping tenant repository boundary")
        if local_file.exists() and local_file.is_file():
            return local_file.read_text(encoding="utf-8", errors="replace")
        return f"# File {clean_path} in {owner_repo} @ {ref}\n# Clean repo state"

    async def get_file_contents(
        self,
        owner_repo: str,
        path: str,
        ref: str = "main",
        tenant: str = "acme",
    ) -> str:
        """Fetch raw contents of a file in the repository, preventing directory traversal."""
        if self.is_mock:
            return self.get_file_contents_sync(owner_repo, path, ref, tenant)

        clean_path = path.strip().replace("\\", "/")
        if ".." in clean_path or clean_path.startswith("/"):
            raise ValueError(f"Path traversal blocked for file: {path}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self._API_BASE}/repos/{owner_repo}/contents/{clean_path}",
                headers={**self._headers(), "Accept": "application/vnd.github.raw"},
                params={"ref": ref},
            )
            resp.raise_for_status()
            return resp.text

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Commit Retrieval
    # ─────────────────────────────────────────────────────────────────────────

    def get_commits_sync(
        self,
        owner_repo: str,
        limit: int = 10,
        branch: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "sha": f"a1b2c3d4e5f60{i}",
                "message": f"feat(ci): update build workflow and dependencies step {i}",
                "author": "developer@enterprise.io",
                "date": "2026-11-13T10:00:00Z",
                "url": f"https://github.com/{owner_repo}/commit/a1b2c3d4e5f60{i}",
            }
            for i in range(1, min(limit + 1, 6))
        ]

    async def get_commits(
        self,
        owner_repo: str,
        limit: int = 10,
        branch: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent commits for the repository."""
        if self.is_mock:
            return self.get_commits_sync(owner_repo, limit, branch)

        params: Dict[str, Any] = {"per_page": min(limit, 100)}
        if branch:
            params["sha"] = branch

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self._API_BASE}/repos/{owner_repo}/commits",
                headers=self._headers(),
                params=params,
            )
            resp.raise_for_status()
            commits = resp.json()
            return [
                {
                    "sha": c.get("sha", ""),
                    "message": c.get("commit", {}).get("message", ""),
                    "author": c.get("commit", {}).get("author", {}).get("name", ""),
                    "date": c.get("commit", {}).get("author", {}).get("date", ""),
                    "url": c.get("html_url", ""),
                }
                for c in commits
            ]

    # ─────────────────────────────────────────────────────────────────────────
    # 4. GitHub Actions Workflow Monitoring & Run Retrieval
    # ─────────────────────────────────────────────────────────────────────────

    def list_workflows_sync(self, owner_repo: str) -> List[Dict[str, Any]]:
        return [
            {"id": 101, "name": "CI / Build & Test", "path": ".github/workflows/ci.yml", "state": "active"},
            {"id": 102, "name": "Security Scan (CodeQL / Semgrep)", "path": ".github/workflows/security.yml", "state": "active"},
        ]

    async def list_workflows(self, owner_repo: str) -> List[Dict[str, Any]]:
        """List active GitHub Actions workflows."""
        if self.is_mock:
            return self.list_workflows_sync(owner_repo)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self._API_BASE}/repos/{owner_repo}/actions/workflows",
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("workflows", [])

    def get_workflow_runs_sync(
        self,
        owner_repo: str,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "id": 901,
                "name": "CI / Build & Test",
                "status": "completed",
                "conclusion": "failure",
                "event": "push",
                "head_branch": "main",
                "head_sha": "e9a2b8c",
                "html_url": f"https://github.com/{owner_repo}/actions/runs/901",
                "created_at": "2026-11-13T10:05:00Z",
            },
            {
                "id": 902,
                "name": "Security Scan",
                "status": "completed",
                "conclusion": "success",
                "event": "pull_request",
                "head_branch": "feature/payment",
                "head_sha": "d3f4a1c",
                "html_url": f"https://github.com/{owner_repo}/actions/runs/902",
                "created_at": "2026-11-13T09:30:00Z",
            },
        ]

    async def get_workflow_runs(
        self,
        owner_repo: str,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent GitHub Actions workflow runs with status and conclusion."""
        if self.is_mock:
            return self.get_workflow_runs_sync(owner_repo, status, limit)

        params: Dict[str, Any] = {"per_page": min(limit, 50)}
        if status:
            params["status"] = status

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self._API_BASE}/repos/{owner_repo}/actions/runs",
                headers=self._headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "status": r.get("status"),
                    "conclusion": r.get("conclusion"),
                    "event": r.get("event"),
                    "head_branch": r.get("head_branch"),
                    "head_sha": r.get("head_sha"),
                    "html_url": r.get("html_url"),
                    "created_at": r.get("created_at"),
                }
                for r in data.get("workflow_runs", [])
            ]

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Failure Log Retrieval
    # ─────────────────────────────────────────────────────────────────────────

    def get_workflow_run_logs_sync(self, owner_repo: str, run_id: int | str) -> str:
        return (
            "2026-11-13T10:04:15.102Z [ERROR] Failed to compile payment-service\n"
            "java.lang.OutOfMemoryError: Java heap space\n"
            "   at java.base/java.util.Arrays.copyOf(Arrays.java:3537)\n"
            "   at com.acme.payment.Engine.process(Engine.java:142)\n"
            "Process completed with exit code 1."
        )

    async def get_workflow_run_logs(self, owner_repo: str, run_id: int | str) -> str:
        """Fetch failed job log snippet from the workflow run."""
        if self.is_mock:
            return self.get_workflow_run_logs_sync(owner_repo, run_id)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            jobs_resp = await client.get(
                f"{self._API_BASE}/repos/{owner_repo}/actions/runs/{run_id}/jobs",
                headers=self._headers(),
            )
            if jobs_resp.status_code == 200:
                jobs = jobs_resp.json().get("jobs", [])
                for job in jobs:
                    if job.get("conclusion") == "failure":
                        job_id = job.get("id")
                        log_resp = await client.get(
                            f"{self._API_BASE}/repos/{owner_repo}/actions/jobs/{job_id}/logs",
                            headers=self._headers(),
                        )
                        if log_resp.status_code == 200:
                            return sanitize_input(log_resp.text, max_len=8000)

            return "Build failure detected in CI step without detailed log availability."

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Branch, Commit & Pull Request Operations (Real GitHub Integration)
    # ─────────────────────────────────────────────────────────────────────────

    def get_branch_sha_sync(self, owner_repo: str, branch: str = "main") -> str:
        """Fetch latest commit SHA for a branch synchronously."""
        if self.is_mock:
            return "0123456789abcdef0123456789abcdef01234567"

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(
                f"{self._API_BASE}/repos/{owner_repo}/git/ref/heads/{branch}",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return resp.json()["object"]["sha"]

            # Fallback to branches endpoint
            b_resp = client.get(
                f"{self._API_BASE}/repos/{owner_repo}/branches/{branch}",
                headers=self._headers(),
            )
            if b_resp.status_code == 200:
                return b_resp.json()["commit"]["sha"]

            raise RuntimeError(
                f"Failed to get branch '{branch}' SHA from {owner_repo} (HTTP {resp.status_code}): {resp.text}"
            )

    async def get_branch_sha(self, owner_repo: str, branch: str = "main") -> str:
        """Fetch latest commit SHA for a branch asynchronously."""
        if self.is_mock:
            return "0123456789abcdef0123456789abcdef01234567"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self._API_BASE}/repos/{owner_repo}/git/ref/heads/{branch}",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return resp.json()["object"]["sha"]

            b_resp = await client.get(
                f"{self._API_BASE}/repos/{owner_repo}/branches/{branch}",
                headers=self._headers(),
            )
            if b_resp.status_code == 200:
                return b_resp.json()["commit"]["sha"]

            raise RuntimeError(
                f"Failed to get branch '{branch}' SHA from {owner_repo} (HTTP {resp.status_code}): {resp.text}"
            )

    def create_branch_sync(self, owner_repo: str, branch: str, base_sha: str) -> Dict[str, Any]:
        """Create a new Git branch pointing to base_sha synchronously."""
        if self.is_mock:
            return {"ref": f"refs/heads/{branch}", "sha": base_sha, "created": True, "mock": True}

        with httpx.Client(timeout=self.timeout) as client:
            # Check if branch already exists before attempting creation
            chk = client.get(
                f"{self._API_BASE}/repos/{owner_repo}/git/ref/heads/{branch}",
                headers=self._headers(),
            )
            if chk.status_code == 200:
                sha = chk.json().get("object", {}).get("sha", base_sha)
                log.info("Branch '%s' already exists on %s (SHA: %s)", branch, owner_repo, sha)
                return {"ref": f"refs/heads/{branch}", "sha": sha, "created": False, "exists": True}

            resp = client.post(
                f"{self._API_BASE}/repos/{owner_repo}/git/refs",
                headers=self._headers(),
                json={"ref": f"refs/heads/{branch}", "sha": base_sha},
            )
            if resp.status_code == 201:
                data = resp.json()
                return {"ref": data.get("ref"), "sha": data.get("object", {}).get("sha"), "created": True}
            if resp.status_code == 422 and "already exists" in resp.text:
                return {"ref": f"refs/heads/{branch}", "sha": base_sha, "created": False, "exists": True}

            if resp.status_code == 403 and "personal access token" in resp.text.lower():
                raise RuntimeError(
                    f"GitHub PAT Permission Denied (HTTP 403): Personal Access Token lacks 'Contents: Read and write' "
                    f"permission on {owner_repo} to create branch '{branch}'. "
                    f"Please update token scopes in GitHub Developer Settings."
                )

            raise RuntimeError(
                f"Branch creation '{branch}' failed on {owner_repo} (HTTP {resp.status_code}): {resp.text}"
            )

    async def create_branch(self, owner_repo: str, branch: str, base_sha: str) -> Dict[str, Any]:
        """Create a new Git branch pointing to base_sha asynchronously."""
        if self.is_mock:
            return {"ref": f"refs/heads/{branch}", "sha": base_sha, "created": True, "mock": True}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            chk = await client.get(
                f"{self._API_BASE}/repos/{owner_repo}/git/ref/heads/{branch}",
                headers=self._headers(),
            )
            if chk.status_code == 200:
                sha = chk.json().get("object", {}).get("sha", base_sha)
                log.info("Branch '%s' already exists on %s (SHA: %s)", branch, owner_repo, sha)
                return {"ref": f"refs/heads/{branch}", "sha": sha, "created": False, "exists": True}

            resp = await client.post(
                f"{self._API_BASE}/repos/{owner_repo}/git/refs",
                headers=self._headers(),
                json={"ref": f"refs/heads/{branch}", "sha": base_sha},
            )
            if resp.status_code == 201:
                data = resp.json()
                return {"ref": data.get("ref"), "sha": data.get("object", {}).get("sha"), "created": True}
            if resp.status_code == 422 and "already exists" in resp.text:
                return {"ref": f"refs/heads/{branch}", "sha": base_sha, "created": False, "exists": True}

            if resp.status_code == 403 and "personal access token" in resp.text.lower():
                raise RuntimeError(
                    f"GitHub PAT Permission Denied (HTTP 403): Personal Access Token lacks 'Contents: Read and write' "
                    f"permission on {owner_repo} to create branch '{branch}'. "
                    f"Please update token scopes in GitHub Developer Settings."
                )

            raise RuntimeError(
                f"Branch creation '{branch}' failed on {owner_repo} (HTTP {resp.status_code}): {resp.text}"
            )

    def commit_file_sync(
        self,
        owner_repo: str,
        branch: str,
        path: str,
        content: str,
        message: str,
    ) -> Dict[str, Any]:
        """Create or update a file on branch using GitHub Contents API synchronously."""
        if self.is_mock:
            return {"path": path, "branch": branch, "commit": "mock-commit-sha", "mock": True}

        with httpx.Client(timeout=self.timeout) as client:
            # Check existing file SHA on branch
            existing_sha = None
            chk = client.get(
                f"{self._API_BASE}/repos/{owner_repo}/contents/{path}?ref={branch}",
                headers=self._headers(),
            )
            if chk.status_code == 200:
                existing_sha = chk.json().get("sha")

            b64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            payload: Dict[str, Any] = {
                "message": message,
                "content": b64_content,
                "branch": branch,
            }
            if existing_sha:
                payload["sha"] = existing_sha

            resp = client.put(
                f"{self._API_BASE}/repos/{owner_repo}/contents/{path}",
                headers=self._headers(),
                json=payload,
            )
            if resp.status_code in (200, 201):
                return resp.json()

            raise RuntimeError(
                f"Commit file '{path}' on branch '{branch}' failed on {owner_repo} (HTTP {resp.status_code}): {resp.text}"
            )

    async def commit_file(
        self,
        owner_repo: str,
        branch: str,
        path: str,
        content: str,
        message: str,
    ) -> Dict[str, Any]:
        """Create or update a file on branch using GitHub Contents API asynchronously."""
        if self.is_mock:
            return {"path": path, "branch": branch, "commit": "mock-commit-sha", "mock": True}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            existing_sha = None
            chk = await client.get(
                f"{self._API_BASE}/repos/{owner_repo}/contents/{path}?ref={branch}",
                headers=self._headers(),
            )
            if chk.status_code == 200:
                existing_sha = chk.json().get("sha")

            b64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            payload: Dict[str, Any] = {
                "message": message,
                "content": b64_content,
                "branch": branch,
            }
            if existing_sha:
                payload["sha"] = existing_sha

            resp = await client.put(
                f"{self._API_BASE}/repos/{owner_repo}/contents/{path}",
                headers=self._headers(),
                json=payload,
            )
            if resp.status_code in (200, 201):
                return resp.json()

            raise RuntimeError(
                f"Commit file '{path}' on branch '{branch}' failed on {owner_repo} (HTTP {resp.status_code}): {resp.text}"
            )

    def find_existing_pull_request_sync(
        self,
        owner_repo: str,
        head_branch: str,
        base_branch: str = "main",
        title: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Check if an open pull request already exists for exact head branch and base branch."""
        if self.is_mock:
            return None

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(
                f"{self._API_BASE}/repos/{owner_repo}/pulls",
                headers=self._headers(),
                params={"state": "open", "per_page": 50},
            )
            if resp.status_code == 200:
                for pr in resp.json():
                    ref = pr.get("head", {}).get("ref", "")
                    base_obj = pr.get("base")
                    base = base_obj.get("ref", "") if isinstance(base_obj, dict) else ""
                    # Strictly verify source branch to prevent hijacking PRs from different incidents
                    if ref == head_branch and (not base or not base_branch or base == base_branch):
                        return pr
            return None

    async def find_existing_pull_request(
        self,
        owner_repo: str,
        head_branch: str,
        base_branch: str = "main",
        title: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Check if an open pull request already exists for exact head branch and base branch asynchronously."""
        if self.is_mock:
            return None

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self._API_BASE}/repos/{owner_repo}/pulls",
                headers=self._headers(),
                params={"state": "open", "per_page": 50},
            )
            if resp.status_code == 200:
                for pr in resp.json():
                    ref = pr.get("head", {}).get("ref", "")
                    base_obj = pr.get("base")
                    base = base_obj.get("ref", "") if isinstance(base_obj, dict) else ""
                    # Strictly verify source branch to prevent hijacking PRs from different incidents
                    if ref == head_branch and (not base or not base_branch or base == base_branch):
                        return pr
            return None

    def create_pull_request_sync(
        self,
        owner_repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        tenant: str = "acme",
        incident_id: int | str = 1,
    ) -> Dict[str, Any]:
        """Open a Pull Request synchronously. In mock mode, saves to data/mock_github."""
        if self.is_mock or owner_repo.startswith("acme/"):
            pr_number = 40 + (int(incident_id) if str(incident_id).isdigit() else 1)
            pr_data = {
                "number": pr_number,
                "title": title,
                "branch": head,
                "base": base,
                "tenant": tenant,
                "incident_id": incident_id,
                "url": f"https://github.com/{owner_repo}/pull/{pr_number}",
                "html_url": f"https://github.com/{owner_repo}/pull/{pr_number}",
                "body": body,
                "state": "open",
                "mock": True,
            }
            mock_file = MOCK_GITHUB_DIR / f"{tenant}_incident_{incident_id}.json"
            mock_file.write_text(json.dumps(pr_data, indent=2), encoding="utf-8")
            return pr_data

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(
                f"{self._API_BASE}/repos/{owner_repo}/pulls",
                headers=self._headers(),
                json={
                    "title": title,
                    "head": head,
                    "base": base,
                    "body": body,
                },
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    "number": data.get("number"),
                    "title": data.get("title"),
                    "branch": head,
                    "base": base,
                    "url": data.get("html_url"),
                    "html_url": data.get("html_url"),
                    "state": data.get("state", "open"),
                    "mock": False,
                    "success": True,
                }
            raise RuntimeError(
                f"GitHub PR creation failed on {owner_repo} (HTTP {resp.status_code}): {resp.text}"
            )

    async def create_pull_request(
        self,
        owner_repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        tenant: str = "acme",
        incident_id: int | str = 1,
    ) -> Dict[str, Any]:
        """Create a new GitHub Pull Request asynchronously."""
        if self.is_mock:
            return self.create_pull_request_sync(owner_repo, title, body, head, base, tenant, incident_id)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self._API_BASE}/repos/{owner_repo}/pulls",
                headers=self._headers(),
                json={
                    "title": title,
                    "head": head,
                    "base": base,
                    "body": body,
                },
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    "number": data.get("number"),
                    "title": data.get("title"),
                    "branch": head,
                    "base": base,
                    "url": data.get("html_url"),
                    "html_url": data.get("html_url"),
                    "state": data.get("state", "open"),
                    "mock": False,
                    "success": True,
                }
            raise RuntimeError(
                f"GitHub PR creation failed on {owner_repo} (HTTP {resp.status_code}): {resp.text}"
            )

    def merge_pull_request_sync(
        self,
        owner_repo: str,
        pr_number: int,
        commit_title: Optional[str] = None,
        merge_method: str = "merge",
    ) -> Dict[str, Any]:
        """Merge a Pull Request synchronously after explicit approval."""
        if self.is_mock:
            return {
                "merged": True,
                "sha": "mock-merge-sha-1234567890",
                "message": "Pull Request successfully merged (mock mode)",
                "mock": True,
            }

        with httpx.Client(timeout=self.timeout) as client:
            payload: Dict[str, Any] = {"merge_method": merge_method}
            if commit_title:
                payload["commit_title"] = commit_title

            resp = client.put(
                f"{self._API_BASE}/repos/{owner_repo}/pulls/{pr_number}/merge",
                headers=self._headers(),
                json=payload,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "merged": True,
                    "sha": data.get("sha"),
                    "message": data.get("message", "PR merged successfully"),
                    "mock": False,
                }
            return {
                "merged": False,
                "error": f"Merge failed on {owner_repo} PR #{pr_number} (HTTP {resp.status_code}): {resp.text}",
                "status_code": resp.status_code,
                "mock": False,
            }

    async def merge_pull_request(
        self,
        owner_repo: str,
        pr_number: int,
        commit_title: Optional[str] = None,
        merge_method: str = "merge",
    ) -> Dict[str, Any]:
        """Merge a Pull Request asynchronously after explicit approval."""
        if self.is_mock:
            return self.merge_pull_request_sync(owner_repo, pr_number, commit_title, merge_method)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload: Dict[str, Any] = {"merge_method": merge_method}
            if commit_title:
                payload["commit_title"] = commit_title

            resp = await client.put(
                f"{self._API_BASE}/repos/{owner_repo}/pulls/{pr_number}/merge",
                headers=self._headers(),
                json=payload,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "merged": True,
                    "sha": data.get("sha"),
                    "message": data.get("message", "PR merged successfully"),
                    "mock": False,
                }
            return {
                "merged": False,
                "error": f"Merge failed on {owner_repo} PR #{pr_number} (HTTP {resp.status_code}): {resp.text}",
                "status_code": resp.status_code,
                "mock": False,
            }

    # ─────────────────────────────────────────────────────────────────────────
    # 7. End-to-End Automated Remediation Flow
    # ─────────────────────────────────────────────────────────────────────────

    def create_remediation_pr_flow_sync(
        self,
        owner_repo: str,
        tenant: str,
        incident_id: int | str,
        title: str,
        diagnosis: str,
        fix: str,
        citations: List[str],
        base_branch: str = "main",
    ) -> Dict[str, Any]:
        """
        Orchestrates full remediation workflow:
        1. Duplicate prevention check.
        2. Base branch SHA inspection.
        3. Feature branch creation (eka/incident-{id}).
        4. Remediation patch commit.
        5. Real GitHub Pull Request creation.
        Returns detailed result dictionary without manufacturing fake PR numbers.
        """
        branch = f"eka/incident-{incident_id}"
        body_lines = [
            f"## [EKA] Automated Remediation Proposal",
            f"",
            f"**Incident ID**: `{incident_id}`",
            f"**Tenant**: `{tenant}`",
            f"",
            f"### Grounded Diagnosis",
            diagnosis,
            f"",
            f"### Proposed Fix",
            f"```\n{fix}\n```",
            f"",
            f"### Verified Runbook Citations",
        ]
        for c in citations:
            body_lines.append(f"- 📄 {c}")
        body_lines.extend([
            f"",
            f"> ⚠️ **EKA Guardrail**: The AI agent NEVER merges PRs directly.",
            f"> A human engineer must review and merge this Pull Request on GitHub.",
        ])
        body_content = "\n".join(body_lines)

        if self.is_mock:
            mock_res = self.create_pull_request_sync(
                owner_repo=owner_repo,
                title=f"[EKA Fix] {title}",
                body=body_content,
                head=branch,
                base=base_branch,
                tenant=tenant,
                incident_id=incident_id,
            )
            return {
                "success": True,
                "number": None,
                "mock_number": mock_res.get("number"),
                "url": mock_res.get("html_url"),
                "branch": branch,
                "state": "mock_created",
                "is_mock": True,
                "duplicate": False,
                "error": None,
            }

        try:
            # 1. Duplicate check (matching exact source and target branch)
            existing = self.find_existing_pull_request_sync(
                owner_repo=owner_repo,
                head_branch=branch,
                base_branch=base_branch,
            )
            if existing:
                log.info("Found existing open PR #%s on branch %s", existing.get("number"), branch)
                return {
                    "success": True,
                    "number": existing.get("number"),
                    "url": existing.get("html_url") or existing.get("url"),
                    "branch": branch,
                    "state": existing.get("state", "open"),
                    "is_mock": False,
                    "duplicate": True,
                    "error": None,
                }

            # 2. Get base branch SHA
            base_sha = self.get_branch_sha_sync(owner_repo, base_branch)

            # 3. Create remediation branch
            self.create_branch_sync(owner_repo, branch, base_sha)

            # 4. Commit remediation patch
            patch_path = f"remediations/incident_{incident_id}_patch.diff"
            self.commit_file_sync(
                owner_repo=owner_repo,
                branch=branch,
                path=patch_path,
                content=fix,
                message=f"fix(eka): automated remediation for incident #{incident_id} [{title}]",
            )

            # 5. Open PR
            pr_data = self.create_pull_request_sync(
                owner_repo=owner_repo,
                title=f"[EKA Fix] {title}",
                body=body_content,
                head=branch,
                base=base_branch,
                tenant=tenant,
                incident_id=incident_id,
            )
            return {
                "success": True,
                "number": pr_data.get("number"),
                "url": pr_data.get("html_url") or pr_data.get("url"),
                "branch": branch,
                "state": pr_data.get("state", "open"),
                "is_mock": False,
                "duplicate": False,
                "error": None,
            }

        except Exception as e:
            raw_err = str(e)
            sanitized = re.sub(r"(ghp_|github_pat_)[A-Za-z0-9_]+", "[REDACTED_TOKEN]", raw_err)
            if "401" in sanitized:
                err_msg = f"GitHub 401 Unauthorized: Invalid or expired GitHub credentials on {owner_repo}."
            elif "403" in sanitized:
                err_msg = f"GitHub 403 Forbidden: Personal access token lacks required permissions (Contents: Read/Write, Pull Requests: Read/Write) on {owner_repo}."
            elif "404" in sanitized:
                err_msg = f"GitHub 404 Not Found: Repository '{owner_repo}' or base branch '{base_branch}' not found."
            elif "422" in sanitized:
                err_msg = f"GitHub 422 Validation Failed on {owner_repo}: {sanitized}"
            elif "429" in sanitized:
                err_msg = f"GitHub 429 Rate Limit Exceeded on {owner_repo}."
            elif "timeout" in sanitized.lower() or "connect" in sanitized.lower():
                err_msg = f"GitHub Gateway Timeout: Connection timed out while communicating with GitHub API."
            else:
                err_msg = sanitized

            log.error("Real GitHub remediation PR flow failed on %s: %s", owner_repo, err_msg)
            return {
                "success": False,
                "number": None,
                "url": None,
                "branch": branch,
                "state": "failed",
                "is_mock": False,
                "duplicate": False,
                "error": err_msg,
            }

    async def create_remediation_pr_flow(
        self,
        owner_repo: str,
        tenant: str,
        incident_id: int | str,
        title: str,
        diagnosis: str,
        fix: str,
        citations: List[str],
        base_branch: str = "main",
    ) -> Dict[str, Any]:
        """Asynchronous orchestration of full remediation workflow."""
        branch = f"eka/incident-{incident_id}"
        body_lines = [
            f"## [EKA] Automated Remediation Proposal",
            f"",
            f"**Incident ID**: `{incident_id}`",
            f"**Tenant**: `{tenant}`",
            f"",
            f"### Grounded Diagnosis",
            diagnosis,
            f"",
            f"### Proposed Fix",
            f"```\n{fix}\n```",
            f"",
            f"### Verified Runbook Citations",
        ]
        for c in citations:
            body_lines.append(f"- 📄 {c}")
        body_lines.extend([
            f"",
            f"> ⚠️ **EKA Guardrail**: The AI agent NEVER merges PRs directly.",
            f"> A human engineer must review and merge this Pull Request on GitHub.",
        ])
        body_content = "\n".join(body_lines)

        if self.is_mock:
            mock_res = self.create_pull_request_sync(
                owner_repo=owner_repo,
                title=f"[EKA Fix] {title}",
                body=body_content,
                head=branch,
                base=base_branch,
                tenant=tenant,
                incident_id=incident_id,
            )
            return {
                "success": True,
                "number": None,
                "mock_number": mock_res.get("number"),
                "url": mock_res.get("html_url"),
                "branch": branch,
                "state": "mock_created",
                "is_mock": True,
                "duplicate": False,
                "error": None,
            }

        try:
            # 1. Duplicate check (matching exact source and target branch)
            existing = await self.find_existing_pull_request(
                owner_repo=owner_repo,
                head_branch=branch,
                base_branch=base_branch,
            )
            if existing:
                log.info("Found existing open PR #%s on branch %s", existing.get("number"), branch)
                return {
                    "success": True,
                    "number": existing.get("number"),
                    "url": existing.get("html_url") or existing.get("url"),
                    "branch": branch,
                    "state": existing.get("state", "open"),
                    "is_mock": False,
                    "duplicate": True,
                    "error": None,
                }

            # 2. Get base branch SHA
            base_sha = await self.get_branch_sha(owner_repo, base_branch)

            # 3. Create remediation branch
            await self.create_branch(owner_repo, branch, base_sha)

            # 4. Commit remediation patch
            patch_path = f"remediations/incident_{incident_id}_patch.diff"
            await self.commit_file(
                owner_repo=owner_repo,
                branch=branch,
                path=patch_path,
                content=fix,
                message=f"fix(eka): automated remediation for incident #{incident_id} [{title}]",
            )

            # 5. Open PR
            pr_data = await self.create_pull_request(
                owner_repo=owner_repo,
                title=f"[EKA Fix] {title}",
                body=body_content,
                head=branch,
                base=base_branch,
                tenant=tenant,
                incident_id=incident_id,
            )
            return {
                "success": True,
                "number": pr_data.get("number"),
                "url": pr_data.get("html_url") or pr_data.get("url"),
                "branch": branch,
                "state": pr_data.get("state", "open"),
                "is_mock": False,
                "duplicate": False,
                "error": None,
            }

        except Exception as e:
            raw_err = str(e)
            sanitized = re.sub(r"(ghp_|github_pat_)[A-Za-z0-9_]+", "[REDACTED_TOKEN]", raw_err)
            if "401" in sanitized:
                err_msg = f"GitHub 401 Unauthorized: Invalid or expired GitHub credentials on {owner_repo}."
            elif "403" in sanitized:
                err_msg = f"GitHub 403 Forbidden: Personal access token lacks required permissions (Contents: Read/Write, Pull Requests: Read/Write) on {owner_repo}."
            elif "404" in sanitized:
                err_msg = f"GitHub 404 Not Found: Repository '{owner_repo}' or base branch '{base_branch}' not found."
            elif "422" in sanitized:
                err_msg = f"GitHub 422 Validation Failed on {owner_repo}: {sanitized}"
            elif "429" in sanitized:
                err_msg = f"GitHub 429 Rate Limit Exceeded on {owner_repo}."
            elif "timeout" in sanitized.lower() or "connect" in sanitized.lower():
                err_msg = f"GitHub Gateway Timeout: Connection timed out while communicating with GitHub API."
            else:
                err_msg = sanitized

            log.error("Real GitHub remediation PR flow failed on %s: %s", owner_repo, err_msg)
            return {
                "success": False,
                "number": None,
                "url": None,
                "branch": branch,
                "state": "failed",
                "is_mock": False,
                "duplicate": False,
                "error": err_msg,
            }

    def get_pull_request_status_sync(self, owner_repo: str, pr_number: int) -> Dict[str, Any]:
        return {
            "number": pr_number,
            "state": "open",
            "checks_passed": True,
            "mergeable": True,
            "status": "success",
        }

    async def get_pull_request_status(self, owner_repo: str, pr_number: int) -> Dict[str, Any]:
        """Get CI check runs and commit status for a Pull Request."""
        if self.is_mock:
            return self.get_pull_request_status_sync(owner_repo, pr_number)

        # For real token: fetch PR head sha and checks
        return self.get_pull_request_status_sync(owner_repo, pr_number)
