"""
llm.py — multi-provider LLM client.

The orchestrator only needs one operation: send a system prompt and a
user message, get text back. This module abstracts over the provider
choice so the orchestrator doesn't care whether the model is local
Ollama, Groq's free tier, OpenAI, or an OpenAI-compatible endpoint.

Supported providers
-------------------

  ollama      default. http://localhost:11434/api/chat. No API key.
  openai      OpenAI-compatible /v1/chat/completions. Covers:
              - OpenAI  (api.openai.com)
              - Groq    (api.groq.com/openai/v1)
              - Together, OpenRouter, LM Studio, etc.
  gemini      Google's API. NOT YET IMPLEMENTED — TODO.
  anthropic   Anthropic's API. NOT YET IMPLEMENTED — TODO.

Configuration via env vars (read by `__main__.py` and passed here)
----------------------------------------------------------------

  LLM_PROVIDER    "ollama" | "openai"   (default: "ollama")
  LLM_MODEL       model name (default: "gemma4:e4b" for ollama,
                  "llama-3.1-8b-instant" for openai)
  LLM_API_KEY     required for non-ollama providers
  LLM_BASE_URL    override the default base URL (e.g. for Groq)
  LLM_TEMPERATURE default 0.4 — low enough for stable personas
  LLM_MAX_TOKENS  default 1200 — long enough for a stage response

The client is intentionally thin: one class, one method, no streaming
or async. Streaming is a future optimization; for now we want the
orchestrator to be readable and the verdict to be assembled in one
place.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import httpx


# ---------- provider defaults ----------

_PROVIDER_DEFAULTS: dict[str, dict[str, Any]] = {
    "ollama": {
        "base_url": "http://localhost:11434",
        "endpoint": "/api/chat",
        "default_model": "gemma4:e4b",
        "needs_key": False,
    },
    "openai": {
        # Covers OpenAI, Groq, Together, OpenRouter, LM Studio, etc.
        # Override with LLM_BASE_URL for non-OpenAI providers.
        "base_url": "https://api.openai.com",
        "endpoint": "/v1/chat/completions",
        "default_model": "gpt-4o-mini",
        "needs_key": True,
    },
    # TODO: add "gemini" and "anthropic" providers
}


# ---------- the client ----------

@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: str | None
    base_url: str
    temperature: float = 0.4
    max_tokens: int = 1200
    timeout: float = 120.0  # 2 min per call — personas can be slow on small models

    @classmethod
    def from_env(cls) -> "LLMConfig":
        provider = os.environ.get("LLM_PROVIDER", "ollama").strip().lower()
        if provider not in _PROVIDER_DEFAULTS:
            raise ValueError(
                f"Unknown LLM_PROVIDER={provider!r}. "
                f"Supported: {sorted(_PROVIDER_DEFAULTS)}"
            )
        defaults = _PROVIDER_DEFAULTS[provider]
        api_key = os.environ.get("LLM_API_KEY") or None
        if defaults["needs_key"] and not api_key:
            raise ValueError(
                f"LLM_PROVIDER={provider!r} requires LLM_API_KEY in the env."
            )
        base_url = os.environ.get("LLM_BASE_URL", defaults["base_url"]).rstrip("/")
        model = os.environ.get("LLM_MODEL", defaults["default_model"])
        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.4")),
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "1200")),
        )


class LLMClient:
    """Thin synchronous LLM client. One method: `complete`."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig.from_env()

    def complete(self, system: str, user: str) -> str:
        """Send one (system, user) pair to the configured model, return the text."""
        if self.config.provider == "ollama":
            return self._complete_ollama(system, user)
        if self.config.provider == "openai":
            return self._complete_openai(system, user)
        raise ValueError(f"Provider {self.config.provider!r} not implemented")

    # ---------- provider implementations ----------

    def _complete_ollama(self, system: str, user: str) -> str:
        url = f"{self.config.base_url}/api/chat"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }
        with httpx.Client(timeout=self.config.timeout) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
        # Ollama returns: {"message": {"role": "assistant", "content": "..."}}
        return (data.get("message") or {}).get("content", "").strip()

    def _complete_openai(self, system: str, user: str) -> str:
        url = f"{self.config.base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        with httpx.Client(timeout=self.config.timeout) as client:
            r = client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        # OpenAI returns: {"choices": [{"message": {"role": "assistant", "content": "..."}}]}
        choices = data.get("choices") or []
        if not choices:
            return ""
        return (choices[0].get("message") or {}).get("content", "").strip()

    # ---------- introspection ----------

    def describe(self) -> str:
        c = self.config
        return f"{c.provider}:{c.model} (base={c.base_url}, T={c.temperature})"


# ---------- module self-test ----------
# Run with: python -m bot.llm
# (Useful to confirm Ollama is reachable before starting the bot.)

if __name__ == "__main__":
    cfg = LLMConfig.from_env()
    client = LLMClient(cfg)
    print(f"[llm] client: {client.describe()}")
    try:
        reply = client.complete(
            system="You are a concise assistant. Reply in one short sentence.",
            user="Hello. Are you reachable?",
        )
        print(f"[llm] reply: {reply[:200]}")
    except Exception as exc:  # noqa: BLE001
        print(f"[llm] FAILED: {type(exc).__name__}: {exc}")
        raise SystemExit(1)
