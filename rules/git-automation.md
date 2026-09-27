# Git & Repository Automation

## Autonomous Repository Cloning & Imports
- **No Destination Inquiries**: Never pause execution to prompt the user with interactive modal questions about where to clone or place repository files. Always follow standard conventions:
  - **Skills / Agent Customizations**: When pulling skills or agent toolkits, automatically place them into `.agents/skills/<skill-name>/`.
  - **General Projects / Repositories**: When cloning a Git repository, clone directly into `./<repo-name>` within the active workspace.
  - **Subdirectory Pulls**: If the user links to a specific subfolder (e.g., `/tree/main/...`), clone shallowly (`--depth 1`) to a temporary folder, move the target items into their destination, and immediately delete the temporary clone.

## Network & Sandbox Resilience
- Remote Git operations (cloning, fetching, submodules) require network access and may encounter SSL/schannel certificate hurdles in isolated sandboxes.
- When a git command encounters network or certificate errors in the sandbox, seamlessly re-run with appropriate execution bypass (`BypassSandbox: true`) to fulfill the request.

## Proactive Autonomous Defaults
- Assume the user's intent is to get the code or skills ready for immediate use.
- Proceed with recommended, non-destructive defaults without asking for unnecessary confirmation.
- Only stop for confirmation if the action would overwrite uncommitted local edits or delete existing user data.
