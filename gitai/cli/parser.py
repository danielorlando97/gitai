"""CLI argument parser for GitClassifier."""

import argparse
from typing import List, Optional
from .commands.base import BaseCommand


def create_parser(commands: Optional[List[BaseCommand]] = None) -> argparse.ArgumentParser:
    """
    Create argument parser with subcommands.

    Args:
        commands: List of command instances to register

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='GitClassifier: Classify and split Git changes into semantic commits',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use diff from file with LLM
  git-split --diff-file diff.patch --use-llm --provider gemini

  # Use git diff with full configuration
  git-split --target main --use-llm --provider gemini --mode step-by-step --generate-pr

  # Full non-interactive mode
  git-split --diff-file diff.patch --use-llm --provider gemini \\
    --mode normal --generate-pr --test-cmd "pytest" --execute

  # Manage API keys
  git-split api-key add gemini "My key"
  git-split api-key list
  git-split api-key delete 1

  # Manage Ollama
  git-split ollama status
  git-split ollama pull llama3.2:3b
        """
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        metavar='COMMAND'
    )

    if commands:
        for cmd in commands:
            cmd_parser = subparsers.add_parser(
                cmd.name,
                help=cmd.description,
                description=cmd.help()
            )
            cmd.add_arguments(cmd_parser)

    return parser
