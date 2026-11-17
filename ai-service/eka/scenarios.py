"""
EKA Built-in Test Scenarios

Five pre-built incidents for demo / testing without real log ingestion.

Scenario fields:
  id               — short slug
  name             — human-readable title
  tenant           — tenant slug
  description      — what this scenario tests
  raw_log          — realistic log snippet
  expected_pattern — the pattern ID the pipeline should identify
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Scenario:
    id: str
    name: str
    tenant: str
    description: str
    raw_log: str
    expected_pattern: str


_SCENARIOS: list[Scenario] = [
    Scenario(
        id="oom",
        name="OutOfMemory Heap Error",
        tenant="acme",
        description=(
            "Simulates a Java service crashing with an OutOfMemoryError when "
            "the JVM heap is exhausted under load. Tests OOM pattern detection."
        ),
        raw_log=(
            "2024-03-15T12:34:56Z ERROR [payment-service] Unhandled exception in thread 'main'\n"
            "java.lang.OutOfMemoryError: Java heap space\n"
            "\tat java.base/java.util.Arrays.copyOf(Arrays.java:3745)\n"
            "\tat java.base/java.util.ArrayList.grow(ArrayList.java:265)\n"
            "\tat com.acme.payment.OrderProcessor.loadOrders(OrderProcessor.java:142)\n"
            "\tat com.acme.payment.OrderProcessor.run(OrderProcessor.java:88)\n"
            "GC overhead limit exceeded\n"
            "Heap dump written to: /tmp/java_pid1234.hprof\n"
            "JVM flags: -Xms256m -Xmx512m -XX:+HeapDumpOnOutOfMemoryError\n"
            "Total orders in memory: 487,329 — peak RSS: 523 MB"
        ),
        expected_pattern="oom",
    ),
    Scenario(
        id="dep_missing",
        name="Missing npm Dependency",
        tenant="acme",
        description=(
            "Simulates a Node.js build failure caused by a missing npm package. "
            "Tests dependency resolution pattern detection."
        ),
        raw_log=(
            "2024-03-15T09:12:00Z INFO  [build-service] Starting npm install\n"
            "npm warn deprecated inflight@1.0.6\n"
            "npm error code MODULE_NOT_FOUND\n"
            "npm error Cannot find module '@acme/shared-utils'\n"
            "npm error Require stack:\n"
            "npm error - /app/src/index.js\n"
            "npm error - /app/server.js\n"
            "npm error A complete log of this run can be found in:\n"
            "npm error     /root/.npm/_logs/2024-03-15T09_12_00_000Z-debug-0.log\n"
            "ERROR: build failed with exit code 1\n"
            "Missing dependency: @acme/shared-utils@^2.1.0 not found in registry"
        ),
        expected_pattern="dep_missing",
    ),
    Scenario(
        id="env_missing",
        name="Missing Environment Variable",
        tenant="globex",
        description=(
            "Simulates a service startup failure because a required environment "
            "variable is not configured. Tests env-var pattern detection."
        ),
        raw_log=(
            "2024-03-15T08:00:01Z INFO  [api-gateway] Initialising configuration\n"
            "2024-03-15T08:00:01Z INFO  [api-gateway] Loading environment...\n"
            "2024-03-15T08:00:01Z ERROR [api-gateway] Configuration validation failed\n"
            "KeyError: 'DATABASE_URL'\n"
            "Traceback (most recent call last):\n"
            "  File \"/app/config.py\", line 34, in load\n"
            "    db_url = os.environ['DATABASE_URL']\n"
            "  File \"<frozen importlib._bootstrap>\", line 241, in _call_with_frames_cleaned\n"
            "KeyError: 'DATABASE_URL'\n"
            "Required environment variables: DATABASE_URL, REDIS_URL, JWT_SECRET\n"
            "Missing: DATABASE_URL\n"
            "process.env.DATABASE_URL is undefined — check your deployment config"
        ),
        expected_pattern="env_missing",
    ),
    Scenario(
        id="port_conflict",
        name="Port Conflict (EADDRINUSE)",
        tenant="acme",
        description=(
            "Simulates a Node.js web server failing to start because port 3000 "
            "is already in use by another process."
        ),
        raw_log=(
            "2024-03-15T10:45:00Z INFO  [web-server] Starting HTTP server on port 3000\n"
            "events.js:292\n"
            "      throw er; // Unhandled 'error' event\n"
            "      ^\n"
            "\n"
            "Error: listen EADDRINUSE: address already in use :::3000\n"
            "    at Server.setupListenHandle [as _listen2] (net.js:1324:16)\n"
            "    at listenInCluster (net.js:1372:12)\n"
            "    at Server.listen (net.js:1460:7)\n"
            "    at Function.listen (/app/node_modules/express/lib/application.js:618:24)\n"
            "    at Object.<anonymous> (/app/src/server.js:42:5)\n"
            "Emitted 'error' event on Server instance at:\n"
            "    at emitErrorNT (net.js:1351:8)\n"
            "    at processTicksAndRejections (internal/process/task_queues.js:82:21) {\n"
            "  code: 'EADDRINUSE',\n"
            "  errno: -98,\n"
            "  syscall: 'listen',\n"
            "  address: '::',\n"
            "  port: 3000\n"
            "}"
        ),
        expected_pattern="port_conflict",
    ),
    Scenario(
        id="build_timeout",
        name="CI Build Timeout",
        tenant="globex",
        description=(
            "Simulates a CI pipeline build that exceeds its time limit, "
            "causing an automatic cancellation."
        ),
        raw_log=(
            "2024-03-15T11:00:00Z INFO  [ci-runner] Starting build job #4821 for branch main\n"
            "2024-03-15T11:00:05Z INFO  [ci-runner] Installing dependencies...\n"
            "2024-03-15T11:04:30Z INFO  [ci-runner] Running test suite...\n"
            "2024-03-15T11:14:30Z INFO  [ci-runner] Running integration tests...\n"
            "2024-03-15T11:30:00Z WARN  [ci-runner] Build has been running for 30 minutes\n"
            "2024-03-15T11:45:00Z ERROR [ci-runner] Build exceeded time limit of 45 minutes\n"
            "2024-03-15T11:45:00Z ERROR [ci-runner] Job #4821 timed out and has been cancelled\n"
            "Timeout: CI build exceeded time limit\n"
            "Build failed: timed out after 2700s\n"
            "Consider: splitting test suite, adding caching, or increasing timeout\n"
            "Last successful step: integration-tests (started at 11:14:30)\n"
            "Exceeded time limit: 45m 0s"
        ),
        expected_pattern="build_timeout",
    ),
]

_INDEX: dict[str, Scenario] = {s.id: s for s in _SCENARIOS}


def get_scenarios() -> list[Scenario]:
    """Return all built-in test scenarios."""
    return list(_SCENARIOS)


def get_scenario(scenario_id: str) -> Optional[Scenario]:
    """Return a scenario by its ID, or None if not found."""
    return _INDEX.get(scenario_id)
