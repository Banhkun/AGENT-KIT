# Grok / auto-install path

Use this reference when running in a Grok environment (`skill-installer`
present under `/root/.grok/skills/`, or user skills live under
`/home/workdir/.grok/skills/`).

## Prerequisites

Prefer the bundled `skill-installer` skill (it provides
`scripts/install-skill.sh` and `scripts/list-skills.sh`). If packaging is
also needed, lean on tooling from `skill-creator` (`quick_validate.py` and
`package_skill.py`). If those scripts are missing, copy them from a
skill-creator that has them into the working directory so
`python3 -m scripts.quick_validate` and `python3 -m scripts.package_skill`
resolve.

## 1. Get the repo's skill folders onto disk (or use skill-installer URLs)

`web_fetch` / `open_page` on `github.com/.../tree/...` URLs is often blocked
by robots.txt. Prefer one of these approaches:

**Preferred (auto-install path):** Use the skill-installer directly with
`--repo` / `--path` / `--url` — it downloads the zip itself and does not
require a local tarball.

**Fallback (for packaging or when you need the folders on disk):**

```bash
curl -sL "https://codeload.github.com/<owner>/<repo>/tar.gz/refs/heads/<branch>" -o repo.tar.gz
tar -xzf repo.tar.gz
```

Default branch is usually `main`; fall back to `master` if that 404s. Then
locate the skills directory (commonly `skills/`, but check the repo's
README.md or root listing if it's not obvious) — each immediate
subdirectory containing a `SKILL.md` is one skill.

## 2. Compare against what's already available

For every skill folder found, check whether a skill of the same name already
exists locally. Look in:

- `/home/workdir/.grok/skills/` (user skills — persistent)
- `/root/.grok/skills/` (bundled skills)
- Any other locations visible in the system prompt or available_skills list

Where a same-named skill exists, run a recursive diff:

```bash
diff -rq /path/to/local/<skill-name> <extracted-repo>/skills/<skill-name>
```

Present a clear **Comparison result** to the user (preferably a table or
structured list) with three buckets:

- **Already available, identical** — mention as FYI; recommend skip.
- **Already available, but differs** — list exactly which files differ and
  briefly describe the changes so the user can decide; recommend skip by
  default (to protect local customizations) but offer overwrite.
- **Not available locally** — new to this environment; recommend install.

## 3. Ask before proceeding (mandatory interactive gate)

**Stop after the Comparison result.** Do **not** install, overwrite, or
package anything until the user explicitly confirms what to do.

Ask a clear question, for example:

> Comparison complete. How would you like to proceed?
> - Update / overwrite the differing skill(s)?
> - Install only the new skill(s)?
> - Skip everything?
> - Something else (please specify)?

Wait for the user's answer. Never auto-overwrite a differing skill.

## 4. Validate every skill the user approved

Only after confirmation, validate each approved folder:

```bash
# Preferred if skill-creator scripts are present
python3 -m scripts.quick_validate <path-to-skill-folder>

# Or the shell validator from the bundled skill-creator
bash /root/.grok/skills/skill-creator/scripts/validate-skill.sh <path-to-skill-folder>
```

Report validation failures rather than silently installing a broken skill.

## 5. Install approved skills (preferred)

For each validated skill the user approved (new **or** explicitly requested
overwrite), install it into the persistent user skills directory.

If the destination already exists (overwrite case), remove it first:

```bash
rm -rf /home/workdir/.grok/skills/<skill-name>
```

Then install:

```bash
bash /root/.grok/skills/skill-installer/scripts/install-skill.sh \
  --repo <owner>/<repo> \
  --path <path/to/skill> \
  --ref <branch> \
  --dest /home/workdir/.grok/skills
```

Or with a full GitHub tree URL:

```bash
bash /root/.grok/skills/skill-installer/scripts/install-skill.sh \
  --url https://github.com/<owner>/<repo>/tree/<branch>/<path/to/skill> \
  --dest /home/workdir/.grok/skills
```

- Loop through every approved skill — don't stop at the first one.
- After successful installs, tell the user clearly that they must **start a
  new session** for the new/updated skills to be discovered and become available.

This is the preferred path because it requires no user upload or Save
action — the skills are live in `/home/workdir/.grok/skills/` immediately
(after a session restart).

## 6. Package only when needed (fallback or explicit request)

Use packaging instead of (or in addition to) auto-install when:

- The skill-installer is unavailable or fails, **or**
- The user explicitly asks for `.skill` files / packages / downloadable
  artifacts.

```bash
python3 -m scripts.package_skill <path-to-skill-folder>
```

Present the resulting `.skill` files to the user (via the file render /
download mechanism available in the environment). Note that packaging ends
at "validated and handed over" — the user still has to Save/install the
file themselves.

## 7. Deliver summary

Always give a clear summary:

- What was already present (identical / differing)
- What the user decided
- What was newly installed or overwritten (and that a new session is required)
- What was packaged (if anything)
- Any validation failures
