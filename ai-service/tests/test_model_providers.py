"""
Unit tests for EKA AI Model Provider Abstraction Layer (Phase 2)
Tests Groq, Ollama, Offline providers, fallback behavior, and secret redaction.
"""
import json
from eka.providers import (
    BaseModelProvider,
    LLMResponse,
    OfflineModelProvider,
    GroqModelProvider,
    OllamaModelProvider,
    get_model_provider,
)
from eka.providers.base import redact_secrets_from_log, parse_structured_json
from eka.llm import get_llm


def test_base_provider_protocol():
    """Verify that all concrete providers inherit from BaseModelProvider."""
    offline = OfflineModelProvider()
    groq = GroqModelProvider()
    ollama = OllamaModelProvider()

    assert isinstance(offline, BaseModelProvider)
    assert isinstance(groq, BaseModelProvider)
    assert isinstance(ollama, BaseModelProvider)

    assert offline.provider_name == "offline"
    assert groq.provider_name == "groq"
    assert ollama.provider_name == "ollama"


def test_offline_provider_analysis():
    """Verify offline provider rule matching and confidence bounds."""
    provider = OfflineModelProvider()
    
    # 1. OOM failure
    oom_log = "FATAL: java.lang.OutOfMemoryError: Java heap space"
    res = provider.analyze("", oom_log)
    assert isinstance(res, LLMResponse)
    assert res.pattern_id == "oom"
    assert res.confidence >= 0.50
    assert "heap" in res.diagnosis.lower()

    # 2. Port conflict
    port_log = "Error: listen EADDRINUSE: address already in use :::8080"
    res_port = provider.analyze("", port_log)
    assert res_port.pattern_id == "port_conflict"
    assert "port" in res_port.diagnosis.lower()

    # 3. Unknown failure
    unknown_log = "Random non-matching system text"
    res_unk = provider.analyze("", unknown_log)
    assert res_unk.pattern_id == "unknown"
    assert res_unk.confidence == 0.0


def test_offline_provider_diagnose_with_chunks():
    """Verify diagnose_sync() binds citations and sets confidence."""
    provider = OfflineModelProvider()
    chunks = [
        {"id": "pattern_oom", "text": "Runbook OOM fix", "metadata": {"pdf_name": "oom_runbook.pdf", "page": 4}, "score": 0.91}
    ]
    res = provider.diagnose_sync("acme", "java.lang.OutOfMemoryError", chunks, {})
    assert len(res.citations) == 1
    assert "oom_runbook.pdf" in res.citations[0]
    assert "Page 4" in res.citations[0]
    assert res.confidence >= 0.85


def test_groq_fallback_when_unconfigured():
    """Verify Groq provider cleanly falls back to offline when API key is missing."""
    provider = GroqModelProvider(api_key="")
    chunks = [{"id": "oom", "text": "Heap info", "metadata": {"page": 2}, "score": 0.88}]
    res = provider.diagnose_sync("acme", "OutOfMemoryError in build", chunks, {})
    assert isinstance(res, LLMResponse)
    assert res.pattern_id == "oom"


def test_ollama_fallback_when_daemon_unreachable():
    """Verify Ollama provider gracefully falls back to offline when local daemon is not running."""
    # Point to an unreachable port
    provider = OllamaModelProvider(base_url="http://127.0.0.1:54321", timeout=0.5, max_retries=1)
    res = provider.diagnose_sync("acme", "FATAL: java.lang.OutOfMemoryError", [], {})
    assert isinstance(res, LLMResponse)
    assert res.pattern_id == "oom"


def test_secret_redaction_in_provider_logs():
    """Verify API keys and bearer tokens are redacted from logs."""
    dirty_log = "Error sending request with Bearer eyJhbGciOiJIUzI1NiJ9 and key gsk_1234567890abcdef and ghp_token1234567890"
    cleaned = redact_secrets_from_log(dirty_log)
    assert "eyJhbGci" not in cleaned
    assert "gsk_1234567890" not in cleaned
    assert "ghp_token1234567890" not in cleaned
    assert "[REDACTED]" in cleaned


def test_parse_structured_json():
    """Verify JSON extractor handles markdown code blocks and raw JSON."""
    markdown_wrapped = "```json\n{\"diagnosis\": \"Heap leak\", \"confidence\": 0.89}\n```"
    parsed = parse_structured_json(markdown_wrapped)
    assert parsed["diagnosis"] == "Heap leak"
    assert parsed["confidence"] == 0.89

    raw = "{\"diagnosis\": \"Direct test\"}"
    parsed_raw = parse_structured_json(raw)
    assert parsed_raw["diagnosis"] == "Direct test"


def test_factory_and_agent_decoupling():
    """Verify factory returns BaseModelProvider instance without caller coupling."""
    provider_off = get_model_provider("offline")
    assert provider_off.provider_name == "offline"

    provider_ollama = get_model_provider("ollama")
    assert provider_ollama.provider_name == "ollama"

    provider_groq = get_model_provider("groq")
    assert provider_groq.provider_name == "groq"

    # get_llm() returns BaseModelProvider
    llm = get_llm()
    assert isinstance(llm, BaseModelProvider)
