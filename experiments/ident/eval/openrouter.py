"""OpenRouter chat adapter for IDENT (stdlib HTTP only)."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODELS = (
    "openai/gpt-4o-mini",
    "anthropic/claude-sonnet-4",
    "google/gemini-2.5-flash",
)


@dataclass
class OpenRouterChatModel:
    """Minimal OpenAI-compatible chat client via OpenRouter."""

    model: str
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.0
    max_tokens: int = 500
    timeout_s: float = 60.0
    max_retries: int = 4
    referer: str = "https://github.com/jawaunbrown/research-derived-experiments"
    title: str = "IDENT benchmark"

    def __post_init__(self) -> None:
        key = self.api_key or os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is required (e.g. doppler run --project cofounder --config dev)"
            )
        self.api_key = key
        self.base_url = (
            self.base_url
            or os.environ.get("OPENROUTER_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/")

    def complete(self, *, system: str, user: str) -> str:
        url = f"{self.base_url}/chat/completions"
        body: dict[str, Any] = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        payload = json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.referer,
            "X-Title": self.title,
        }
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            request = urllib.request.Request(
                url, data=payload, headers=headers, method="POST"
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                    raw = response.read().decode("utf-8")
                data = json.loads(raw)
                choices = data.get("choices") or []
                if not choices:
                    raise RuntimeError(f"empty choices from OpenRouter: {data!r}")
                message = choices[0].get("message") or {}
                content = message.get("content")
                if content is None:
                    raise RuntimeError(f"missing message.content: {data!r}")
                if isinstance(content, list):
                    # Some models return content parts.
                    texts = [
                        part.get("text", "")
                        for part in content
                        if isinstance(part, dict)
                    ]
                    return "".join(texts)
                return str(content)
            except urllib.error.HTTPError as exc:
                last_error = exc
                detail = exc.read().decode("utf-8", errors="replace")
                retryable = exc.code in {408, 409, 429, 500, 502, 503, 504}
                if not retryable or attempt >= self.max_retries:
                    raise RuntimeError(
                        f"OpenRouter HTTP {exc.code} for {self.model}: {detail[:500]}"
                    ) from exc
                time.sleep(min(2**attempt, 16))
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise RuntimeError(
                        f"OpenRouter request failed for {self.model}: {exc}"
                    ) from exc
                time.sleep(min(2**attempt, 16))
        raise RuntimeError(f"OpenRouter request failed for {self.model}: {last_error}")
