#!/bin/bash

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat << 'HELP'
gitai - Git AI Assistant

DESCRIPTION:
    AI-powered tools for git workflows including commit generation and PR
    creation.

USAGE:
    gitai generate <command> [options]

COMMANDS:
    generate commit    Generate gitai.sh with atomic commits
    generate pr        Generate gitai.sh with PR creation command
    update             Update current branch with commits (or create PR if --base is specified)

OPTIONS:
    --help, -h         Show this help message
    --base, -b <branch> Base branch for PR (for generate pr and update)

EXAMPLES:
    gitai generate commit              Generate gitai.sh with atomic commits
    gitai generate pr                   Generate gitai.sh with PR creation command
    gitai generate pr --base main      Generate gitai.sh with PR targeting main branch
    gitai update                        Update current branch with commits
    gitai update --base main            Update branch and create PR targeting main
    gitai --help                       Show this help message

For more information, visit the project repository.
HELP
    exit 0
fi

# Check for generate commit command
if [ "$1" = "generate" ] && [ "$2" = "commit" ]; then
    # Get the prompt file location
    PROMPT_FILE="$HOME/.local/share/gitai/prompt.md"

    # Check if prompt file exists
    if [ ! -f "$PROMPT_FILE" ]; then
        echo "Error: prompt.md not found at $PROMPT_FILE"
        exit 1
    fi

    # Check if cursor is installed
    if ! command -v cursor &> /dev/null; then
        echo "Error: cursor command not found. Please install Cursor AI."
        exit 1
    fi

    # Run cursor agent with the prompt
    cursor agent --stream-partial-output --output-format stream-json -p "$(cat "$PROMPT_FILE")"
    exit 0
fi

# Check for generate pr command
if [ "$1" = "generate" ] && [ "$2" = "pr" ]; then
    # Get the prompt file location
    PR_PROMPT_FILE="$HOME/.local/share/gitai/pr-prompt.md"

    # Check if prompt file exists
    if [ ! -f "$PR_PROMPT_FILE" ]; then
        echo "Error: pr-prompt.md not found at $PR_PROMPT_FILE"
        exit 1
    fi

    # Check if cursor is installed
    if ! command -v cursor &> /dev/null; then
        echo "Error: cursor command not found. Please install Cursor AI."
        exit 1
    fi

    # Parse arguments for --base flag
    BASE_BRANCH=""
    shift 2
    while [[ $# -gt 0 ]]; do
        case $1 in
            --base|-b)
                if [ -z "$2" ]; then
                    echo "Error: --base requires a branch name"
                    exit 1
                fi
                BASE_BRANCH="$2"
                shift 2
                ;;
            *)
                echo "Error: Unknown option $1"
                echo "Usage: gitai generate pr [--base <branch>]"
                exit 1
                ;;
        esac
    done

    # Build the prompt with base branch if provided
    PROMPT_CONTENT="$(cat "$PR_PROMPT_FILE")"
    
    if [ -n "$BASE_BRANCH" ]; then
        PROMPT_CONTENT="$PROMPT_CONTENT

**IMPORTANT:** The base branch for this PR is: $BASE_BRANCH
Include the flag \`--base $BASE_BRANCH\` in the \`gh pr create\` command."
    fi

    # Run cursor agent with the prompt
    cursor agent --stream-partial-output --output-format stream-json -p "$PROMPT_CONTENT"
    exit 0
fi

# Check for update command
if [ "$1" = "update" ]; then
    # Parse arguments for --base flag
    BASE_BRANCH=""
    shift
    while [[ $# -gt 0 ]]; do
        case $1 in
            --base|-b)
                if [ -z "$2" ]; then
                    echo "Error: --base requires a branch name"
                    exit 1
                fi
                BASE_BRANCH="$2"
                shift 2
                ;;
            *)
                echo "Error: Unknown option $1"
                echo "Usage: gitai update [--base <branch>]"
                exit 1
                ;;
        esac
    done

    # Check if cursor is installed
    if ! command -v cursor &> /dev/null; then
        echo "Error: cursor command not found. Please install Cursor AI."
        exit 1
    fi

    # Step 1: Generate commit script
    if [ -n "$BASE_BRANCH" ]; then
        echo "Step 1/4: Generating commit script..."
    else
        echo "Step 1/3: Generating commit script..."
    fi
    
    PROMPT_FILE="$HOME/.local/share/gitai/prompt.md"
    if [ ! -f "$PROMPT_FILE" ]; then
        echo "Error: prompt.md not found at $PROMPT_FILE"
        exit 1
    fi
    
    cursor agent --stream-partial-output --output-format stream-json -p "$(cat "$PROMPT_FILE")"
    
    if [ ! -f "gitai.sh" ]; then
        echo "Error: gitai.sh was not generated"
        exit 1
    fi

    # Step 2: Execute commit script
    echo ""
    if [ -n "$BASE_BRANCH" ]; then
        echo "Step 2/4: Executing commits..."
    else
        echo "Step 2/3: Executing commits..."
    fi
    
    chmod +x gitai.sh
    sh gitai.sh
    COMMIT_EXIT_CODE=$?
    
    if [ $COMMIT_EXIT_CODE -ne 0 ]; then
        echo "Error: Commit script failed with exit code $COMMIT_EXIT_CODE"
        rm -f gitai.sh
        exit $COMMIT_EXIT_CODE
    fi

    # If no base branch specified, only update current branch (no PR)
    if [ -z "$BASE_BRANCH" ]; then
        # Step 3: Cleanup
        echo ""
        echo "Step 3/3: Cleaning up..."
        git push origin $(git branch --show-current)
        rm -f gitai.sh
        
        echo ""
        echo "✓ Update workflow completed successfully!"
        echo "Current branch has been updated with atomic commits."
        exit 0
    fi

    # Step 3: Generate PR script (only if base branch is specified)
    echo ""
    echo "Step 3/4: Generating PR script..."
    PR_PROMPT_FILE="$HOME/.local/share/gitai/pr-prompt.md"
    if [ ! -f "$PR_PROMPT_FILE" ]; then
        echo "Error: pr-prompt.md not found at $PR_PROMPT_FILE"
        rm -f gitai.sh
        exit 1
    fi

    PROMPT_CONTENT="$(cat "$PR_PROMPT_FILE")"
    PROMPT_CONTENT="$PROMPT_CONTENT

**IMPORTANT:** The base branch for this PR is: $BASE_BRANCH
Include the flag \`--base $BASE_BRANCH\` in the \`gh pr create\` command."

    cursor agent --stream-partial-output --output-format stream-json -p "$PROMPT_CONTENT"
    
    if [ ! -f "gitai.sh" ]; then
        echo "Error: gitai.sh was not generated"
        exit 1
    fi

    # Step 4: Execute PR script
    echo ""
    echo "Step 4/4: Creating PR..."
    chmod +x gitai.sh
    sh gitai.sh
    PR_EXIT_CODE=$?
    
    # Cleanup
    rm -f gitai.sh

    if [ $PR_EXIT_CODE -ne 0 ]; then
        echo "Error: PR creation script failed with exit code $PR_EXIT_CODE"
        exit $PR_EXIT_CODE
    fi

    echo ""
    echo "✓ Update workflow completed successfully!"
    exit 0
fi

# If no recognized command, show help
cat << 'HELP'
gitai - Git AI Assistant

USAGE:
    gitai generate commit              Generate gitai.sh with atomic commits
    gitai generate pr [--base <branch>] Generate gitai.sh with PR creation command
    gitai update [--base <branch>]     Update branch with commits (create PR if --base specified)
    gitai --help                       Show this help message

For more information, visit the project repository.
HELP
exit 1