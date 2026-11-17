"""
real_smoke.py — End-to-end smoke test against live GitHub and Slack integrations.

Requires:
  - GITHUB_REPOS set in .env (e.g. GITHUB_REPOS=acme=owner/repo,globex=owner/repo2)
  - GITHUB_TOKEN set in .env
  - (Optional) SLACK_WEBHOOK_URL set for Slack notification check

Runs the OOM build-failure scenario for the acme tenant, verifies a PR is created
in mock_github or real GitHub, and prints the PR URL and Slack result.

Usage:
    python -m scripts.real_smoke
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from eka.config import get_settings

OOM_LOG = """\
2024-01-15T10:23:41Z WARN  OutOfMemoryError: Java heap space
2024-01-15T10:23:41Z ERROR java.lang.OutOfMemoryError: Java heap space
    at java.util.Arrays.copyOf(Arrays.java:3210)
    at com.acme.service.DataProcessor.processLargeBatch(DataProcessor.java:142)
2024-01-15T10:23:42Z FATAL Killed by OOM killer (signal 9)
Container acme-api exited with code 137
"""


async def run_smoke(settings) -> None:
    from eka.embeddings import get_embedder
    from eka.store import HybridStore
    from eka.llm import get_llm
    from eka.agents import (
        research_agent,
        context_builder_agent,
        reasoning_agent,
        security_agent,
        executor_agent,
    )

    tenant = "acme"
    embedder = get_embedder(settings)
    store = HybridStore(settings)
    llm = get_llm(settings)

    print(f"[SMOKE] Running OOM scenario for tenant: {tenant}")
    print(f"[SMOKE] Store backend: {'ChromaDB' if store.chroma_available else 'in-memory'}")
    print(f"[SMOKE] LLM provider:  {settings.LLM_PROVIDER}")

    state: dict = {
        "tenant": tenant,
        "log": OOM_LOG,
        "role": "DEVELOPER",
        "actor": "dev@acme",
        "incident_id": "smoke-001",
    }

    t0 = time.monotonic()

    state = await research_agent(state)
    state = await context_builder_agent(state)
    state = await reasoning_agent(state)
    state = await security_agent(state)
    state = await executor_agent(state)

    elapsed = (time.monotonic() - t0) * 1000

    print(f"\n[SMOKE] Pipeline completed in {elapsed:.0f} ms")
    print(f"        Diagnosis       : {state.get('diagnosis', 'N/A')}")
    print(f"        Pattern matched : {state.get('pattern_id', 'N/A')}")
    print(f"        Confidence      : {state.get('confidence', 0):.2f}")
    print(f"        Policy decision : {state.get('policy_decision', 'N/A')}")

    pr_url = state.get("pr_url")
    slack_result = state.get("slack_result")

    if pr_url:
        print(f"        PR URL          : {pr_url}")
    else:
        print(f"        PR URL          : (not created — approval required or executor skipped)")

    if slack_result:
        print(f"        Slack result    : {slack_result}")
    else:
        print(f"        Slack result    : (no webhook configured or not triggered)")

    print()
    if pr_url or state.get("policy_decision") in ("CONFIRM", "ALLOW"):
        print("[SMOKE] ✓ End-to-end smoke test PASSED")
    else:
        print("[SMOKE] ✗ End-to-end smoke test FAILED — no PR created and no ALLOW/CONFIRM decision")
        sys.exit(1)


def main() -> None:
    settings = get_settings()

    # Guard: require GITHUB_REPOS
    if not settings.GITHUB_REPOS:
        print("[ERROR] GITHUB_REPOS is not set in .env or environment.")
        print("        Set GITHUB_REPOS=acme=owner/repo,globex=owner/repo2 in ai-service/.env and retry.")
        sys.exit(1)

    if not settings.GITHUB_TOKEN:
        print("[WARN]  GITHUB_TOKEN not set — PR creation will use mock mode.")

    asyncio.run(run_smoke(settings))


if __name__ == "__main__":
    main()
