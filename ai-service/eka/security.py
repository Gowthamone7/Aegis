"""
EKA Security Module

sanitize_input(text, max_len)   — strip dangerous control chars, limit length
detect_injection(text)          — detect prompt-injection markers
sanitize_for_output(text)       — redact API keys / tokens in output
verify_citations(resp, chunks)  — verify cited pattern IDs exist in chunks
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ─────────────────────────── types ───────────────────────────────────────────

@dataclass
class InjectionResult:
    detected: bool
    markers: list[str] = field(default_factory=list)


# ─────────────────────────── injection patterns ───────────────────────────────

_INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ignore previous", re.compile(r"ignore\s+previous", re.I)),
    ("disregard", re.compile(r"\bdisregard\b", re.I)),
    ("system:", re.compile(r"\bsystem\s*:", re.I)),
    ("assistant:", re.compile(r"\bassistant\s*:", re.I)),
    ("<|", re.compile(r"<\|", re.I)),
    ("]]>", re.compile(r"\]\]>", re.I)),
    # Repeated override attempts: e.g. "override override override"
    ("repeated override", re.compile(r"\boverride\b.*?\boverride\b", re.I | re.S)),
    # Jailbreak classics
    ("jailbreak", re.compile(r"\bjailbreak\b", re.I)),
    ("new instructions", re.compile(r"new\s+instructions?", re.I)),
    ("ignore all", re.compile(r"ignore\s+all", re.I)),
    ("forget everything", re.compile(r"forget\s+everything", re.I)),
    ("act as", re.compile(r"\bact\s+as\b.{0,30}(admin|root|system|ai|gpt|llm)", re.I)),
    ("prompt injection", re.compile(r"prompt\s+injection", re.I)),
]

# Redaction patterns for secrets in output
_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Bearer token", re.compile(r"Bearer\s+[A-Za-z0-9\-_\.]{20,}", re.I)),
    ("sk- key", re.compile(r"\bsk-[A-Za-z0-9]{20,}")),
    ("ghp_ token", re.compile(r"\bghp_[A-Za-z0-9]{20,}")),
    ("ghs_ token", re.compile(r"\bghs_[A-Za-z0-9]{20,}")),
    ("ghr_ token", re.compile(r"\bghr_[A-Za-z0-9]{20,}")),
    ("API key header", re.compile(r"(?:api[-_]?key|api[-_]?token)\s*[:=]\s*['\"]?[A-Za-z0-9\-_\.]{20,}['\"]?", re.I)),
    ("Authorization header", re.compile(r"Authorization:\s*[^\n]{10,}", re.I)),
]

# Control characters to strip (keep \t, \n, \r)
_CONTROL_CHAR_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)


# ─────────────────────────── public functions ─────────────────────────────────

def sanitize_input(text: str, max_len: int = 8000) -> str:
    """
    Strip null bytes and ASCII control characters (preserving tabs, LF, CR),
    then limit to *max_len* characters.
    """
    if not isinstance(text, str):
        text = str(text)
    # Remove null bytes
    text = text.replace("\x00", "")
    # Remove other control characters (excluding \t \n \r)
    text = _CONTROL_CHAR_RE.sub("", text)
    # Truncate
    if len(text) > max_len:
        text = text[:max_len]
    return text


def detect_injection(text: str) -> InjectionResult:
    """
    Scan *text* for known prompt-injection markers.
    Returns an InjectionResult with detected=True and the matching marker names.
    """
    if not text:
        return InjectionResult(detected=False)

    found: list[str] = []
    for label, pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            found.append(label)

    return InjectionResult(detected=bool(found), markers=found)


def sanitize_for_output(text: str) -> str:
    """
    Redact potential secrets (Bearer tokens, sk- keys, ghp_ tokens, etc.)
    from text before it is returned to the user.
    """
    if not text:
        return text
    for label, pattern in _SECRET_PATTERNS:
        text = pattern.sub(f"[REDACTED:{label}]", text)
    return text


def verify_citations(
    llm_response: "LLMResponse",  # noqa: F821  (avoid circular at module level)
    retrieved_chunks: list[dict],
) -> bool:
    """
    Return True if at least one citation in *llm_response.citations* matches
    the id of a retrieved chunk.

    If there are no citations at all this returns False (no evidence).
    """
    if not llm_response.citations:
        return False

    chunk_ids = {str(chunk.get("id", "")) for chunk in retrieved_chunks}
    # Also accept pattern_id match
    chunk_ids.update(
        str(chunk.get("metadata", {}).get("pattern_id", ""))
        for chunk in retrieved_chunks
    )
    # Remove empty string
    chunk_ids.discard("")

    for citation in llm_response.citations:
        if str(citation) in chunk_ids:
            return True

    return False
