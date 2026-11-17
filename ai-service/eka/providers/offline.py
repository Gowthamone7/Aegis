"""
Offline Deterministic Rule-Based Model Provider

Operates with zero external network connectivity. Uses deterministic pattern rules,
AST hints, and exact keyword heuristics to produce reliable diagnostic assessments.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from .base import (
    BaseModelProvider,
    LLMResponse,
    SYSTEM_DIAGNOSIS_PROMPT,
)

log = logging.getLogger(__name__)

# Predefined deterministic failure heuristics
_FAILURE_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "oom",
        "keywords": ["outofmemoryerror", "java heap space", "heap", "gc overhead", "xmx", "xms"],
        "diagnosis": "Out-of-memory error detected: JVM heap space exhausted.",
        "fix": "Increase container JVM allocation via -Xmx flag (e.g., -Xms512m -Xmx2048m -XX:+UseG1GC) and enable HeapDumpOnOutOfMemoryError.",
    },
    {
        "id": "dep_missing",
        "keywords": ["cannot find module", "module not found", "npm err missing", "dependency", "package not found"],
        "diagnosis": "Missing runtime/build dependency detected in manifest.",
        "fix": "Add missing dependency to package.json or requirements.txt and execute lockfile update.",
    },
    {
        "id": "env_missing",
        "keywords": ["environment variable", "env var", "undefined variable", "keyerror", "getenv", "process.env"],
        "diagnosis": "Missing required runtime environment variable detected.",
        "fix": "Configure mandatory environment variables in deploy manifest or vault secret injection.",
    },
    {
        "id": "port_conflict",
        "keywords": ["eaddrinuse", "address already in use", "port", "listen eaddrinuse"],
        "diagnosis": "Socket bind failure: target port already allocated by another process.",
        "fix": "Update application binding port or terminate conflicting listener process.",
    },
    {
        "id": "build_timeout",
        "keywords": ["timeout", "timed out", "build failed", "exceeded time limit", "ci timeout", "execution timed out"],
        "diagnosis": "CI/CD execution pipeline timed out before completion.",
        "fix": "Increase job timeout threshold, parallelize build stages, and enable dependency caching layers.",
    },
]


def _match_pattern(text_lower: str) -> Optional[Dict[str, Any]]:
    best: Optional[Dict[str, Any]] = None
    best_hits = 0
    for pattern in _FAILURE_PATTERNS:
        hits = sum(1 for kw in pattern["keywords"] if kw in text_lower)
        if hits > best_hits:
            best_hits = hits
            best = pattern
    if best_hits == 0:
        return None
    return {**best, "hits": best_hits, "total": len(best["keywords"])}


class OfflineModelProvider(BaseModelProvider):
    """Deterministic rule-based reasoning engine without network access."""

    @property
    def provider_name(self) -> str:
        return "offline"

    @property
    def model_name(self) -> str:
        return "offline-rule-engine-v1"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        resp = self.analyze("", user_prompt)
        return json.dumps(resp.to_dict())

    def analyze(self, pattern_text: str, log_text: str) -> LLMResponse:
        log_lower = log_text.lower()
        match = _match_pattern(log_lower)

        if match:
            confidence = round(match["hits"] / max(match["total"], 1), 2)
            confidence = min(confidence, 0.90)  # Offline ceiling
            citations = [match["id"]]
            return LLMResponse(
                diagnosis=match["diagnosis"],
                pattern_id=match["id"],
                confidence=confidence,
                fix_description=match["fix"],
                citations=citations,
                raw_text=json.dumps({
                    "diagnosis": match["diagnosis"],
                    "pattern_id": match["id"],
                    "confidence": confidence,
                    "fix_description": match["fix"],
                    "citations": citations,
                }),
            )

        # Fallback for unrecognized error
        words = list(dict.fromkeys(re.findall(r"\w+", log_lower)))[:5]
        return LLMResponse(
            diagnosis="Unable to identify a known failure pattern in error log.",
            pattern_id="unknown",
            confidence=0.0,
            fix_description="Escalate to human on-call engineer for investigation.",
            citations=[],
            raw_text=json.dumps({
                "diagnosis": "Unable to identify pattern.",
                "pattern_id": "unknown",
                "confidence": 0.0,
                "fix_description": "Escalate to human engineer.",
                "citations": [],
                "keywords": words,
            }),
        )

    def diagnose_sync(
        self,
        tenant: str,
        log_text: str,
        retrieved_chunks: List[Dict[str, Any]],
        code_context: Dict[str, str],
    ) -> LLMResponse:
        resp = self.analyze("", log_text)
        if resp.pattern_id != "unknown" and retrieved_chunks:
            citations = []
            for c in retrieved_chunks:
                meta = c.get("metadata", {})
                pdf = meta.get("pdf_name", meta.get("title", f"{tenant}-runbook.pdf"))
                page = meta.get("page", 1)
                score = c.get("score", 0.88)
                citations.append(f"{pdf} (Page {page}) [similarity: {score:.2f}]")
            resp.citations = citations
            resp.confidence = max(resp.confidence, 0.88)
        return resp

    async def diagnose(
        self,
        tenant: str,
        log_text: str,
        retrieved_chunks: List[Dict[str, Any]],
        code_context: Dict[str, str],
    ) -> LLMResponse:
        return self.diagnose_sync(tenant, log_text, retrieved_chunks, code_context)

