"""Gemini provider implementation."""

import os
from typing import Optional, Any
from .base import AbstractProvider

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    ChatGoogleGenerativeAI = None


class GeminiProvider(AbstractProvider):
    """Google Gemini LLM provider."""

    provider_name = "gemini"

    def __init__(self, model_name: Optional[str] = None,
                 api_key: Optional[str] = None, **kwargs):
        """Initialize Gemini provider."""
        if not HAS_LANGCHAIN:
            raise ImportError(
                "Gemini requires langchain-google-genai. "
                "Install with: pip install langchain-google-genai"
            )

        if model_name is None:
            model_name = os.getenv("GEMINI_MODEL")
            if not model_name:
                model_name = "models/gemini-2.5-flash-lite"

        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError(
                    "GOOGLE_API_KEY not configured. "
                    "Set environment variable or use API key manager."
                )

        super().__init__(model_name, api_key, **kwargs)
        self._client = None

    def get_client(self) -> Any:
        """Get Gemini client instance."""
        if self._client is None:
            self._client = ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=0,
                google_api_key=self.api_key
            )
            # Store key_id for rotation
            if self._key_id:
                self._client._key_id = self._key_id
            if self._key_manager:
                self._client._key_manager = self._key_manager
        return self._client

    def invoke(self, prompt: str, **kwargs) -> str:
        """Invoke Gemini with a prompt."""
        client = self.get_client()
        response = client.invoke(prompt)
        if hasattr(response, 'content'):
            return response.content
        return str(response)

    def supports_structured_output(self) -> bool:
        """Check if Gemini supports structured output."""
        return True
