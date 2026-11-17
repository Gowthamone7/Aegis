"""
EKA 5-Agent Pipeline Execution

Runs the sequential 5-agent pipeline:
START -> research -> context_builder -> reasoning -> security -> executor -> END
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TypedDict

from .agents import (
    research_agent,
    context_builder_agent,
    reasoning_agent,
    security_agent,
    executor_agent,
)

log = logging.getLogger(__name__)


def run_pipeline(
    tenant: str,
    raw_log: str,
    incident_id: int | str = 1,
    username: str = "developer",
    user_role: str = "developer",
    title: str = "Build Failure",
) -> Dict[str, Any]:
    """Runs an incident through the full 5-agent pipeline synchronously and reliably."""
    state: Dict[str, Any] = {
        "incident_id": incident_id,
        "tenant": tenant,
        "username": username,
        "user_role": user_role,
        "title": title,
        "raw_log": raw_log,
        "events": [],
        "injection_detected": False,
        "escalate_flag": False,
    }

    # Node 1: Research Agent
    state = research_agent(state)

    # Node 2 & 3: Context Builder & Reasoning (skip if injection detected)
    if not state.get("injection_detected"):
        state = context_builder_agent(state)
        state = reasoning_agent(state)

    # Node 4: Security Agent (Guardrails, RBAC, Policy Engine)
    state = security_agent(state)

    # Node 5: Executor Agent (Action Execution or Queuing)
    state = executor_agent(state)

    return state
