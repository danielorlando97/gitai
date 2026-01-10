"""Factory for prompt generation."""

from typing import Optional
from .templates import PromptTemplates


class PromptFactory:
    """Factory for creating prompts."""

    @staticmethod
    def get_goals_identification_prompt(
        user_context: Optional[str] = None
    ) -> str:
        """Get goals identification prompt."""
        return PromptTemplates.get_goals_identification_prompt(user_context)

    @staticmethod
    def get_hunk_classification_prompt(
        user_context: Optional[str] = None
    ) -> str:
        """Get hunk classification prompt."""
        return PromptTemplates.get_hunk_classification_prompt(user_context)

    @staticmethod
    def get_pr_summary_prompt(
        user_description: Optional[str] = None
    ) -> str:
        """Get PR summary prompt."""
        return PromptTemplates.get_pr_summary_prompt(user_description)
