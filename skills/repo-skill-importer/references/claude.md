# Claude / packaging path

Use this reference when running in a Claude / Anthropic-style environment
(paths under `/mnt/skills/`, `present_files` available, or when auto-install
is not possible).

## Prerequisites

This path leans on tooling from the `skill-creator` skill
(`quick_validate.py` and `package_skill.py`). If `skill-creator` isn't
already available, copy its `scripts/` directory into your working
directory first — everything below assumes `scripts/quick_validate.py` and
`scripts/package_skill.py` are importable as `scripts.quick_validate` /
`scripts.package_skill` from your working dir.

## 1. Get the repo's skill folders onto disk

`web_fetch` on `github.com/.../tree/...` URLs is usually blocked by
`robots.txt`. Don't fight it — pull the repo's tarball instead, which goes
through `codeload.github.com` (allowed egress domain):

```bash
curl -sL "https://codeload.github.com/<owner>/<repo>/tar.gz/refs/heads/<branch>" -o repo.tar.gz
tar -xzf repo.tar.gz
```

Default branch is usually `main`; fall back to `master` if that 404s. Then
locate the skills directory (commonly `skills/`, but check the repo's
`README.md` or root listing if it's not obvious) — each immediate
subdirectory containing a `SKILL.md` is one skill.

## 2. Compare against what's already available

For every skill folder found, check whether a skill of the same name already
exists locally — check `/mnt/skills/public/`, `/mnt/skills/private/`,
`/mnt/skills/examples/`, `/mnt/skills/plugins/`, and any deferred/installed
skills or plugins visible in the system prompt or `<available_skills>`. Where
a same-named skill exists, run a recursive diff:

```bash
diff -rq /mnt/skills/<location>/<skill-name> <extracted-repo>/skills/<skill-name>
```

Summarize the result to the user in three buckets before packaging anything:

- **Already available, identical** — skip packaging this one by default, mention it as FYI.
- **Already available, but differs** — call out exactly which files differ
  (e.g. a reference doc or a script) so the user can decide whether to
  overwrite; skip packaging by default here too unless the user asks for it.
- **Not available locally** — new to this environment; package these.

> **Hint:** Don't import/package a skill that's already available locally
> unless the user explicitly asks for it (e.g. "package it anyway", "give me
> the repo version", "update it"). Silently repackaging something the user
> already has adds clutter and risks overwriting a newer or customized local
> version with an older repo one. Default to skipping duplicates and only
> surfacing what's genuinely new — say what you skipped and why, so the user
> can override if they actually want it.

## 3. Validate every skill

Before packaging, validate each folder so problems surface before the user
tries to install:

```bash
python3 -m scripts.quick_validate <path-to-skill-folder>
```

Run this from the directory containing `scripts/` (see Prerequisites) so the
relative import resolves. Report validation failures to the user rather than
silently packaging a broken skill.

## 4. Package only what's new (or explicitly requested)

For each validated skill folder that is **not** already available locally
(per step 2's bucketing), package it:

```bash
python3 -m scripts.package_skill <path-to-skill-folder>
```

This produces a `<skill-name>.skill` file in the current directory. Loop
through every *new* skill folder found in step 1 — don't stop at the first
one unless the user only asked for one specific skill. Skip skills already
available locally (identical or differing) unless the user explicitly asks
you to package those too.

## 5. Deliver

Copy every resulting `.skill` file into the outputs directory and present
them all in a single `present_files` call so the user gets one batch of file
cards rather than one per skill. In the reply text (not repeated per file),
flag again which ones differ from an already-installed version — that's the
one thing the file cards themselves can't communicate.

## 6. Note the install boundary

Be upfront that presenting a `.skill` file is as far as this goes — actually
saving/installing it into the user's profile happens when *they* click the
file card's Save action (where the org allows it), not automatically. This
skill's job ends at "validated, packaged, and handed over".
