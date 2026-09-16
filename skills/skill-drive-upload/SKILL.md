---
name: skill-drive-upload
description: Upload skills (or skill zips) to the user's Google Drive skills folder at My Drive/.agent/skills. Use when the user asks to upload a skill, move a skill to Drive, put a skill in .agent/skills, or similar. Always target that folder.
---

# Skill Drive Upload

## Overview

Standard location for skills on this user's Google Drive is `My Drive/.agent/skills` (folder ID `1BujfOJNyZczxwk1GDqnr86dZbfgfu3AK`). Always upload skill packages there.

## Instructions

When uploading a skill to Drive:

1. **Locate the skill directory**
   - User skills live under `/home/workdir/.grok/skills/<skill-name>/`.
   - Bundled skills are under `/root/.grok/skills/<skill-name>/` (copy or zip from there if needed).

2. **Package the skill**
   - Create a zip of the skill folder (exclude `__pycache__` and `*.pyc`):
     ```bash
     cd /path/to/parent && zip -r /home/workdir/artifacts/<skill-name>.zip <skill-name> -x "*/__pycache__/*" "*.pyc"
     ```
   - Place the zip under `/home/workdir/artifacts/` so the Drive upload tool can see it.

3. **Upload to the correct folder**
   - Use the Google Drive upload tool with:
     - `artifact_path`: `/<skill-name>.zip` (relative to artifacts root)
     - `file_name`: `<skill-name>.zip` (or a clear name the user requested)
     - `folder_id`: `1BujfOJNyZczxwk1GDqnr86dZbfgfu3AK`
   - Do **not** upload to Drive root or any other folder unless the user explicitly asks for a different location.

4. **Confirm**
   - After upload, report the file name, size if useful, and the Drive web link.
   - Optionally list the target folder to show the new file is present.

## Notes

- The folder path is always `My Drive/.agent/skills`. Prefer the stable folder ID above.
- If the user says "upload this skill" or "move all skills to this folder", follow the steps above.
- For bulk uploads of multiple skills, zip and upload each one into the same folder ID.
- Never leave skill zips only in artifacts without uploading when the user asked for Drive.
