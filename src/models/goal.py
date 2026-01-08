"""Goal model for functional objectives."""

from pydantic import BaseModel, Field


class Goal(BaseModel):
    """Model for a functional objective."""

    id: int = Field(description="Unique objective ID")
    description: str = Field(description="Suggested commit message")
