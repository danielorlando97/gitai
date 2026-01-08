#!/usr/bin/env python3
"""
Main entry point for GitClassifier.

This is the new modular entry point using the CLI command pattern.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.cli import create_parser
from src.cli.commands import (
    SplitCommand, APIKeyCommand, OllamaCommand
)


def show_help() -> None:
    """Show help text."""
    help_text = """
GitClassifier - Herramienta inteligente para organizar commits

USO:
    git-split [comando] [opciones]

COMANDOS:
    (sin comando)     Ejecuta el clasificador interactivo
    help              Muestra esta ayuda
    api-key           Gestiona API keys de LLMs
    ollama            Configura y gestiona Ollama

EJEMPLOS:
    git-split                    # Modo interactivo
    git-split help               # Mostrar ayuda
    git-split api-key add gemini "Mi key"
    git-split api-key list
    git-split api-key delete 1
    git-split ollama status
    git-split --target main --use-llm --provider gemini

PROVEEDORES SOPORTADOS:
    ollama    Ollama local (recomendado, por defecto)
    gemini    Google Gemini
    openai    OpenAI

Para más información, visita: https://github.com/tu-repo/git-ai
"""
    print(help_text)


def main() -> int:
    """Main entry point."""
    # Handle help command before parsing
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'help':
        show_help()
        return 0

    # Create commands
    commands = [
        SplitCommand(),
        APIKeyCommand(),
        OllamaCommand()
    ]

    command_names = [cmd.name for cmd in commands]

    # Check if first arg is a command name
    if len(sys.argv) > 1 and sys.argv[1] in command_names:
        # Explicit command specified
        parser = create_parser(commands)
        args = parser.parse_args()
        if hasattr(args, 'command') and args.command:
            for cmd in commands:
                if cmd.name == args.command:
                    return cmd.execute(args)
    else:
        # No command specified, default to split
        # Create parser with only split command for default behavior
        split_cmd = SplitCommand()
        parser = create_parser([split_cmd])
        
        # If args start with --, they're split arguments
        if len(sys.argv) > 1 and sys.argv[1].startswith('-'):
            # Arguments provided, parse as split command
            args = parser.parse_args(['split'] + sys.argv[1:])
        else:
            # No arguments, interactive mode
            args = parser.parse_args(['split'])
        
        return split_cmd.execute(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
