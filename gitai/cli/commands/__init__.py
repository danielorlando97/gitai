"""CLI commands for GitClassifier."""

from .base import BaseCommand
from .split import SplitCommand
from .api_key import APIKeyCommand
from .ollama import OllamaCommand

__all__ = [
    "BaseCommand",
    "SplitCommand",
    "APIKeyCommand",
    "OllamaCommand"
]
