"""Direct OpenAI / Anthropic / OpenRouter chat adapters for IDENT."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from experiments.ident.eval.openrouter import OpenRouterChatModel


def _post_json(
    url: str,
    *,
    headers: dict[str, str],
    body: dict[str, Any],
    timeout_s: float,
    max_retries: int,
    label: str,
) -> dict[str, Any]:
    payload = json.dumps(body).encode("utf-8")
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        request = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            detail = exc.read().decode("utf-8", errors="replace")
            retryable = exc.code in {408, 409, 429, 500, 502, 503, 504}
            if not retryable or attempt >= max_retries:
                raise RuntimeError(f"{label} HTTP {exc.code}: {detail[:800]}") from exc
            time.sleep(min(2**attempt, 16))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt >= max_retries:
                raise RuntimeError(f"{label} request failed: {exc}") from exc
            time.sleep(min(2**attempt, 16))
    raise RuntimeError(f"{label} request failed: {last_error}")


@dataclass
class OpenAIChatModel:
    """OpenAI Chat Completions client (direct API key)."""

    model: str
    api_key: str | None = None
    base_url: str = "https://api.openai.com/v1"
    temperature: float | None = 0.0
    max_tokens: int = 1200
    timeout_s: float = 120.0
    max_retries: int = 4

    def __post_init__(self) -> None:
        key = self.api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is required")
        self.api_key = key
        self.base_url = self.base_url.rstrip("/")

    def complete(self, *, system: str, user: str) -> str:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        # GPT-5.x family prefers max_completion_tokens and may reject temperature.
        if self.model.startswith("gpt-5"):
            body["max_completion_tokens"] = self.max_tokens
        else:
            body["max_tokens"] = self.max_tokens
            if self.temperature is not None:
                body["temperature"] = self.temperature
        data = _post_json(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            body=body,
            timeout_s=self.timeout_s,
            max_retries=self.max_retries,
            label=f"OpenAI:{self.model}",
        )
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError(f"empty choices from OpenAI: {data!r}")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if content is None:
            # Some reasoning models put text only in refusal/other fields.
            raise RuntimeError(f"missing message.content from OpenAI: {data!r}")
        if isinstance(content, list):
            return "".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        return str(content)


@dataclass
class AnthropicChatModel:
    """Anthropic Messages API client (direct API key)."""

    model: str
    api_key: str | None = None
    base_url: str = "https://api.anthropic.com"
    max_tokens: int = 2400
    timeout_s: float = 240.0
    max_retries: int = 4
    # Opus 5 thinking is on by default; keep budget moderate for JSON protocol.
    effort: str | None = "medium"

    def __post_init__(self) -> None:
        key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is required")
        self.api_key = key
        self.base_url = self.base_url.rstrip("/")

    def complete(self, *, system: str, user: str) -> str:
        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        if self.effort is not None:
            body["output_config"] = {"effort": self.effort}
        data = _post_json(
            f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": self.api_key or "",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            body=body,
            timeout_s=self.timeout_s,
            max_retries=self.max_retries,
            label=f"Anthropic:{self.model}",
        )
        blocks = data.get("content") or []
        texts: list[str] = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if block.get("type") in {"text", "output_text"} and block.get("text"):
                texts.append(str(block["text"]))
        if not texts:
            raise RuntimeError(f"no text blocks from Anthropic: {data!r}")
        return "\n".join(texts)


def make_chat_model(spec: str):
    """Build a chat model from a provider-qualified spec.

    Accepted forms:
      openai:gpt-5.6
      anthropic:claude-opus-5
      openrouter:openai/gpt-4o-mini
      openai/gpt-4o-mini   (OpenRouter, backward compatible)
    """
    if ":" in spec and not spec.startswith("http"):
        provider, model = spec.split(":", 1)
        provider = provider.lower()
        if provider == "openai":
            return OpenAIChatModel(model=model)
        if provider == "anthropic":
            return AnthropicChatModel(model=model)
        if provider == "openrouter":
            return OpenRouterChatModel(model=model)
        raise ValueError(f"unknown provider in model spec: {spec}")
    # Bare OpenRouter-style slug.
    return OpenRouterChatModel(model=spec)
