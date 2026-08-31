# Sourced from MIDAS with permission (see bio-claim-firewall/PROVENANCE.md).
"""Lifted from MIDAS src/models/providers/openai_sdk.py. Adapted:

  - Image handling stripped: `_format_messages`'s content-array/image
    branch is gone — messages pass through unchanged (bio-claim-firewall
    has no vision pipeline; see PHASE_4_PLAN.md "Skip: vision pipeline").
  - `ModelResponse` renamed `ChatResponse`; both it and `ChatRequest` now
    live in `../types.py` instead of `.base`.
  - `ModelProvider` renamed `BaseProvider`.

This module imports `openai`, `httpx`, `tenacity`, `pydantic`, and
`truststore` at the top level, as MIDAS's does — all optional dependencies
of bio-claim-firewall as a whole (see PROVENANCE.md);
`model_manager/providers/__init__.py` catches the ImportError if any of
them are not installed.

No API key is ever hard-coded here: `api_key` is passed in by the caller
(ModelManager._get_provider), which reads it from the env var named in the
provider's config.yaml entry (`api_key_env`) — never from a literal.
"""
from __future__ import annotations

import ssl
import time
from os import getenv
from typing import Any, Dict, List, Optional

import httpx
from openai import OpenAI
from openai import APIError, APITimeoutError, APIConnectionError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception
from pydantic import ValidationError
import truststore

from .base import BaseProvider, ModelError, ModelRetryable, ModelTimeout
from ..types import ChatRequest, ChatResponse


# Define retryable OpenAI exceptions
def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (APITimeoutError, APIConnectionError)):
        return True
    if isinstance(exc, APIError):
        # Retry on 408, 409, 429, 5xx status codes
        if hasattr(exc, 'status_code') and exc.status_code in {408, 409, 429, 500, 502, 503, 504}:
            return True
    if isinstance(exc, ModelRetryable):
        return True
    return False


class OpenAIProvider(BaseProvider):
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, default_headers: Optional[Dict[str, str]] = None, timeout: float = 60.0, **kwargs):
        http_client = kwargs.pop("http_client", None)
        if http_client is None:
            # Use the operating system trust store rather than certifi. This keeps
            # TLS verification enabled while supporting networks that install a
            # trusted local root certificate for HTTPS inspection.
            ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            http_client = httpx.Client(verify=ssl_context, timeout=timeout)

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key or getenv("OPENAI_API_KEY"),
            default_headers=default_headers or {},
            timeout=timeout,
            http_client=http_client,
            **kwargs
        )
        self.base_url = base_url
        self.timeout = timeout

    @retry(reraise=True, wait=wait_exponential_jitter(initial=0.5, max=4), stop=stop_after_attempt(3), retry=retry_if_exception(_is_retryable))
    def chat(self, req: ChatRequest) -> ChatResponse:
        # Prepare the request parameters
        params = dict(req.params or {})

        # Handle JSON mode and schema
        response_format = None
        if req.schema is not None:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response_schema",
                    "strict": True,
                    "schema": req.schema.model_json_schema()
                }
            }

        messages = req.messages

        # Prepare the completion request
        completion_params = {
            "model": req.model,
            "messages": messages,
            **params
        }

        if response_format:
            completion_params["response_format"] = response_format

        t0 = time.perf_counter()
        try:
            # extra_body must be passed as a kwarg to the SDK — not merged into
            # completion_params — so the SDK can forward it in the HTTP body
            # without triggering its own parameter validation (e.g. reasoning_format).
            response = self.client.chat.completions.create(
                **completion_params,
                **({"extra_body": req.extra_body} if req.extra_body else {}),
            )
        except APITimeoutError as e:
            raise ModelTimeout(f"OpenAI timeout: {e}") from e
        except APIError as e:
            msg = f"OpenAI API error: {e}"
            if _is_retryable(e):
                raise ModelRetryable(msg) from e
            raise ModelError(msg) from e
        except Exception as e:
            raise ModelError(f"OpenAI provider error: {e}") from e

        dt = time.perf_counter() - t0

        # Extract content from response with robust error handling
        try:
            content = response.choices[0].message.content or ""
        except (IndexError, AttributeError) as e:
            raise ModelError(f"Invalid response structure from OpenAI API: {e}") from e

        # Build metadata with improved error handling
        meta = {
            "provider": "openai",
            "model": getattr(response, 'model', req.model),
            "latency": dt,
            "base_url": self.base_url or "https://api.openai.com/v1",
            "timeout": self.timeout
        }

        # Safely add usage information
        if hasattr(response, 'usage') and response.usage:
            try:
                meta["usage"] = response.usage.model_dump()
            except AttributeError:
                # Fallback for older openai library versions
                meta["usage"] = {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', None),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', None),
                    "total_tokens": getattr(response.usage, 'total_tokens', None)
                }

        # Safely add response metadata
        if hasattr(response, 'choices') and response.choices:
            meta["finish_reason"] = getattr(response.choices[0], 'finish_reason', None)

        if hasattr(response, 'created'):
            meta["created"] = response.created

        if hasattr(response, 'id'):
            meta["id"] = response.id

        # Parse structured response if schema was provided
        parsed = None
        if req.schema is not None and content:
            try:
                parsed = req.schema.model_validate_json(content)
            except ValidationError as ve:
                # Log validation error but don't fail the request
                meta["validation_error"] = str(ve)

        return ChatResponse(content=content, raw=response, meta=meta, parsed=parsed)

    def health_check(self) -> bool:
        """SYNCHRONOUS health check - blocks until complete"""
        try:
            # Try to list models as a simple health check
            _ = self.client.models.list()
            return True
        except Exception:
            return False
