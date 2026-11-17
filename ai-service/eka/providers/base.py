"""
EKA Model Provider Abstraction Layer

Defines standardized interfaces and schemas for AI model providers:
- Groq (Cloud API)
- Ollama (Local Self-Hosted API)
- Offline (Deterministic Rule-Based Engine)
"""
from __future__ import annotations

import abc
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Response Schema
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LLMResponse:
    diagnosis: str
    pattern_id: str
    confidence: float
    fix_description: str
    citations: List[str]
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diagnosis": self.diagnosis,
            "pattern_id": self.pattern_id,
            "confidence": self.confidence,
            "fix_description": self.fix_description,
            "citations": self.citations,
            "raw_text": self.raw_text,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Common System Prompts & Utilities
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_DIAGNOSIS_PROMPT = """You are an expert DevOps/SRE incident analyst and cybersecurity engineer.
Given retrieved knowledge-base patterns, code context, and a raw CI/CD build error log snippet, produce a JSON
object (and ONLY the JSON object — no markdown fences, no surrounding prose) with these exact keys:
  diagnosis       (string)  — concise description of the root cause
  pattern_id      (string)  — ID of the matched pattern, or "unknown"
  confidence      (float)   — 0.0 to 1.0 confidence score
  fix_description (string)  — concrete remediation steps or unified git diff
  citations       (array)   — list of pattern IDs or document titles supporting this diagnosis

Respond ONLY with valid JSON. No explanations outside the JSON."""


def build_user_prompt(
    chunks: List[Dict[str, Any]],
    log_text: str,
    code_context: Optional[Dict[str, Any]] = None,
) -> str:
    patterns_section = ""
    for i, chunk in enumerate(chunks, 1):
        patterns_section += (
            f"[Pattern {i} — id={chunk.get('id', '?')}]\n{chunk.get('text', '')}\n\n"
        )

    code_section = ""
    if code_context:
        for path, content in code_context.items():
            code_section += f"[Code file: {path}]\n{content[:2000]}\n\n"

    return (
        f"=== Retrieved Patterns ===\n{patterns_section or '(none)'}\n"
        f"=== Code Context ===\n{code_section or '(none)'}\n"
        f"=== Raw Log ===\n{log_text[:4000]}\n"
    )


def parse_structured_json(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from LLM text safely, stripping any markdown wrappers."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(cleaned)


def redact_secrets_from_log(text: str) -> str:
    """Scrub sensitive credentials from logging output."""
    if not text:
        return ""
    text = re.sub(r"(Bearer\s+)[A-Za-z0-9\-_\.]{10,}", r"\1[REDACTED]", text, flags=re.I)
    text = re.sub(r"(gsk_[A-Za-z0-9]{10,})", r"[REDACTED_GROQ_KEY]", text)
    text = re.sub(r"(ghp_[A-Za-z0-9]{10,})", r"[REDACTED_GH_TOKEN]", text)
    text = re.sub(r"(sk-[A-Za-z0-9]{10,})", r"[REDACTED_API_KEY]", text)
    return text


# ─────────────────────────────────────────────────────────────────────────────
# Base Provider Interface
# ─────────────────────────────────────────────────────────────────────────────

class BaseModelProvider(abc.ABC):
    """
    Abstract interface for all EKA LLM providers.
    Ensures complete decoupling between the multi-agent pipeline and specific model backends.
    """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'groq', 'ollama', 'offline')."""
        ...

    @property
    @abc.abstractmethod
    def model_name(self) -> str:
        """Configured model identifier."""
        ...

    @abc.abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate raw text or structured string output from the model."""
        ...

    @abc.abstractmethod
    async def diagnose(
        self,
        tenant: str,
        log_text: str,
        retrieved_chunks: List[Dict[str, Any]],
        code_context: Dict[str, str],
    ) -> LLMResponse:
        """Execute structured root cause diagnosis with evidence grounding."""
        ...

    @abc.abstractmethod
    def analyze(self, pattern_text: str, log_text: str) -> LLMResponse:
        """Synchronous analysis interface preserved for backward compatibility."""
        ...

    def diagnose_sync(
        self,
        tenant: str,
        log_text: str,
        retrieved_chunks: List[Dict[str, Any]],
        code_context: Dict[str, str],
    ) -> LLMResponse:
        """Synchronous diagnostic execution (rule-based fallback)."""
        return self.analyze("", log_text)

    async def aanalyze(
        self,
        pattern_text: str,
        log_text: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
        code_context: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """Async analysis adapter."""
        return await self.diagnose(
            tenant="default",
            log_text=log_text,
            retrieved_chunks=chunks or [],
            code_context=code_context or {},
        )

