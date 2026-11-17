"""
EKA LLM Module (Backward Compatibility & Provider Re-exports)

Provides unified access to:
- BaseModelProvider (abstract interface)
- LLMResponse (response schema)
- OfflineLLM / OfflineModelProvider
- GroqLLM / GroqModelProvider
- OllamaLLM / OllamaModelProvider
- get_llm() -> BaseModelProvider
"""
from __future__ import annotations

import logging
from typing import Optional

from .providers import (
    BaseModelProvider,
    LLMResponse,
    OfflineModelProvider,
    GroqModelProvider,
    OllamaModelProvider,
    get_model_provider,
)

log = logging.getLogger(__name__)

# Aliases for 100% backward compatibility
OfflineLLM = OfflineModelProvider
GroqLLM = GroqModelProvider
OllamaLLM = OllamaModelProvider


def get_llm(provider_type: Optional[str] = None) -> BaseModelProvider:
    """
    Returns the configured AI Model Provider instance.
    Decouples callers from specific LLM vendors.
    """
    return get_model_provider(provider_type)


__all__ = [
    "BaseModelProvider",
    "LLMResponse",
    "OfflineLLM",
    "GroqLLM",
    "OllamaLLM",
    "OfflineModelProvider",
    "GroqModelProvider",
    "OllamaModelProvider",
    "get_llm",
    "get_model_provider",
]
