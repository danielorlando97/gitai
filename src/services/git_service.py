"""Git operations service."""

import subprocess
from typing import Optional, List
from ..utils.git import (
    get_current_branch, get_current_head, create_temp_branch,
    cleanup_temp_branch, is_git_repo, rollback_to_commit
)


class GitService:
    """Service for Git operations."""

    @staticmethod
    def check_repository() -> bool:
        """Check if current directory is a git repository."""
        return is_git_repo()

    @staticmethod
    def get_current_branch() -> Optional[str]:
        """Get current branch name."""
        return get_current_branch()

    @staticmethod
    def get_current_head() -> Optional[str]:
        """Get current HEAD SHA."""
        return get_current_head()

    @staticmethod
    def create_temp_branch() -> Optional[str]:
        """Create temporary branch."""
        return create_temp_branch()

    @staticmethod
    def cleanup_temp_branch(
        branch_name: str,
        original_branch: str
    ) -> bool:
        """Cleanup temporary branch."""
        return cleanup_temp_branch(branch_name, original_branch)

    @staticmethod
    def rollback_to_commit(commit_sha: str) -> bool:
        """Rollback to a specific commit."""
        return rollback_to_commit(commit_sha)

    @staticmethod
    def get_branches() -> List[str]:
        """Get list of all branches."""
        try:
            result = subprocess.check_output(
                ['git', 'branch', '--format=%(refname:short)'],
                stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
            return [b for b in result.split('\n') if b]
        except subprocess.CalledProcessError:
            return []

    @staticmethod
    def checkout_branch(branch_name: str) -> bool:
        """Checkout a branch."""
        try:
            subprocess.run(
                ['git', 'checkout', branch_name],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
