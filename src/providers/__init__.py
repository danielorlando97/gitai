"""LLM Providers for GitClassifier."""

from .base import AbstractProvider
from .factory import ProviderFactory
from .ollama import OllamaProvider
from .gemini import GeminiProvider
from .openai import OpenAIProvider

# Register providers
ProviderFactory.register("ollama", OllamaProvider)
ProviderFactory.register("gemini", GeminiProvider)
ProviderFactory.register("openai", OpenAIProvider)

__all__ = [
    "AbstractProvider",
    "ProviderFactory",
    "OllamaProvider",
    "GeminiProvider",
    "OpenAIProvider"
]
