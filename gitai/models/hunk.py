"""Hunk model for code changes."""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class Hunk(BaseModel):
    """Model for a code change hunk."""

    file: str = Field(description="File path")
    content: str = Field(description="Hunk content (diff format)")
    line_start: Optional[int] = Field(None, description="Start line number")
    line_end: Optional[int] = Field(None, description="End line number")

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {
            "file": self.file,
            "content": self.content
        }
