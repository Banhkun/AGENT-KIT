# Antigravity IDE / Direct Install Path

Use this reference when running in a Google Antigravity / Gemini environment (indicated by `.agents/skills/` in the workspace root or `~/.gemini/config/`).

## Local Skill Locations
- **Workspace Skills (Default)**: `<workspace>/.agents/skills/<skill-name>/`
- **Global Skills**: `~/.gemini/config/skills/<skill-name>/`

## 1. Download & Extract
Download the repository archive using curl or PowerShell:

```powershell
curl.exe -sL "https://codeload.github.com/<owner>/<repo>/tar.gz/refs/heads/<branch>" -o temp_repo/repo.tar.gz
tar -xzf temp_repo/repo.tar.gz -C temp_repo
```

Locate the skills directory (commonly `skills/`) — each immediate subdirectory containing a `SKILL.md` is one skill.

## 2. Compare Against Local Skills
Locate every skill folder in the downloaded repo and compare it against same-named local skills in `<workspace>/.agents/skills/`.

When running on Windows, normalize line endings before diffing to avoid false positives caused by CRLF (local checkouts) vs LF (tarball archives):
- **Already available, identical**: Text content matches after normalizing line endings (`-replace "\r\n", "`n"`). Recommend skip.
- **Already available, but differs**: Specific files differ. Recommend skip by default to protect local customizations, but offer to update/overwrite if the user requests the repo version.
- **Not available locally**: Skill directory does not exist locally. Recommend install.

Present a structured comparison summary showing every skill and its bucket.

## 3. Mandatory Interactive Gate
After showing the comparison, **stop and ask the user** using `ask_question`:
- Recommend installing new skills.
- Explicitly ask before updating or overwriting differing skills.
- Never install, overwrite, or delete anything until the user confirms.

## 4. Validate Approved Skills
Validate each approved skill folder using the validator from `skill-creator`:

```powershell
python -m scripts.quick_validate "<path-to-skill-folder>"
```

*Note*: If `pyyaml` is not present in the global Python environment, run via `uv`:
```powershell
uv run --with pyyaml python -m scripts.quick_validate "<path-to-skill-folder>"
```

Report any validation failures before proceeding with delivery.

## 5. Install Approved Skills
Directly copy the validated folders into `<workspace>/.agents/skills/<skill-name>/`:
- If updating an existing differing skill, remove or overwrite the destination folder cleanly.
- If installing a new skill, create the target folder and copy files recursively.
- Clean up any temporary files in `temp_repo`.

## 6. Deliver Summary
Summarize:
- Skills that were already present and skipped
- Skills newly installed or updated
- Reminder that a new chat session or editor reload triggers discovery of the new skills
