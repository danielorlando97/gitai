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

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None


class OllamaProvider(AbstractProvider):
    """Ollama LLM provider."""

    provider_name = "ollama"

    def __init__(self, model_name: Optional[str] = None,
                 api_key: Optional[str] = None, **kwargs):
        """Initialize Ollama provider."""
        if model_name is None:
            model_name = "llama3.2:3b"
        super().__init__(model_name, api_key, **kwargs)
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._client = None

    def get_client(self) -> Any:
        """Get Ollama client instance."""
        if self._client is None:
            # Prioritize LangChain if available
            if HAS_OLLAMA_LANGCHAIN and ChatOllama:
                self._client = ChatOllama(
                    model=self.model_name,
                    base_url=self.base_url,
                    temperature=0
                )
            elif HAS_OPENAI:
                # Fallback to OpenAI-compatible client
                base_url = f"{self.base_url}/v1"
                self._client = OpenAI(base_url=base_url, api_key="ollama")
            else:
                raise ImportError(
                    "Ollama requires langchain-ollama or openai. "
                    "Install with: pip install langchain-ollama"
                )
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
        return HAS_OLLAMA_LANGCHAIN
