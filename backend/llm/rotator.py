"""Chat generation clients for market agent messages."""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Sequence
from typing import Any


class AgentChatRotator:
    """Generate short market chat text across supported LLM providers."""

    def __init__(
        self,
        api_keys: Sequence[str] | None = None,
        model_name: str = "gemini-1.5-flash",
        request_timeout: float = 8.0,
        provider: str = "gemini",
        base_url: str | None = None,
    ) -> None:
        self.provider = provider
        self.api_keys = [api_key for api_key in (api_keys or []) if api_key]
        self.model_name = model_name
        self.request_timeout = request_timeout
        self.base_url = (base_url or "").rstrip("/")
        self.last_error: str | None = None
        self._cursor = 0

        if self.provider in {"gemini", "openrouter"} and not self.api_keys:
            raise ValueError(f"{self.provider} requires at least one API key")
        if self.provider == "ollama" and not self.base_url:
            raise ValueError("ollama requires a base URL")

    def generate_chat(self, context: str | None = None) -> str:
        prompt = self._build_prompt(context)
        self.last_error = None
        try:
            if self.provider == "gemini":
                return self._generate_gemini(prompt)
            if self.provider == "openrouter":
                return self._generate_openrouter(prompt)
            if self.provider == "ollama":
                return self._generate_ollama(prompt)
            raise RuntimeError(f"unsupported chat provider: {self.provider}")
        except Exception as exc:
            self.last_error = str(exc)
            raise

    def _generate_gemini(self, prompt: str) -> str:
        last_error: Exception | None = None
        for _ in range(len(self.api_keys)):
            api_key = self._next_api_key()
            try:
                genai = self._load_genai()
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content(
                    prompt,
                    request_options={"timeout": self.request_timeout},
                )
                text = getattr(response, "text", "")
                if text:
                    return text.strip()
            except Exception as exc:
                last_error = exc
                if not self._is_retryable(exc):
                    raise
        raise RuntimeError("all Gemini API keys failed") from last_error

    def _generate_openrouter(self, prompt: str) -> str:
        payload = json.dumps(
            {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode()
        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self._next_api_key()}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.request_timeout) as response:
            data = json.loads(response.read().decode())
        return data["choices"][0]["message"]["content"].strip()

    def _generate_ollama(self, prompt: str) -> str:
        payload = json.dumps(
            {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
            }
        ).encode()
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.request_timeout) as response:
            data = json.loads(response.read().decode())
        return data["response"].strip()

    def _next_api_key(self) -> str:
        api_key = self.api_keys[self._cursor]
        self._cursor = (self._cursor + 1) % len(self.api_keys)
        return api_key

    @staticmethod
    def _build_prompt(context: str | None) -> str:
        base_prompt = (
            "Generate one short Indonesian retail stock trader chat message. "
            "Use casual slang like to the moon, serok, cutloss, or nyangkut. "
            "Return only the chat text, max 12 words."
        )
        if not context:
            return base_prompt
        return f"{base_prompt}\nMarket context: {context}"

    @staticmethod
    def _load_genai() -> Any:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError(
                "google-generativeai is required for AgentChatRotator"
            ) from exc
        return genai

    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        text = str(error).lower()
        retryable_markers = (
            "429",
            "quota",
            "rate limit",
            "resource exhausted",
            "temporarily unavailable",
            "deadline",
            "timeout",
        )
        return any(marker in text for marker in retryable_markers)
