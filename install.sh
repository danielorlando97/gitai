#!/bin/bash
# Installation script for gitai global command

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURSOR_GITAI_DIR="$SCRIPT_DIR/cursor-gitai"

echo -e "${BLUE}Installing gitai command globally...${NC}"

# Check if cursor-gitai directory exists
if [ ! -d "$CURSOR_GITAI_DIR" ]; then
    echo -e "${RED}Error: cursor-gitai directory not found at $CURSOR_GITAI_DIR${NC}"
    exit 1
fi

# Create directory for gitai data files
GITAI_DATA_DIR="$HOME/.local/share/gitai"
mkdir -p "$GITAI_DATA_DIR"

# Copy the prompt.md file
PROMPT_SOURCE="$CURSOR_GITAI_DIR/commiter-prompt.md"
if [ ! -f "$PROMPT_SOURCE" ]; then
    echo -e "${RED}Error: commiter-prompt.md not found at $PROMPT_SOURCE${NC}"
    exit 1
fi
cp "$PROMPT_SOURCE" "$GITAI_DATA_DIR/prompt.md"
echo -e "${GREEN}✓ Copied prompt.md to $GITAI_DATA_DIR${NC}"

# Copy the pr-prompt.md file
PR_PROMPT_SOURCE="$CURSOR_GITAI_DIR/pr-prompt.md"
if [ ! -f "$PR_PROMPT_SOURCE" ]; then
    echo -e "${RED}Error: pr-prompt.md not found at $PR_PROMPT_SOURCE${NC}"
    exit 1
fi
cp "$PR_PROMPT_SOURCE" "$GITAI_DATA_DIR/pr-prompt.md"
echo -e "${GREEN}✓ Copied pr-prompt.md to $GITAI_DATA_DIR${NC}"

# Create the gitai executable
GITAI_EXEC="$HOME/.local/bin/gitai"
CLI_SOURCE="$CURSOR_GITAI_DIR/cli.sh"
if [ ! -f "$CLI_SOURCE" ]; then
    echo -e "${RED}Error: cli.sh not found at $CLI_SOURCE${NC}"
    exit 1
fi
cp "$CLI_SOURCE" "$GITAI_EXEC"
echo -e "${GREEN}✓ Copied cli.sh to $GITAI_EXEC${NC}"

# Make gitai executable
chmod +x "$GITAI_EXEC"

# Detect user's default shell (not the script's shell)
USER_SHELL="${SHELL##*/}"
SHELL_RC=""
if [ "$USER_SHELL" = "zsh" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ "$USER_SHELL" = "bash" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_RC="$HOME/.bash_profile"
fi

# Ensure ~/.local/bin exists
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

# Add ~/.local/bin to PATH if not already there
if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
    if [ -n "$SHELL_RC" ]; then
        # Check if PATH entry already exists in rc file
        if ! grep -q "export PATH.*\.local/bin" "$SHELL_RC" 2>/dev/null; then
            echo "" >> "$SHELL_RC"
            echo '# Added by gitai installer' >> "$SHELL_RC"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
            echo -e "${GREEN}Added ~/.local/bin to PATH in $SHELL_RC${NC}"
            echo -e "${BLUE}Please run: source $SHELL_RC${NC}"
        else
            echo -e "${BLUE}~/.local/bin already in PATH (configured in $SHELL_RC)${NC}"
        fi
    else
        echo -e "${BLUE}Please add this to your shell rc file:${NC}"
        echo 'export PATH="$HOME/.local/bin:$PATH"'
    fi
else
    echo -e "${GREEN}~/.local/bin already in PATH${NC}"
fi

echo -e "${GREEN}✓ gitai command installed successfully!${NC}"
echo -e "${BLUE}Executable: $GITAI_EXEC${NC}"
echo -e "${BLUE}Data directory: $GITAI_DATA_DIR${NC}"
echo -e "${BLUE}Usage: Navigate to your project directory and run 'gitai generate commit'${NC}"