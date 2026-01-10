"""GitPlan model for commit planning."""

from typing import List
from pydantic import BaseModel, Field
from .goal import Goal


class GitPlan(BaseModel):
    """Model for complete Git plan."""

    goals: List[Goal] = Field(description="List of functional objectives")
