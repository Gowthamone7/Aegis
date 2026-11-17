"""
Groq Cloud Model Provider

Integrates with Groq's high-speed inference API using standard OpenAI chat format.
Includes automated retries on HTTP 429, timeout handling, secret-safe logging,
and fallback to the offline rule provider.
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


class GroqModelProvider(BaseModelProvider):
    """Async Groq API provider with exponential backoff and offline fallback."""

    _BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.groq_api_key
        self._model = model or settings.groq_model
        self._timeout = timeout or settings.llm_timeout
        self._max_retries = max_retries or settings.llm_max_retries
        self._offline = OfflineModelProvider()

    @property
    def provider_name(self) -> str:
        return "groq"

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
        if not self._api_key:
            log.warning("GROQ_API_KEY missing — routing through offline fallback.")
            return await self._offline.generate(system_prompt, user_prompt, temperature, max_tokens, response_format)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }
        payload: Dict[str, Any] = {
            "model": self._model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for attempt in range(1, self._max_retries + 1):
                try:
                    resp = await client.post(
                        f"{self._BASE_URL}/chat/completions",
                        json=payload,
                        headers=headers,
                    )

                    # Rate limiting check
                    if resp.status_code == 429:
                        wait = min(float(resp.headers.get("Retry-After", 5.0)), 30.0)
                        log.warning(
                            "Groq rate limit (429) on attempt %d/%d. Waiting %.1fs.",
                            attempt, self._max_retries, wait,
                        )
                        if attempt < self._max_retries:
                            await asyncio.sleep(wait)
                            continue
                        log.error("Groq rate limit exceeded max retries. Falling back to offline provider.")
                        return await self._offline.generate(system_prompt, user_prompt, temperature, max_tokens, response_format)

                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]

                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    log.warning(
                        "Groq network error on attempt %d/%d: %s",
                        attempt, self._max_retries, redact_secrets_from_log(str(exc)),
                    )
                    if attempt == self._max_retries:
                        log.error("Groq unreachable. Falling back to offline provider.")
                        return await self._offline.generate(system_prompt, user_prompt, temperature, max_tokens, response_format)
                    await asyncio.sleep(2 ** attempt)

                except Exception as exc:
                    log.error(
                        "Unexpected Groq client error: %s",
                        redact_secrets_from_log(str(exc)),
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
            log.warning("Could not parse JSON from Groq output: %s. Falling back to offline.", e)
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

