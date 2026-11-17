"""
llm_smoke.py — LLM smoke test using Groq API.

Requires GROQ_API_KEY in .env or environment.
Sends one test prompt and prints model, latency, and token usage.

Usage:
    python -m scripts.llm_smoke
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure ai-service root is on the path when run directly
_HERE = Path(__file__).resolve().parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from eka.config import get_settings

TEST_PROMPT = (
    "You are an expert DevOps engineer. "
    "A Java service is killed by the OOM killer on a Kubernetes node. "
    "In one sentence, what is the most likely root cause?"
)


def main() -> None:
    settings = get_settings()

    if not settings.GROQ_API_KEY:
        print("[ERROR] GROQ_API_KEY is not set in .env or environment.")
        print("        Set GROQ_API_KEY=<your-key> in ai-service/.env and retry.")
        sys.exit(1)

    try:
        import httpx
    except ImportError:
        print("[ERROR] httpx is not installed. Run: pip install httpx")
        sys.exit(1)

    model = settings.GROQ_MODEL
    print(f"[SMOKE] LLM provider : groq")
    print(f"[SMOKE] Model        : {model}")
    print(f"[SMOKE] Prompt       : {TEST_PROMPT[:80]}...")
    print()

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": TEST_PROMPT}],
        "temperature": 0,
        "max_tokens": 100,
    }

    t0 = time.monotonic()
    try:
        resp = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(f"[ERROR] Groq API returned HTTP {exc.response.status_code}: {exc.response.text[:200]}")
        sys.exit(1)
    except httpx.RequestError as exc:
        print(f"[ERROR] Network error calling Groq: {exc}")
        sys.exit(1)

    latency_ms = (time.monotonic() - t0) * 1000
    data = resp.json()

    answer = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", "?")
    completion_tokens = usage.get("completion_tokens", "?")
    total_tokens = usage.get("total_tokens", "?")

    print(f"[SMOKE] ✓ Response received")
    print(f"        Answer          : {answer}")
    print(f"        Latency         : {latency_ms:.0f} ms")
    print(f"        Prompt tokens   : {prompt_tokens}")
    print(f"        Completion tokens: {completion_tokens}")
    print(f"        Total tokens    : {total_tokens}")
    print(f"        Model (response): {data.get('model', model)}")
    print()
    print("[SMOKE] ✓ Groq LLM smoke test PASSED")


if __name__ == "__main__":
    main()
