"""Base command class for CLI commands."""

from abc import ABC, abstractmethod
from typing import List, Optional
import argparse


class BaseCommand(ABC):
    """Abstract base class for CLI commands."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        pass

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the command.

        Args:
            args: Parsed arguments

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        pass

    def help(self) -> str:
        """Get help text for the command."""
        return self.description
