"""Factory for creating LLM providers."""

from typing import Optional, Dict, Any
from .base import AbstractProvider


class ProviderFactory:
    """Factory for creating LLM provider instances."""

    _providers: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, provider_class: type) -> None:
        """
        Register a provider class.

        Args:
            name: Provider name (e.g., 'ollama', 'gemini', 'openai')
            provider_class: Provider class that extends AbstractProvider
        """
        cls._providers[name] = provider_class

    @classmethod
    def create(cls, provider_name: str, model_name: Optional[str] = None,
               key_manager: Optional[Any] = None,
               **kwargs) -> Optional[AbstractProvider]:
        """
        Create a provider instance.

        Args:
            provider_name: Name of the provider
            model_name: Model name to use
            key_manager: API key manager instance
            **kwargs: Additional provider-specific parameters

        Returns:
            Provider instance or None if not found
        """
        if provider_name not in cls._providers:
            return None

        provider_class = cls._providers[provider_name]

        # Get API key from key manager if available
        api_key = None
        key_id = None
        if key_manager:
            key_data = key_manager.get_next_key(provider_name)
            if key_data:
                api_key = key_data['api_key']
                key_id = key_data['id']

        # Fallback to environment variable
        if not api_key:
            env_key = cls._get_env_key(provider_name)
            if env_key:
                api_key = env_key

        return provider_class(
            model_name=model_name,
            api_key=api_key,
            key_id=key_id,
            key_manager=key_manager,
            **kwargs
        )

    @staticmethod
    def _get_env_key(provider_name: str) -> Optional[str]:
        """Get API key from environment variable."""
        import os
        env_map = {
            "gemini": "GOOGLE_API_KEY",
            "openai": "OPENAI_API_KEY",
            "ollama": None  # Ollama doesn't need API key
        }
        env_var = env_map.get(provider_name)
        return os.getenv(env_var) if env_var else None

    @classmethod
    def list_providers(cls) -> list:
        """List all registered providers."""
        return list(cls._providers.keys())
