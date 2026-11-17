"""
Ollama Local Model Provider

Integrates with local self-hosted Ollama instances running on the host or in Docker.
Uses Ollama's native `/api/chat` endpoint with structured JSON enforcement,
timeout guards, retry policies, and graceful fallback to the offline rule provider.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional
import httpx

from .base import (
    BaseModelProvider,
    LLMResponse,
    SYSTEM_DIAGNOSIS_PROMPT,
    build_user_prompt,
    parse_structured_json,
    redact_secrets_from_log,
)
from .offline import OfflineModelProvider
from ..config import settings

log = logging.getLogger(__name__)


class OllamaModelProvider(BaseModelProvider):
    """Local Ollama client with JSON enforcement and offline fallback."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        self._base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._model = model or settings.ollama_model
        self._timeout = timeout or settings.llm_timeout
        self._max_retries = max_retries or settings.llm_max_retries
        self._offline = OfflineModelProvider()

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if response_format and response_format.get("type") == "json_object":
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for attempt in range(1, self._max_retries + 1):
                try:
                    resp = await client.post(
                        f"{self._base_url}/api/chat",
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("message", {}).get("content", "")

                except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
                    log.warning(
                        "Ollama connection error on attempt %d/%d (%s): %s",
                        attempt, self._max_retries, self._base_url, redact_secrets_from_log(str(exc)),
                    )
                    if attempt == self._max_retries:
                        log.info("Ollama daemon unavailable. Falling back to offline rule provider.")
                        return await self._offline.generate(system_prompt, user_prompt, temperature, max_tokens, response_format)
                    await asyncio.sleep(1.0 * attempt)

                except Exception as exc:
                    log.error(
                        "Unexpected Ollama error on attempt %d: %s",
                        attempt, redact_secrets_from_log(str(exc)),
                    )
                    return await self._offline.generate(system_prompt, user_prompt, temperature, max_tokens, response_format)

        return await self._offline.generate(system_prompt, user_prompt, temperature, max_tokens, response_format)

    async def diagnose(
        self,
        tenant: str,
        log_text: str,
        retrieved_chunks: List[Dict[str, Any]],
        code_context: Dict[str, str],
    ) -> LLMResponse:
        user_msg = build_user_prompt(retrieved_chunks, log_text, code_context)
        raw_text = await self.generate(
            system_prompt=SYSTEM_DIAGNOSIS_PROMPT,
            user_prompt=user_msg,
            temperature=0.0,
            max_tokens=600,
            response_format={"type": "json_object"},
        )

        try:
            parsed = parse_structured_json(raw_text)
            return LLMResponse(
                diagnosis=str(parsed.get("diagnosis", "")),
                pattern_id=str(parsed.get("pattern_id", "unknown")),
                confidence=float(parsed.get("confidence", 0.0)),
                fix_description=str(parsed.get("fix_description", "")),
                citations=list(parsed.get("citations", [])),
                raw_text=raw_text,
            )
        except Exception as e:
            log.warning("Could not parse JSON from Ollama output: %s. Falling back to offline.", e)
            return await self._offline.diagnose(tenant, log_text, retrieved_chunks, code_context)

    def diagnose_sync(
        self,
        tenant: str,
        log_text: str,
        retrieved_chunks: List[Dict[str, Any]],
        code_context: Dict[str, str],
    ) -> LLMResponse:
        return self._offline.diagnose_sync(tenant, log_text, retrieved_chunks, code_context)

    def analyze(self, pattern_text: str, log_text: str) -> LLMResponse:
        """Synchronous wrapper falls back to offline engine."""
        return self._offline.analyze(pattern_text, log_text)

