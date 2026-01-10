"""Abstract base class for executors."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class AbstractExecutor(ABC):
    """Abstract base class for plan executors."""

    @abstractmethod
    def execute(
        self,
        plan: Dict[int, Dict],
        rollback_point: Optional[str] = None,
        test_command: Optional[str] = None,
        generate_pr: bool = False,
        llm_client: Optional[Any] = None,
        user_description: Optional[str] = None,
        provider: str = "gemini",
        key_manager: Optional[Any] = None
    ) -> bool:
        """
        Execute the Git plan.

        Args:
            plan: Git plan dictionary
            rollback_point: Git commit SHA for rollback
            test_command: Command to run tests
            generate_pr: Whether to generate PR summary
            llm_client: LLM client for PR generation
            user_description: User description for PR
            provider: LLM provider name
            key_manager: API key manager

        Returns:
            True if execution successful
        """
        pass
