---
name: commit-commands
description: >-
  Automates and guides git workflows: crafting conventional and style-matched
  commits, screening secrets, end-to-end branch-commit-push-PR creation via GitHub
  CLI, and safely pruning stale [gone] branches and worktrees. Use when the user
  asks to commit changes, write a commit message, stage files, push changes, create
  a PR / pull request, clean up merged or deleted branches, or run git commit
  commands. Prefer creating a pull request over direct pushes to main/master.
---

# Commit Commands

Automates git operations and enforces clean git practices, reducing manual context switching while ensuring security, consistent commit history, and tidy branch tracking.

## Preferred delivery path: Pull Request (default)

**Creating a pull request is always preferable** to committing or pushing directly to `main` / `master` / other protected default branches.

- Default workflow for any change (skills, code, docs, config): **branch → commit → push → open PR**.
- Direct push to `main` (e.g. via `github___push_files` or `git push origin main`) is allowed **only** when the user explicitly requests it.
- This rule applies especially when updating skills in repositories such as `AGENT-KIT`.

When using the GitHub connected tools, prefer the sequence that creates a feature branch + PR over a direct commit to `main`.

## Core Workflows

### 1. Smart Commit (`commit`)

Drafts and creates a git commit adhering to repository style, ensuring no sensitive files or secrets are staged.

#### Workflow Steps:
1. **Analyze Repository Status & Diff**:
   - Check status: `git status -s`
   - Inspect changes: `git diff HEAD` (or unstaged `git diff` and staged `git diff --cached`)
   - Check current branch: `git branch --show-current`
   - Check recent commits to match repo tone/style: `git log -n 5 --oneline`

2. **Secret & Sensitive Data Guard**:
   - Explicitly verify and NEVER stage:
     - Environment configs (`.env`, `.env.local`, `*.env`)
     - Credentials and tokens (`credentials.json`, `id_rsa`, `*.pem`, `*.key`, `token*`)
     - Database connection strings with embedded passwords
     - Transient files, local IDE caches (`.gemini/`, `.idea/`, `.vscode/` unless intended)
   - If untracked sensitive files exist, prompt or ensure they are added to `.gitignore`.

3. **Stage Targeted Files**:
   - Stage specific files: `git add <file1> <file2>`
   - Avoid indiscriminate `git add .` or `git add -A` when untracked scratch files exist.

4. **Draft Commit Message**:
   - Match conventional commit format:
     - `feat:` new features or capabilities
     - `fix:` bug fixes
     - `refactor:` code restructuring without changing behavior
     - `docs:` documentation updates
     - `chore:` maintenance, dependency bumps, tooling
     - `test:` adding or fixing tests
   - Keep subject line concise (under 72 characters), imperative mood ("add", "fix", not "added", "fixed").
   - Add a brief bulleted description if the commit involves multiple key changes.

5. **Commit & Verify**:
   - `git commit -m "<commit message>"`
   - Output summary of committed files and hash.

---

### 2. Commit, Push, and Open PR (`commit-push-pr`) — **preferred**

Complete pipeline from local code changes to an open Pull Request on GitHub.
This is the **default** path for delivering changes.

#### Workflow Steps:
1. **Branch Check & Creation**:
   - Check current branch: `git branch --show-current`
   - If on protected or default branch (`main`, `master`, `develop`):
     - Always create a descriptive feature branch (do not commit directly):
       ```bash
       git checkout -b feat/<short-description>
       ```
       or `fix/…`, `chore/…`, `docs/…` as appropriate.

2. **Stage & Commit**:
   - Follow the **Smart Commit** workflow above.

3. **Push to Remote**:
   - Push branch and configure upstream tracking:
     ```bash
     git push -u origin <branch-name>
     ```

4. **Create Pull Request via GitHub CLI (`gh`) or connected tools**:
   - Prefer `gh pr create` when available:
     ```bash
     gh pr create --title "<PR Title>" --body "$(cat <<'EOF'
     ## Summary
     - <Bullet 1>
     - <Bullet 2>

     ## Verification & Testing
     - [x] <Verification item 1>
     - [ ] <Verification item 2>
     EOF
     )"
     ```
   - When using GitHub connected tools, create the branch + commit on the feature branch, then open a PR rather than writing directly to `main`.
   - Provide the generated PR URL to the user.

---

### 3. Clean Stale [gone] Branches (`clean_gone`)

Cleans up local branches whose remote upstream branches have been merged or deleted, safely handling any associated git worktrees before branch deletion.

#### Automated Execution:

**In PowerShell (Windows)**:
```powershell
# 1. Prune stale tracking references
git fetch --prune

# 2. Find branches marked as [gone]
$goneBranches = git branch -vv | Where-Object { $_ -match '\[gone\]' } | ForEach-Object {
    ($_ -replace '^[*+\s]+', '').Split(' ')[0]
}

if (-not $goneBranches) {
    Write-Host "No stale [gone] branches found."
    return
}

# 3. Safely remove attached worktrees if any exist
$worktrees = git worktree list
foreach ($branch in $goneBranches) {
    $wt = $worktrees | Where-Object { $_ -match "\[$branch\]" } | ForEach-Object { $_.Split(' ')[0] }
    if ($wt -and (Test-Path $wt)) {
        Write-Host "Removing worktree for $branch at $wt"
        git worktree remove --force "$wt"
    }
    Write-Host "Deleting branch $branch"
    git branch -D $branch
}
```

**In Bash / macOS / Linux**:
```bash
git fetch --prune
git branch -vv | grep '\[gone\]' | sed 's/^[+* ]//' | awk '{print $1}' | while read branch; do
  echo "Processing branch: $branch"
  worktree=$(git worktree list | grep "\\[$branch\\]" | awk '{print $1}')
  if [ -n "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
    echo "  Removing worktree: $worktree"
    git worktree remove --force "$worktree"
  fi
  echo "  Deleting branch: $branch"
  git branch -D "$branch"
done
```

Or execute the included helper script:
```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/commit-commands/scripts/clean-gone.ps1
```

---

## Best Practices & Safety Rules
- **Prefer Pull Request** over direct push to `main`/`master`. Only direct-push when the user explicitly asks.
- Always run `git status` and verify changes before executing a commit.
- Never commit secrets, credentials, or transient runtime files.
- Ensure worktrees are detached/removed before attempting `git branch -D` on a branch.
- Avoid forcing pushes (`--force`) on shared branches (`main`, `master`).
