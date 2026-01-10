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

from gitai.cli import create_parser
from gitai.cli.commands import (
    SplitCommand, APIKeyCommand, OllamaCommand
)


def show_help() -> None:
    """Show help text."""
    help_text = """
GitClassifier - Intelligent tool for organizing commits

USAGE:
    git-split [command] [options]

COMMANDS:
    (no command)      Run interactive classifier
    help              Show this help message
    split             Classify and split Git changes into semantic commits
    api-key           Manage LLM API keys
    ollama            Configure and manage Ollama

EXAMPLES:
    git-split                           # Interactive mode
    git-split help                      # Show help
    git-split split --target main --use-llm --provider gemini
    git-split api-key add gemini "My key"
    git-split api-key list
    git-split api-key delete 1
    git-split ollama status
    git-split ollama setup

SPLIT COMMAND FLAGS:
    --diff-file, -f           Path to diff file to analyze
    --target, -t              Target branch to compare (default: main)
    --use-llm, -l             Use automatic classification with LLM
    --provider, -p            LLM provider: ollama, gemini, or openai
    --user-context, -c        User context about changes (file or text)
    --user-description, -d   User description for PR (file or text)
    --mode, -m                Execution mode: normal or step-by-step
    --execute, -e             Execute commits automatically without confirmation
    --edit-plan               Edit the plan before executing
    --generate-pr, -g         Generate Pull Request summary
    --test-cmd                Command to run tests after commits
    --skip-git-check          Skip Git repository verification

API-KEY COMMAND SUBCOMMANDS:
    add <provider> [name]     Add a new API key
                              Provider: gemini, openai, or ollama
                              Name: Optional descriptive name
    list [provider]           List all API keys (optionally filtered by provider)
    delete <key_id>           Delete an API key by ID

OLLAMA COMMAND SUBCOMMANDS:
    setup                     Install and configure Ollama
    status                    Check Ollama service status
    list                      List available models
    pull <model>              Download a model
    info                      Show system information

SUPPORTED PROVIDERS:
    ollama    Ollama local (recommended, default)
    gemini    Google Gemini (fast and economical)
    openai    OpenAI (high quality)

For more information, visit: https://github.com/tu-repo/git-ai
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
