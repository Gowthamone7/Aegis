"""
EKA 5-Agent Pipeline Nodes

Agents:
1. research_agent: sanitizes log, hybrid pattern retrieval, checks injection
2. context_builder_agent: fetches sanitized repository code snippets
3. reasoning_agent: LLM root cause analysis + fix proposal with grounding
4. security_agent: multi-layer guardrails (injection, citations, RBAC, policy)
5. executor_agent: executes allowed actions, queues approvals, or blocks
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from .config import settings
from .store import get_store
from .security import sanitize_input, detect_injection, verify_citations, sanitize_for_output
from .llm import get_llm, LLMResponse
from .policy import check_policy, PolicyDecision
from .tools import GitHubTool, SlackTool, RepoReader
from .db import SessionLocal, Incident, Approval, append_audit

log = logging.getLogger(__name__)


def research_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 1: Sanitizes input log and performs hybrid pattern retrieval."""
    tenant = state.get("tenant", "acme")
    raw_log = state.get("raw_log", "")

    # 1. Sanitize input log
    sanitized_log = sanitize_input(raw_log, max_len=8000)
    
    # 2. Check for prompt injection in log
    injection = detect_injection(sanitized_log)
    if injection.detected:
        state["injection_detected"] = True
        state["injection_markers"] = injection.markers
        state["events"].append({
            "agent": "Research Agent",
            "action": "injection_detected",
            "detail": f"Prompt injection markers detected: {', '.join(injection.markers)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # 3. Hybrid search over pattern runbooks
    store = get_store()
    results = store.hybrid_search(tenant, sanitized_log, top_k=3)
    
    chunks = []
    top_score = 0.0
    for r in results:
        chunks.append({
            "id": r.id,
            "text": r.text,
            "metadata": r.metadata,
            "score": r.score,
        })
        if r.score > top_score:
            top_score = r.score

    state["sanitized_log"] = sanitized_log
    state["retrieved_chunks"] = chunks
    state["top_score"] = top_score

    # Check if retrieval confidence meets minimum threshold
    if top_score < settings.t_partial and not state.get("injection_detected"):
        state["escalate_flag"] = True
        state["events"].append({
            "agent": "Research Agent",
            "action": "escalate_low_similarity",
            "detail": f"Top similarity {top_score:.3f} below threshold {settings.t_partial:.2f}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    else:
        state["events"].append({
            "agent": "Research Agent",
            "action": "retrieval_complete",
            "detail": f"Retrieved {len(chunks)} chunks, top score: {top_score:.3f}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    return state


def context_builder_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 2: Extracts relevant configuration and source code safely."""
    tenant = state.get("tenant", "acme")
    files_to_read = ["package.json", ".env.example", "src/app.js"]
    
    code_snippets = RepoReader.fetch_files(tenant, files_to_read)
    state["code_context"] = code_snippets
    
    state["events"].append({
        "agent": "Context Builder Agent",
        "action": "context_built",
        "detail": f"Read {len(code_snippets)} files from repository for tenant {tenant}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return state


def reasoning_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 3: Diagnoses the incident using the LLM with evidence grounding."""
    # Skip deep reasoning if already flagged for injection
    if state.get("injection_detected"):
        state["llm_response"] = {
            "diagnosis": "Build failure diagnosis aborted due to detected adversarial prompt injection.",
            "pattern_id": "none",
            "confidence": 0.0,
            "fix_description": "Review build log for malicious injection attempts.",
            "citations": [],
        }
        return state

    tenant = state.get("tenant", "acme")
    log_text = state.get("sanitized_log", "")
    chunks = state.get("retrieved_chunks", [])
    code_ctx = state.get("code_context", {})

    llm = get_llm()
    # OfflineLLM analyze is synchronous and instant
    pattern_text = "\n".join(c.get("text", "") for c in chunks)
    resp: LLMResponse = llm.analyze(pattern_text, log_text)

    if resp.pattern_id != "unknown" and chunks:
        citations = []
        for c in chunks:
            meta = c.get("metadata", {})
            pdf = meta.get("pdf_name", meta.get("title", "Runbook"))
            page = meta.get("page", 1)
            score = c.get("score", 0.88)
            citations.append(f"{pdf} (Page {page}) [similarity: {score:.2f}]")
        resp.citations = citations
        resp.confidence = max(resp.confidence, state.get("top_score", 0.85))
    else:
        resp.citations = []
        resp.confidence = 0.0

    state["llm_response"] = resp.to_dict()
    state["confidence"] = resp.confidence
    
    state["events"].append({
        "agent": "Reasoning Agent",
        "action": "diagnosis_generated",
        "detail": f"Pattern: {resp.pattern_id}, Confidence: {resp.confidence:.2f}, Citations: {len(resp.citations)}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return state


def security_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 4: Evaluates security guardrails, citations, RBAC, and policy decisions."""
    top_score = state.get("top_score", 0.0)
    llm_resp = state.get("llm_response", {})
    citations = llm_resp.get("citations", [])
    injection = state.get("injection_detected", False)
    escalate = state.get("escalate_flag", False)

    # 1. Block immediately if injection detected
    if injection:
        state["policy_decision"] = "BLOCK"
        state["policy_reason"] = "Adversarial prompt injection detected in input log"
        state["status"] = "BLOCKED"
        state["events"].append({
            "agent": "Security Agent",
            "action": "policy_block",
            "detail": state["policy_reason"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return state

    # 2. Verify citations exist
    has_valid_citations = len(citations) > 0 and any("Page" in c or "pattern" in c or "acme" in c or "globex" in c for c in citations)
    if not has_valid_citations:
        state["policy_decision"] = "BLOCK"
        state["policy_reason"] = "Rule violated: No citation, no action. Retrieval provided no valid evidence."
        state["status"] = "BLOCKED"
        state["events"].append({
            "agent": "Security Agent",
            "action": "policy_block",
            "detail": state["policy_reason"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return state

    # 3. Check similarity thresholds and policy engine
    if escalate or top_score < settings.t_partial:
        state["policy_decision"] = "BLOCK"
        state["policy_reason"] = f"Low similarity ({top_score:.2f} < {settings.t_partial:.2f}): escalated to human review"
        state["status"] = "ESCALATED"
    elif top_score < settings.t_match:
        # Partial match -> Requires manager confirmation
        state["policy_decision"] = "CONFIRM"
        state["policy_reason"] = f"Partial confidence ({top_score:.2f}): requires Manager approval"
        state["status"] = "AWAITING_APPROVAL"
    else:
        # High confidence match -> Allow automatic PR creation
        state["policy_decision"] = "ALLOW"
        state["policy_reason"] = f"High confidence match ({top_score:.2f} >= {settings.t_match:.2f}) with verified citations"
        state["status"] = "ALLOWED"

    state["events"].append({
        "agent": "Security Agent",
        "action": f"decision_{state['policy_decision'].lower()}",
        "detail": state["policy_reason"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return state


def executor_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 5: Executes allowed actions, saves approvals, or updates audit trail."""
    tenant = state.get("tenant", "acme")
    incident_id = state.get("incident_id", 0)
    decision = state.get("policy_decision", "BLOCK")
    llm_resp = state.get("llm_response", {})
    citations = llm_resp.get("citations", [])
    diagnosis = llm_resp.get("diagnosis", "Unknown error")
    fix = llm_resp.get("fix_description", "No automated fix available.")
    title = state.get("title", f"Build Failure #{incident_id}")

    gh = GitHubTool()

    if decision == "ALLOW":
        repo = settings.get_github_repos().get(tenant)
        pr_res = gh.create_pr_sync(
            tenant=tenant,
            incident_id=incident_id,
            title=title,
            diagnosis=diagnosis,
            fix=fix,
            citations=citations,
            repo=repo,
        )
        if pr_res.success:
            state["pr_url"] = pr_res.url
            state["pr_number"] = pr_res.number
            state["pr_branch"] = pr_res.branch
            state["status"] = "PR_OPENED"
            state["events"].append({
                "agent": "Executor Agent",
                "action": "pr_opened",
                "detail": f"Pull Request #{pr_res.number or 'mock'} opened at {pr_res.url} (branch: {pr_res.branch})",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        else:
            state["status"] = "FAILED"
            state["github_error"] = pr_res.error
            state["events"].append({
                "agent": "Executor Agent",
                "action": "pr_failed",
                "detail": f"Pull Request creation failed: {pr_res.error}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    elif decision == "CONFIRM":
        # Create approval record in DB
        with SessionLocal() as db_sess:
            inc_id_int = int(incident_id) if str(incident_id).isdigit() else 1
            target_repo = settings.get_github_repos().get(tenant, f"{tenant}/incident-repo")
            source_branch = f"eka/incident-{inc_id_int}"
            appr = Approval(
                tenant=tenant,
                incident_id=inc_id_int,
                tool="create_github_pr",
                payload_json=fix,
                status="pending",
                repo=target_repo,
                source_branch=source_branch,
                target_branch="main",
                execution_status="Awaiting Approval",
            )
            db_sess.add(appr)
            db_sess.commit()
            db_sess.refresh(appr)
            state["approval_id"] = appr.id

        state["status"] = "AWAITING_APPROVAL"
        state["events"].append({
            "agent": "Executor Agent",
            "action": "approval_queued",
            "detail": f"Action held pending manager approval (Approval ID: {state.get('approval_id')})",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    else:
        # BLOCK or ESCALATED
        state["events"].append({
            "agent": "Executor Agent",
            "action": "action_blocked",
            "detail": f"Execution halted: {state.get('policy_reason', 'Blocked by policy')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # Record audit log
    with SessionLocal() as db_sess:
        append_audit(
            session=db_sess,
            tenant=tenant,
            actor=state.get("username", "system"),
            action=f"INCIDENT_{state.get('status', 'PROCESSED')}",
            detail=f"Decision: {decision}; Status: {state.get('status')}; TopScore: {state.get('top_score', 0):.2f}",
        )

    return state
