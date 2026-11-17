"""
EKA Model Providers Package

Exports:
- BaseModelProvider (abstract interface)
- LLMResponse (standard response dataclass)
- GroqModelProvider (Groq cloud inference)
- OllamaModelProvider (Local Ollama inference)
- OfflineModelProvider (Deterministic offline rule engine)
- get_model_provider (factory function)
"""
from __future__ import annotations

import logging
from typing import Optional

from .base import BaseModelProvider, LLMResponse
from .groq import GroqModelProvider
from .ollama import OllamaModelProvider
from .offline import OfflineModelProvider
from ..config import settings

log = logging.getLogger(__name__)

__all__ = [
    "BaseModelProvider",
    "LLMResponse",
    "GroqModelProvider",
    "OllamaModelProvider",
    "OfflineModelProvider",
    "get_model_provider",
]

_provider_cache: dict[str, BaseModelProvider] = {}


def get_model_provider(provider_type: Optional[str] = None) -> BaseModelProvider:
    """
    Factory function resolving model provider based on configuration or explicit parameter.
    Resolution logic:
      - 'offline' -> OfflineModelProvider
      - 'ollama'  -> OllamaModelProvider
      - 'groq'    -> GroqModelProvider
      - 'auto'    -> If GROQ_API_KEY present: GroqModelProvider, else: OfflineModelProvider
    """
    ptype = (provider_type or settings.llm_provider).lower()
    if ptype in _provider_cache:
        return _provider_cache[ptype]

    provider: BaseModelProvider

    if ptype == "offline":
        provider = OfflineModelProvider()
        log.info("Initialized AI Model Provider: Offline (Deterministic)")
    elif ptype == "ollama":
        provider = OllamaModelProvider()
        log.info("Initialized AI Model Provider: Ollama (Local at %s, model: %s)", settings.ollama_base_url, settings.ollama_model)
    elif ptype == "groq":
        provider = GroqModelProvider()
        log.info("Initialized AI Model Provider: Groq (Model: %s)", settings.groq_model)
    else:  # auto
        if settings.groq_api_key:
            provider = GroqModelProvider()
            log.info("Auto-selected AI Model Provider: Groq (API key detected)")
        else:
            provider = OfflineModelProvider()
            log.info("Auto-selected AI Model Provider: Offline (No API key present)")

    _provider_cache[ptype] = provider
    return provider

