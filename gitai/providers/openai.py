"""OpenAI provider implementation."""

import os
from typing import Optional, Any
from .base import AbstractProvider

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None


class OpenAIProvider(AbstractProvider):
    """OpenAI LLM provider."""

    provider_name = "openai"

    def __init__(self, model_name: Optional[str] = None,
                 api_key: Optional[str] = None, **kwargs):
        """Initialize OpenAI provider."""
        if not HAS_OPENAI:
            raise ImportError(
                "OpenAI requires openai package. "
                "Install with: pip install openai"
            )

        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY not configured. "
                    "Set environment variable or use API key manager."
                )

        if model_name is None:
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        super().__init__(model_name, api_key, **kwargs)
        self._client = None

    def get_client(self) -> Any:
        """Get OpenAI client instance."""
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key)
            # Store key_id for rotation
            if self._key_id:
                self._client._key_id = self._key_id
            if self._key_manager:
                self._client._key_manager = self._key_manager
        return self._client

    def invoke(self, prompt: str, **kwargs) -> str:
        """Invoke OpenAI with a prompt."""
        client = self.get_client()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content

    def supports_structured_output(self) -> bool:
        """Check if OpenAI supports structured output."""
        return True
