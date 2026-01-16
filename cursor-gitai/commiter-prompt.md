# Cursor Prompt: Atomic Commits Script Generator

Analyze all the current project code and git status to generate a `gitai.sh` file containing all necessary commits to update the repository progressively.

## Objectives

1. **Analyze current state**: Examine all modified, new, and deleted files comparing them with the last commit
2. **Identify logical changes**: Group changes into coherent atomic units based on:
   - Implemented functionality
   - Refactorings
   - Bug fixes
   - Configuration changes
   - Dependency updates
   - Documentation improvements

3. **Generate gitai.sh**: Create a bash script that:
   - Contains an ordered sequence of commits
   - Each commit groups logically related changes
   - Uses descriptive messages following Conventional Commits
   - Progresses from fundamental changes to high-level implementations

## Script Requirements

```bash
#!/bin/bash
# Each commit should follow this structure:

# 1. git add specific related files
# 2. git commit with descriptive message
# 3. Comments explaining the commit's purpose

# Example:
# Initial project configuration
git add package.json tsconfig.json
git commit -m "chore: initialize base project configuration"

# Implement data models
git add src/models/*.ts
git commit -m "feat: add main data models"
```

## Commit Message Format

Use Conventional Commits:
- `feat:` new features
- `fix:` bug fixes
- `refactor:` refactorings without functionality changes
- `docs:` documentation changes
- `style:` formatting, missing semicolons, etc.
- `test:` add or modify tests
- `chore:` build changes, dependencies, configs

**CRITICAL: Avoid special characters in commit messages**
- NEVER use single quotes ('), double quotes ("), backticks (`), or any other
  special characters in commit messages
- Use only alphanumeric characters, spaces, hyphens (-), colons (:), and
  parentheses () when necessary
- Replace any special characters with their plain text equivalents or remove
  them entirely
- Examples of BAD messages:
  - `feat: add "user" authentication` (contains quotes)
  - `fix: handle user's data` (contains apostrophe)
  - `chore: update \`package.json\`` (contains backticks)
- Examples of GOOD messages:
  - `feat: add user authentication`
  - `fix: handle user data`
  - `chore: update package.json`

## Suggested Commit Order

1. Configuration and dependencies
2. Base project structure
3. Models and data types
4. Utilities and helpers
5. Business logic/services
6. Components/views (from simple to complex)
7. Component integration
8. Tests
9. Documentation
10. Final adjustments and optimizations

## Specific Instructions

- **Atomic commits**: Each commit should represent a complete and functional
  change on its own
- **Clear messages**: Explain WHAT changed and WHY (when not obvious)
- **Appropriate size**: Neither too granular nor too broad (ideally 1-15 files
  per commit)
- **Dependencies**: Respect the logical order of dependencies between modules
- **No errors**: Each commit should leave the project in a state without
  compilation errors
- **NO SPECIAL CHARACTERS**: Commit messages MUST NOT contain quotes (' or "),
  backticks (`), apostrophes, or any other special characters that could break
  the bash script. Use only plain ASCII alphanumeric characters, spaces,
  hyphens, colons, and parentheses

## Expected Output

Generate an executable `gitai.sh` file with:
- Shebang at the beginning
- Explanatory comments for each section
- Complete sequence of git add/commit commands
- Final message indicating all changes were committed