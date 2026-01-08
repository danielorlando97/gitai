"""CLI module for GitClassifier."""

from .parser import create_parser
from .commands.base import BaseCommand

__all__ = ["create_parser", "BaseCommand"]
