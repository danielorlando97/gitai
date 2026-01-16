# Cursor Prompt: Pull Request Script Generator

Analyze all the current project code and git status to generate a `gitai.sh` file containing the command to create a Pull Request with a well-structured description.

## Objectives

1. **Analyze current state**: Examine all modified, new, and deleted files comparing them with the last commit
2. **Identify changes**: Understand the purpose and impact of the changes
3. **Generate gitai.sh**: Create a bash script that contains a `gh pr create` command with:
   - A concise, descriptive PR title
   - A comprehensive PR description following the specified format

## Script Requirements

```bash
#!/bin/bash
# Create Pull Request with AI-generated description

gh pr create --title "PR Title Here" --body "PR Description Here"
```

If a base branch is specified, include the `--base <branch>` flag:

```bash
#!/bin/bash
# Create Pull Request with AI-generated description

gh pr create --title "PR Title Here" --body "PR Description Here" --base main
```

The PR description must follow this exact Markdown format:

---

## Description

<!-- Brief explanation: Why are these changes needed? -->

[Write a concise explanation (2-4 sentences) of the purpose and motivation behind these changes. Focus on the "why" and the business/technical value.]

---

## Context / Problem

<!-- What error or behavior was observed? Why is this a problem? Include screenshots if useful. -->

[Describe the problem, bug, or limitation that motivated these changes. If you can infer it from the diff, explain what wasn't working or what was missing. If the context is not clear from the diff, use a placeholder:

"**[⚠️ TO BE COMPLETED]** Please describe:

- What error or unexpected behavior was observed?
- Why is this a problem?
- Include screenshots or logs if applicable."

Otherwise, provide a clear explanation based on the code changes.]

---

## Solution / Changes

<!-- List the key changes made in this PR. -->

[Provide a clear, bulleted list of the most significant technical changes made. Group related changes logically and focus on the functional modifications. For example:

- **Authentication Service (`AuthService.ts`):** Created a new service to handle JWT token generation and validation
- **Login Endpoint:** Added `POST /api/v1/login` that authenticates users and returns a JWT token
- **User Model:** Extended the `User` database model with `last_login` timestamp and `password_hash` fields
- **Middleware:** Updated `authMiddleware.ts` to validate JWT tokens on protected routes
- **Tests:** Added unit tests for `AuthService` and integration tests for the login flow]

---

## Testing Instructions

<!-- Steps or scenarios to validate the behavior. Include examples, commands, screenshots. -->

[Provide step-by-step instructions for reviewers to test the changes. Be as specific as possible based on what you can infer from the diff. If complete testing steps cannot be determined, provide a template:

"**[⚠️ TO BE COMPLETED]** Suggested testing approach:

1. **Setup:** [Describe any required setup, e.g., database migrations, environment variables]
2. **Test Scenario 1:** [Describe the main happy path]
   - Example: `curl -X POST http://localhost:3000/api/v1/login -d '{"email":"user@example.com","password":"test123"}'`
   - Expected result: [What should happen]
3. **Test Scenario 2:** [Describe edge cases or error scenarios]
4. **Verification:** [How to confirm the changes work correctly]

Please add specific test cases, screenshots, or additional scenarios."]

---

## Impact / Considerations

<!-- Does it affect other modules? Is it backwards compatible? Any risk? -->

[Analyze and describe:

- **Affected Components:** Which parts of the system are impacted by these changes
- **Breaking Changes:** Is this backwards compatible? Will existing code need updates?
- **Risks:** Any potential issues or side effects to be aware of
- **Performance:** Any performance implications (positive or negative)

For example:

- **Breaking Change:** The old `/login` endpoint is now deprecated and will be removed in v2.0
- **Frontend Impact:** Client applications must update to send JWT tokens in the `Authorization` header
- **Database:** Requires migration to add new `User` fields (migration script included)
- **Risk:** Consider rate-limiting the login endpoint to prevent brute-force attacks]

---

## Tickets

**[⚠️ TO BE COMPLETED]**

- JIRA-XXXX
- [Add related ticket numbers]

---

## PR Title Requirements

The PR title should be:
- Concise (50-72 characters recommended)
- Descriptive of the main change
- Follow conventional commit format when possible (feat:, fix:, refactor:, docs:, chore:, test:, perf:)
- No ending period
- **CRITICAL: Avoid special characters** - Use only alphanumeric characters, spaces, hyphens (-), colons (:), and parentheses () when necessary

Examples:
- `feat: add user authentication system`
- `fix: resolve memory leak in data processor`
- `refactor: simplify authentication middleware`

## Script Format Requirements

**CRITICAL: The script must use proper escaping for the PR body**

The `gh pr create` command must properly escape the body content. Use a heredoc or proper quoting:

```bash
#!/bin/bash
# Create Pull Request

gh pr create --title "feat: add user authentication" --body "$(cat << 'BODY'
## Description

This PR adds user authentication to secure API endpoints.

## Context / Problem

Previously, API endpoints were publicly accessible.

## Solution / Changes

- Added authentication service
- Created login endpoint
- Updated middleware

## Testing Instructions

1. Run the application
2. Test login endpoint

## Impact / Considerations

- Breaking change: Old endpoints deprecated
- Requires database migration

## Tickets

- JIRA-123
BODY
)"
```

If a base branch is specified, add the `--base` flag:

```bash
#!/bin/bash
# Create Pull Request

gh pr create --title "feat: add user authentication" --body "$(cat << 'BODY'
## Description

This PR adds user authentication to secure API endpoints.

## Context / Problem

Previously, API endpoints were publicly accessible.

## Solution / Changes

- Added authentication service
- Created login endpoint
- Updated middleware

## Testing Instructions

1. Run the application
2. Test login endpoint

## Impact / Considerations

- Breaking change: Old endpoints deprecated
- Requires database migration

## Tickets

- JIRA-123
BODY
)" --base main
```

Or use a simpler approach with escaped newlines:

```bash
#!/bin/bash
# Create Pull Request

gh pr create --title "feat: add user authentication" --body "## Description

This PR adds user authentication.

## Context / Problem

API endpoints were publicly accessible.

## Solution / Changes

- Added authentication service
- Created login endpoint

## Testing Instructions

1. Run the application
2. Test login endpoint

## Impact / Considerations

- Breaking change: Old endpoints deprecated

## Tickets

- JIRA-123"
```

If a base branch is specified, add the `--base` flag:

```bash
#!/bin/bash
# Create Pull Request

gh pr create --title "feat: add user authentication" --body "## Description

This PR adds user authentication.

## Context / Problem

API endpoints were publicly accessible.

## Solution / Changes

- Added authentication service
- Created login endpoint

## Testing Instructions

1. Run the application
2. Test login endpoint

## Impact / Considerations

- Breaking change: Old endpoints deprecated

## Tickets

- JIRA-123" --base main
```

## Guiding Principles

1. **Analyze, Don't Just List:** Understand the *intent* of the changes from the code, not just the file modifications.
2. **Be Explicit About Limitations:** Use clear placeholder markers (`**[⚠️ TO BE COMPLETED]**`) for information that cannot be extracted from the diff alone.
3. **Prioritize Completeness:** Fill in as much as possible from the diff analysis, but don't fabricate information.
4. **Audience:** Write for software developers (reviewers, future maintainers) using appropriate technical terminology.
5. **Conventional Commits:** Recognize the type of change (feat, fix, refactor, docs, chore, test, perf) and adapt the tone accordingly.
6. **Actionable Testing:** Provide concrete commands, API calls, or steps that reviewers can actually execute.
7. **Objectivity:** Base descriptions solely on the provided diff. If you make assumptions, state them clearly.
8. **Proper Escaping:** Ensure the bash script is valid and the PR body is properly formatted in the `gh pr create` command.

## Expected Output

Generate an executable `gitai.sh` file with:
- Shebang at the beginning (`#!/bin/bash`)
- Comments explaining the PR creation
- A single `gh pr create` command with properly formatted title and body
- The body must contain the complete PR description following the Markdown format specified above
