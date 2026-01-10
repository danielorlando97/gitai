"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class AbstractProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model_name: Optional[str] = None,
                 api_key: Optional[str] = None,
                 **kwargs):
        """
        Initialize provider.

        Args:
            model_name: Model name to use
            api_key: API key for authentication
            **kwargs: Additional provider-specific parameters
        """
        self.model_name = model_name
        self.api_key = api_key
        self._key_id = kwargs.get("key_id")
        self._key_manager = kwargs.get("key_manager")

    @abstractmethod
    def get_client(self) -> Any:
        """
        Get the LLM client instance.

        Returns:
            LLM client instance
        """
        pass

    @abstractmethod
    def invoke(self, prompt: str, **kwargs) -> str:
        """
        Invoke the LLM with a prompt.

        Args:
            prompt: Prompt text
            **kwargs: Additional parameters

        Returns:
            LLM response text
        """
        pass

    @abstractmethod
    def supports_structured_output(self) -> bool:
        """
        Check if provider supports structured output (Pydantic).

        Returns:
            True if supports structured output
        """
        pass

    def rotate_key(self) -> bool:
        """
        Rotate to next available API key.

        Returns:
            True if rotation successful
        """
        if not self._key_manager or not hasattr(self, "provider_name"):
            return False

        key_data = self._key_manager.get_next_key(self.provider_name)
        if key_data:
            self.api_key = key_data['api_key']
            self._key_id = key_data['id']
            return True
        return False

    def record_error(self, error_type: str, error_message: str) -> None:
        """Record an error for the current API key."""
        if self._key_id and self._key_manager:
            self._key_manager.record_error(
                self._key_id, error_type, error_message
            )
