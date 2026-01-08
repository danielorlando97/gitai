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
        description='GitClassifier: Clasifica y divide cambios de Git en commits semánticos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Usar diff desde archivo con LLM
  git-split --diff-file diff.patch --use-llm --provider gemini

  # Usar git diff con configuración completa
  git-split --target main --use-llm --provider gemini --mode step-by-step --generate-pr

  # Modo no interactivo completo
  git-split --diff-file diff.patch --use-llm --provider gemini \\
    --mode normal --generate-pr --test-cmd "pytest" --execute
        """
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help='Comandos disponibles',
        metavar='COMANDO'
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
