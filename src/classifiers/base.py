"""Abstract base class for classifiers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from ..models.hunk import Hunk
from ..models.goal import Goal


class AbstractClassifier(ABC):
    """Abstract base class for change classifiers."""

    @abstractmethod
    def identify_goals(
        self,
        hunks: List[Hunk],
        user_context: Optional[str] = None
    ) -> List[Goal]:
        """
        Identify functional goals from hunks.

        Args:
            hunks: List of code change hunks
            user_context: Optional user context about changes

        Returns:
            List of identified goals
        """
        pass

    @abstractmethod
    def classify_hunks(
        self,
        hunks: List[Hunk],
        goals: List[Goal],
        user_context: Optional[str] = None
    ) -> Dict[int, Dict]:
        """
        Classify hunks into goals.

        Args:
            hunks: List of code change hunks
            goals: List of goals to classify into
            user_context: Optional user context

        Returns:
            Dictionary mapping goal_id to hunks
        """
        pass
