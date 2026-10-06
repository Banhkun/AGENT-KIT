---
name: teams-agent-converter
description: >-
  Converts the runmyjobs-redwood-query and runmyjobs-redwood-script skills into the flat, all-.txt
  "monolith" package used by the RMJ-Script-Query-Agent (a standalone agent whose system prompt only says
  "cat the instruction file in /mnt/data"). Use this skill whenever the user wants to convert, rebuild,
  refresh, re-sync, port, flatten or package the Redwood/RunMyJobs skills as .txt files, mentions
  RMJ-Script-Query-Agent, 00_START_HERE_JAVA / 00_START_HERE_SQL, explore.py.txt, lookup.py.txt,
  model.json.txt, a "monolith" or "flat folder" edition, or wants a standalone instruction file or system
  prompt for an agent that has no skill support. Also use it after either upstream Redwood skill changes,
  and when debugging a monolith whose agent cannot find a file, a cookbook section, or the model.
---

# Teams agent converter

Turns two folder-based skills into **one flat folder of `.txt` files** plus a tiny system prompt, so an
agent without skill support can use them. The agent's only built-in knowledge is the system prompt; every
rule lives in files it reads with `bash cat`.

## Target layout (what the agent sees)

```
SYSTEM-PROMPT.txt                       <- paste into the agent's system prompt field (4 lines)
data/                                   <- upload ALL of these to /mnt/data
├── RMJ-Script-Query-Agent-instruction.txt   hand-authored: HARD GATE, task routing, business terms
├── 00_START_HERE_JAVA.txt                   hand-authored: Java router + six rules
├── 00_START_HERE_SQL.txt                    hand-authored: SQL router + nine rules
├── sql-cookbook.txt, sql-data-model-exploration.txt,
│   sql-execution-modes.txt, sql-syntax-and-rules.txt     <- from query skill references/ (sql- prefix)
├── sql-query-rules.txt                      <- GENERATED from query SKILL.md "Non-Negotiable Rules"
├── runtime-and-shapes.txt, entities-and-lookup.txt, object-queries.txt,
│   job-and-chain-operations.txt, uc4-object-tags.txt, troubleshooting.txt   <- script skill references/
├── explore.py.txt, lookup.py.txt, build_model.py.txt        <- scripts (run, never read)
└── model.json.txt                           <- 600 KB, ONE shared copy (never open)
```

The `.txt` extension on programs and the model is intentional (upload filters only accept text); Python runs
`python3 explore.py.txt ...` fine. Never rename them back.

## Layers: what is generated vs hand-authored

| Layer | Source of truth | How it is produced |
| :-- | :-- | :-- |
| Reference guides, programs, model | the two upstream skills | **generated** by `scripts/convert.py build` |
| `sql-query-rules.txt` | query `SKILL.md` rules section | **generated** (no upstream reference file exists) |
| Instruction + two START_HERE files | `assets/templates/` in this skill | **copied**; edited by hand, never regenerated from SKILL.md |
| Hand-authored extras with no upstream (`job-definition-actions.txt`) | `assets/extras/` in this skill | **copied** automatically; `--extras DIR` adds more or overrides one |

Do not try to regenerate the START_HERE files from the upstream `SKILL.md` files. They are supersets
(Java: six rules vs four upstream; SQL: nine vs six) with agent-specific gating added. When upstream rules
change, diff the upstream "Non-Negotiable Rules" against the START_HERE file and port the change by hand,
keeping local additions.

## Workflow

1. **Build.** Defaults point at `/mnt/skills/plugins/...` and `/mnt/user-data/outputs/rmj-monolith`.
   ```bash
   python3 scripts/convert.py build [--query-skill DIR] [--script-skill DIR] [--out DIR] [--extras DIR]
   ```
   `build` runs `verify` at the end and exits 1 on any FAIL. If the user already has hand-authored files with
   no upstream source other than the bundled `job-definition-actions.txt`, ask for them and pass `--extras`.
   To update a bundled extra, convert the new `.md` to `.txt` (rewrite any `.docx`/`.md` guide names to the
   flat `.txt` names) and drop it into `assets/extras/`.
2. **Read the verify output.** A `warn` means a routing table names a file that is not in the folder. Any `FAIL`
   means do not deliver.
3. **Deliver** with `present_files`: zip `data/` (or present the files) plus `SYSTEM-PROMPT.txt`. Tell the user
   which files are generated and which are templates.
4. **If the user supplies their own newer START_HERE / instruction files,** copy them into
   `assets/templates/` (they win over the bundled ones) and rebuild; then run the invariant checks below.

## What `convert.py build` does (the conversion rules)

1. `assets/model.json` -> `model.json.txt`. Both upstream copies must be byte-identical; if not, stop and ask.
2. Programs -> `.py.txt`, **and patch `DEFAULT_MODEL`**: upstream uses `HERE/../assets/model.json`, which does
   not exist in a flat folder. Patched to `HERE/model.json.txt`. Also patches the not-found message and
   `build_model.py`'s default `--out`. If the pattern is not found the build aborts (upstream changed).
3. References `.md` -> `.txt`. Query refs get an `sql-` prefix: `query-cookbook.md` -> `sql-cookbook.txt`,
   `data-model-exploration.md` -> `sql-data-model-exploration.txt`, `execution-modes.md` ->
   `sql-execution-modes.txt`. Script refs keep their stem.
4. Text rewrites in every file: `python scripts/x.py` -> `python3 x.py.txt`; `assets/model.json` ->
   `model.json.txt`; `references/x.md` -> flat name; markdown links `[label](file:///references/x.md#3-...)`
   -> `label (x.txt, section 3)`.
5. **Cookbook section markers.** `00_START_HERE_SQL.txt` extracts one recipe with
   `awk '/SECTION: N\./{f=1} /SECTION: N+1\./{f=0} f' sql-cookbook.txt`. Upstream has plain `## N. Title`
   headings, so the converter inserts a line `=== SECTION: N. Title ===` before each. Without markers awk
   prints nothing and the agent silently falls back to guessing.
6. Prepends a one-line `SOURCE:` provenance banner to generated guides.

## Design rule: the agent can only go down one layer at a time, by `cat`

```
SYSTEM-PROMPT.txt  --cat-->  instruction  --cat-->  00_START_HERE_*  --cat-->  guide   (programs: run, never cat)
```

The agent has no search tool, so a file exists for it only if the layer it is **currently reading** names it
by its **exact filename** and it opens it with `bash cd /mnt/data && cat <file>`. Consequences:

- **Each layer must name the next one down.** The system prompt names the instruction file (as a `cat` command),
  the instruction names both START_HERE files, and each START_HERE routing row names its guide. A guide named
  only in the instruction file, or only inside another guide, is unreachable in practice: the start files say
  "cat only the ONE guide you need", so guide-to-guide mentions are not followed.
- **A "Read this when..." / description header inside a guide is inert.** It is visible only after the agent
  has already opened the guide. Do not write one, do not rely on one, leave existing ones alone.
- **The only trigger text that counts is the routing-table row** in `00_START_HERE_*.txt` (and the task-type
  keywords in the instruction's STEP 1). Write rows in the verbs and nouns of real requests ("read, dump,
  compare or delete ... script"), not abstract topic labels.
- **The start files must say how to open things** (`cd /mnt/data && cat <file>`) and forbid search tools;
  otherwise the agent may try enterprise search for a file name it was given.
- When adding a guide (new extra or upstream reference): add its routing row in the right START_HERE first,
  then the file. `verify` check E enforces the chain.

## Invariants to keep true (check by hand when editing templates)

These are the contradictions that bit before. `verify` catches the file/marker/script ones; the rest need eyes.

- **Instruction file is read first, so it must never contradict the START_HERE files.** Known past drift:
  - Java version: the sandbox is `-source 8` (confirmed on a live scheduler): no text blocks, `var`,
    `String.repeat()`, `isBlank()`, `List.of()`, reflection. The instruction's Java INPUT LISTS example must use
    `"A\n" + "B\n"` concatenation, never `"""`.
  - Rule count: instruction says "all six" Java rules; update the number if rules are added.
- **Every file named in a routing table exists** (`verify` check A). `sql-query-rules.txt` is generated for this
  reason; `job-definition-actions.txt` is bundled in `assets/extras/`.
- **Path convention:** START_HERE files use `cd /mnt/data &&`; the system prompt does too. Keep them identical.
- **Never open the big files.** The instruction must keep telling the agent to run, not read,
  `explore.py.txt`, `lookup.py.txt`, `build_model.py.txt`, `model.json.txt`, and to use no search tools for
  entities, getters or syntax.
- **HARD GATE vs START_HERE_SQL step 1:** the gate says run `find` for every domain term; the SQL start file
  says skip `find` when a cookbook row covers every noun. The gate wins in practice (an extra harmless
  command). Leave as is unless the user wants them aligned.
- **Business-term mapping** (Production Partition etc. -> P1111/P1112/P1113) appears in three files; change all
  three together.

## Verify only

```bash
python3 scripts/convert.py verify /path/to/data
```
Checks: (A) every `*.txt` named in the instruction/start files exists, and (E) the layer chain holds: system prompt `cat`s the instruction, the instruction names both START_HERE
files, and every guide/program is named in a START_HERE file; (B) no leftover `scripts/`, `assets/`,
`references/*.md`, `file:///` paths; (C) the awk line returns each cookbook section cleanly and the START_HERE
routing does not point past the last section; (D) every `explore.py.txt` / `lookup.py.txt` command written in
the routing tables, plus a `check` on a sample query, runs from inside the flat folder.

## Troubleshooting a deployed monolith

| Symptom | Likely cause |
| :-- | :-- |
| `model.json not found` | an un-patched script (still looks in `../assets/`); rebuild |
| awk returns nothing for a cookbook section | markers missing/renamed in `sql-cookbook.txt` |
| agent emits `"""` text blocks and the script fails to compile | instruction file's Java INPUT LISTS drifted back |
| agent says "Explorer run: not run" | instruction HARD GATE lines were edited; restore from template |
| agent tries to `cat model.json.txt` / use web search | the "run, never read" / "no search" lines were lost |
| `FileNotFoundError` on a guide | filename in a routing table has no file in `/mnt/data` |
| agent never opens a guide that exists | no START_HERE routing row names it (check E), or the row is too abstract to match the request |
