---
name: repo-skill-importer
description: Pulls Claude/Grok skills (SKILL.md folders) out of a GitHub repository, compares each one against skills already available in this environment, validates them, and either installs them automatically or packages them as installable .skill files. Use this whenever the user gives a GitHub repo or folder link containing skills and asks to check into, pull, import, sync, grab, install, or loop through the skills in it — even if they don't say skill-creator or package explicitly. Also trigger on phrases like compare and pull all the skills or do the same for the rest when a repo of skills was mentioned earlier in the conversation.
---

# Repo Skill Importer

Fetches every skill folder from a GitHub repo, diffs each against what's
already available locally, validates it, then delivers the skills in the
way that fits the current agent environment.

## Environment routing (do this first)

Detect which environment you are running in and load the matching reference:

| Environment signal | Load this reference | Delivery style |
|--------------------|---------------------|----------------|
| `skill-installer` present under `/root/.grok/skills/` **or** paths like `/home/workdir/.grok/skills/` | `references/grok.md` | **Auto-install** into persistent user skills dir |
| Claude / Anthropic-style paths (`/mnt/skills/...`) **or** `present_files` tooling | `references/claude.md` | **Package** as `.skill` files for the user to Save |
| Unclear | Prefer `references/claude.md` (safer, no write to skill dirs) and mention both options |

Read the chosen reference **before** starting the workflow. Follow its
steps for prerequisites, local skill locations, install/package commands,
and delivery notes. The common workflow outline below is shared; the
reference fills in the environment-specific details.

## Common workflow outline

1. **Get the repo's skill folders onto disk**  
   Prefer `codeload.github.com` tarball (or the environment's preferred
   download method). Locate every immediate subdirectory that contains a
   `SKILL.md`.

2. **Compare against what's already available**  
   Diff same-named skills. Bucket into three groups:
   - **Already available, identical**
   - **Already available, but differs** (list exactly which files differ)
   - **Not available locally** (new)

   Present a clear **Comparison result** to the user (table or structured
   summary) showing every skill and its bucket, plus a short description of
   what changed for any differing skills.

3. **Ask before proceeding** (mandatory interactive gate)  
   After showing the Comparison result, **stop and ask the user** whether
   to proceed. Do **not** install, overwrite, or package anything until the
   user explicitly confirms.
   - For identical skills: default recommendation is skip.
   - For differing skills: default recommendation is skip (to protect local
     customizations), but offer to overwrite/update if the user wants the
     repo version.
   - For new skills: default recommendation is install/package.
   Wait for the user's decision (e.g. "yes, update the differing ones",
   "install only the new ones", "overwrite all", "skip everything").

4. **Validate every skill** the user approved for delivery  
   Use the environment's validator (`quick_validate.py` or
   `validate-skill.sh`). Do not deliver broken skills.

5. **Deliver only what the user approved**  
   Follow the loaded reference:
   - Grok → auto-install into `/home/workdir/.grok/skills/`
   - Claude → package `.skill` files and present them

6. **Summarize**  
   What was already present, what was newly delivered / overwritten, any
   validation failures, and (for auto-install) that a new session is required.

## Notes

- If the repo has no `skills/` folder or no `SKILL.md` files, say so
  plainly rather than guessing at unrelated folders.
- If the user names a specific skill, only process that one.
- Prefer the environment-native path (auto-install on Grok, package on
  Claude). Offer the other path only if the user asks or the preferred
  path fails.
- **Never auto-overwrite a differing skill.** Always surface the Comparison
  result first and wait for explicit confirmation.
