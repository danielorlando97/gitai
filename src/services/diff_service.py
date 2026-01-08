"""Diff operations service."""

from typing import List, Optional
from ..utils.diff import (
    read_diff_from_file, get_git_diff, parse_hunks,
    create_summary_for_llm
)
from ..models.hunk import Hunk


class DiffService:
    """Service for diff operations."""

    @staticmethod
    def read_from_file(file_path: str) -> Optional[str]:
        """Read diff from file."""
        return read_diff_from_file(file_path)

    @staticmethod
    def get_git_diff(
        target_branch: str,
        use_working_dir: bool = False
    ) -> Optional[str]:
        """Get diff from git."""
        return get_git_diff(target_branch, use_working_dir)

    @staticmethod
    def parse_hunks(diff_text: str) -> List[Hunk]:
        """Parse diff text into hunks."""
        hunks_dict = parse_hunks(diff_text)
        return [
            Hunk(file=h['file'], content=h['content'])
            for h in hunks_dict
        ]

    @staticmethod
    def create_summary(
        hunks: List[Hunk],
        max_chars: int = 8000
    ) -> str:
        """Create summary of hunks for LLM."""
        hunks_dict = [
            h.to_dict() if hasattr(h, 'to_dict') else {
                'file': h.file,
                'content': h.content
            }
            for h in hunks
        ]
        return create_summary_for_llm(hunks_dict, max_chars)
