"""Ollama provider implementation."""

import os
from typing import Optional, Any
from .base import AbstractProvider

try:
    from langchain_ollama import ChatOllama
    HAS_OLLAMA_LANGCHAIN = True
except ImportError:
    HAS_OLLAMA_LANGCHAIN = False
    ChatOllama = None


class OllamaProvider(AbstractProvider):
    """Ollama LLM provider."""

    provider_name = "ollama"

    def __init__(self, model_name: Optional[str] = None,
                 api_key: Optional[str] = None, **kwargs):
        """Initialize Ollama provider."""
        if not HAS_OLLAMA_LANGCHAIN:
            raise ImportError(
                "Ollama requires langchain-ollama. "
                "Install with: pip install langchain-ollama"
            )
        if model_name is None:
            model_name = "llama3.2:3b"
        super().__init__(model_name, api_key, **kwargs)
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._client = None

    def get_client(self) -> Any:
        """Get Ollama client instance."""
        if self._client is None:
            self._client = ChatOllama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=0
            )
            # Store key_id for rotation
            if self._key_id:
                self._client._key_id = self._key_id
            if self._key_manager:
                self._client._key_manager = self._key_manager
        return self._client

    def invoke(self, prompt: str, **kwargs) -> str:
        """Invoke Ollama with a prompt."""
        client = self.get_client()
        response = client.invoke(prompt)
        if hasattr(response, 'content'):
            return response.content
        return str(response)

    def supports_structured_output(self) -> bool:
        """Check if Ollama supports structured output."""
        return True
