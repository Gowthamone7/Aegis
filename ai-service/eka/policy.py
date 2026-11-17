"""
EKA Policy Engine

Classifies tool calls as READ / WRITE / DESTRUCTIVE and applies role-based
access control + confidence threshold checks.

Tool registry:
  search_patterns      → READ
  fetch_code_snippet   → READ
  create_github_pr     → WRITE
  send_slack_alert     → WRITE
  restart_service      → DESTRUCTIVE
  delete_branch        → DESTRUCTIVE
  merge_pr             → DESTRUCTIVE
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from .config import settings
from .auth import DEVELOPER, MANAGER, VIEWER, ADMIN


# ─────────────────────────── enums ───────────────────────────────────────────

class ToolClass(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    DESTRUCTIVE = "DESTRUCTIVE"


class Decision(str, Enum):
    ALLOW = "ALLOW"
    CONFIRM = "CONFIRM"   # requires human approval
    BLOCK = "BLOCK"


# ─────────────────────────── tool registry ────────────────────────────────────

TOOL_REGISTRY: dict[str, ToolClass] = {
    "search_patterns": ToolClass.READ,
    "fetch_code_snippet": ToolClass.READ,
    "create_github_pr": ToolClass.WRITE,
    "send_slack_alert": ToolClass.WRITE,
    "restart_service": ToolClass.DESTRUCTIVE,
    "delete_branch": ToolClass.DESTRUCTIVE,
    "merge_pr": ToolClass.DESTRUCTIVE,
}


def get_tool_class(tool_name: str) -> ToolClass:
    """Return the ToolClass for a tool name, defaulting to READ."""
    return TOOL_REGISTRY.get(tool_name, ToolClass.READ)


# ─────────────────────────── policy decision ─────────────────────────────────

@dataclass
class PolicyDecision:
    decision: Decision
    reason: str
    tool: str = ""
    tool_class: str = ""


# ─────────────────────────── policy rules ────────────────────────────────────

class RiskPolicy:
    """
    Applies deterministic policy rules in order of precedence:

    1. DESTRUCTIVE tools → always BLOCK
    2. WRITE tools:
       - MANAGER or ADMIN role → ALLOW (regardless of confidence)
       - confidence > T_MATCH and has_citation → ALLOW
       - confidence > T_PARTIAL → CONFIRM (needs human approval)
       - otherwise → BLOCK
    3. READ tools → always ALLOW
    """

    def __init__(self) -> None:
        self.t_match = settings.t_match
        self.t_partial = settings.t_partial

    def check(
        self,
        role: str,
        tool_class: ToolClass | str,
        confidence: float,
        has_citation: bool,
        tool: str = "",
    ) -> PolicyDecision:
        if isinstance(tool_class, str):
            tool_class = ToolClass(tool_class.upper())
        tc_name = tool_class.value

        # ── DESTRUCTIVE ────────────────────────────────────────────────────
        if tool_class == ToolClass.DESTRUCTIVE:
            return PolicyDecision(
                decision=Decision.BLOCK,
                reason="Destructive tools are always blocked by policy.",
                tool=tool,
                tool_class=tc_name,
            )

        # ── READ ───────────────────────────────────────────────────────────
        if tool_class == ToolClass.READ:
            return PolicyDecision(
                decision=Decision.ALLOW,
                reason="Read-only tool — automatically allowed.",
                tool=tool,
                tool_class=tc_name,
            )

        # ── WRITE ──────────────────────────────────────────────────────────
        # No citation, no action
        if not has_citation:
            return PolicyDecision(
                decision=Decision.BLOCK,
                reason="Rule violated: No citation, no action. Grounding required.",
                tool=tool,
                tool_class=tc_name,
            )

        # Manager / Admin can always approve writes
        if role in (MANAGER, ADMIN):
            return PolicyDecision(
                decision=Decision.ALLOW,
                reason=f"Role '{role}' is authorized for write operations.",
                tool=tool,
                tool_class=tc_name,
            )

        # Developer / Viewer with high confidence + citation → ALLOW
        if confidence >= self.t_match and has_citation:
            return PolicyDecision(
                decision=Decision.ALLOW,
                reason=(
                    f"Confidence {confidence:.2f} ≥ T_MATCH {self.t_match:.2f} "
                    "and citations present — auto-allowed."
                ),
                tool=tool,
                tool_class=tc_name,
            )

        # Medium confidence → human approval required
        if confidence >= self.t_partial:
            return PolicyDecision(
                decision=Decision.CONFIRM,
                reason=(
                    f"Confidence {confidence:.2f} between T_PARTIAL "
                    f"{self.t_partial:.2f} and T_MATCH {self.t_match:.2f} — "
                    "requires manager approval."
                ),
                tool=tool,
                tool_class=tc_name,
            )

        # Low confidence → block
        return PolicyDecision(
            decision=Decision.BLOCK,
            reason=(
                f"Confidence {confidence:.2f} < T_PARTIAL {self.t_partial:.2f} — "
                "insufficient evidence to proceed."
            ),
            tool=tool,
            tool_class=tc_name,
        )


# ─────────────────────────── convenience function ─────────────────────────────

_policy = RiskPolicy()


def check_policy(
    role: str,
    tool_class: ToolClass,
    confidence: float,
    has_citation: bool,
    tool: str = "",
) -> PolicyDecision:
    """
    Shorthand for RiskPolicy().check(...).
    Uses a module-level singleton so thresholds are read once from settings.
    """
    return _policy.check(
        role=role,
        tool_class=tool_class,
        confidence=confidence,
        has_citation=has_citation,
        tool=tool,
    )
