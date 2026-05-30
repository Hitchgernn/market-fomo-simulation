"""Round-robin Gemini API key rotator for agent chat generation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


class AgentChatRotator:
    """Generate short market chat text while rotating across Gemini API keys."""

    def __init__(
        self,
        api_keys: Sequence[str],
        model_name: str = "gemini-1.5-flash",
        request_timeout: float = 8.0,
    ) -> None:
        self.api_keys = [api_key for api_key in api_keys if api_key]
        if not self.api_keys:
            raise ValueError("at least one Gemini API key is required")

        self.model_name = model_name
        self.request_timeout = request_timeout
        self._cursor = 0

    def generate_chat(self, context: str | None = None) -> str:
        """Generate slang-style retail investor chat with API-key failover."""
        prompt = self._build_prompt(context)
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
