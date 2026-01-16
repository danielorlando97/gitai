# GitAI

AI-powered Git workflow assistant that helps you create atomic commits and professional Pull Requests using Cursor AI.

## Features

- 🤖 **AI-Powered Commit Generation**: Automatically analyzes your changes and generates atomic commits following Conventional Commits standards
- 📝 **Professional PR Descriptions**: Creates well-structured Pull Request descriptions with all necessary sections
- ⚡ **Automated Workflow**: Single command to generate commits, apply them, and create PRs
- 🎯 **Conventional Commits**: Follows industry-standard commit message formats
- 🔧 **Flexible Base Branch**: Specify target branch for Pull Requests

## Requirements

- [Cursor AI](https://cursor.sh/) - AI-powered code editor
- [GitHub CLI](https://cli.github.com/) (`gh`) - Required for PR creation
- Git - Version control system
- Bash shell

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd gitai
```

2. Run the installation script:
```bash
./install.sh
```

3. The installer will:
   - Copy the `gitai` command to `~/.local/bin/`
   - Install prompt files to `~/.local/share/gitai/`
   - Add `~/.local/bin` to your PATH (if not already present)

4. Reload your shell configuration:
```bash
source ~/.zshrc  # or ~/.bashrc
```

5. Verify installation:
```bash
gitai --help
```

## Usage

### Generate Atomic Commits

Analyze your changes and generate a script with atomic commits:

```bash
gitai generate commit
```

This will:
1. Analyze all modified, new, and deleted files
2. Group changes into logical atomic commits
3. Generate a `gitai.sh` script with commit commands
4. You can review and execute: `sh gitai.sh`

### Generate Pull Request

Create a professional PR description:

```bash
# Without base branch (uses repository default)
gitai generate pr

# With specific base branch
gitai generate pr --base main
gitai generate pr -b develop
```

This will:
1. Analyze your changes
2. Generate a comprehensive PR description following best practices
3. Create a `gitai.sh` script with `gh pr create` command
4. You can review and execute: `sh gitai.sh`

### Automated Workflow

Execute the complete workflow in one command:

```bash
# Without base branch
gitai update

# With specific base branch
gitai update --base main
gitai update -b develop
```

This will automatically:
1. Generate atomic commits script
2. Execute commits
3. Generate PR creation script
4. Create the Pull Request
5. Clean up temporary files

## Commands

### `gitai generate commit`

Generates a `gitai.sh` script containing atomic commits based on your current changes.

**Example output:**
```bash
#!/bin/bash
# Initial project configuration
git add package.json tsconfig.json
git commit -m "chore: initialize base project configuration"

# Implement data models
git add src/models/*.ts
git commit -m "feat: add main data models"
```

### `gitai generate pr [--base <branch>]`

Generates a `gitai.sh` script with a `gh pr create` command including a well-structured PR description.

**Options:**
- `--base, -b <branch>`: Target base branch for the PR

**Example output:**
```bash
#!/bin/bash
# Create Pull Request

gh pr create --title "feat: add user authentication" --body "## Description
..."
```

### `gitai update [--base <branch>]`

Executes the complete workflow: generates commits, applies them, generates PR, and creates it.

**Options:**
- `--base, -b <branch>`: Target base branch for the PR

**Workflow:**
1. Step 1/4: Generating commit script
2. Step 2/4: Executing commits
3. Step 3/4: Generating PR script
4. Step 4/4: Creating PR

## PR Description Format

The generated PR descriptions follow this structure:

- **Description**: Brief explanation of why changes are needed
- **Context / Problem**: What error or behavior was observed
- **Solution / Changes**: Key technical changes made
- **Testing Instructions**: Steps to validate the behavior
- **Impact / Considerations**: Affected components, breaking changes, risks
- **Tickets**: Related ticket numbers (if applicable)

## Commit Message Format

Commits follow [Conventional Commits](https://www.conventionalcommits.org/) standards:

- `feat:` - New features
- `fix:` - Bug fixes
- `refactor:` - Code refactoring
- `docs:` - Documentation changes
- `style:` - Formatting changes
- `test:` - Test additions/modifications
- `chore:` - Build changes, dependencies, configs

## Examples

### Basic Workflow

```bash
# Make some changes to your code
git add .
gitai generate commit
# Review gitai.sh
sh gitai.sh
```

### Create PR with Specific Base Branch

```bash
gitai generate pr --base main
# Review gitai.sh
sh gitai.sh
```

### Complete Automated Workflow

```bash
# Make changes, then:
gitai update --base main
# That's it! Commits are created and PR is opened
```

## How It Works

GitAI uses Cursor AI's agent capabilities to:

1. **Analyze Changes**: Examines your git diff and project structure
2. **Understand Context**: Identifies logical groupings and dependencies
3. **Generate Scripts**: Creates executable bash scripts with git/gh commands
4. **Follow Best Practices**: Applies Conventional Commits and PR description standards

The tool generates scripts that you can review before executing, giving you full control over the process.

## Troubleshooting

### Command not found

If `gitai` command is not found after installation:

1. Ensure `~/.local/bin` is in your PATH:
```bash
echo $PATH | grep -q ".local/bin" || export PATH="$HOME/.local/bin:$PATH"
```

2. Add to your shell config file (`~/.zshrc` or `~/.bashrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

3. Reload your shell:
```bash
source ~/.zshrc  # or ~/.bashrc
```

### Cursor not found

Make sure Cursor AI is installed and the `cursor` command is available in your PATH.

### GitHub CLI not found

Install GitHub CLI:
- macOS: `brew install gh`
- Linux: See [GitHub CLI installation guide](https://cli.github.com/manual/installation)

### No changes found

Ensure you have uncommitted changes or staged files:
```bash
git status
git diff
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or suggestions, please open an issue on the repository.
