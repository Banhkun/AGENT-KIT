---
name: runmyjobs-redwood-script
description: >-
  Extracts and guides how Java (RedwoodScript) code interacts with the RunMyJobs (Redwood) Data Model.
  Use this skill whenever reading, writing, querying, updating, or debugging Java code that interacts with
  RunMyJobs / Redwood objects, SchedulerSession (jcsSession), Object Queries, JobDefinitions, JobChains,
  parameters, tables, transaction persistence, and UC4 to RMJ ObjectTag correspondence (UC4ExternalBusinessKey).
---

# RunMyJobs (Redwood) Data Model — Java Interaction Guide

Router skill for **writing** RedwoodScript. The code in these references is not executable
here — RedwoodScript runs inside the Redwood scheduler. Treat every example as a template to
adapt into the answer, never as something to run.

Read only the reference the current task needs. Do not load all six.

This skill also bundles `scripts/lookup.py` and `assets/model.json` — a real dump of the
Redwood Data Model (462 entities, their fields, and ~600 `SchedulerSession` lookup/creation
methods). Run the script; never load `model.json` into context directly, it's too large to
be worth reading in full.

## Default code shape: function-oriented bare script

Default to a standalone `{ ... }` script body, not a compiled class extending `*Stub`. For
reusable or multi-line helper logic inside that block, use one of:

- **A local (non-static) class**, defined at the top of the block, for anything with several
  parameters, a `throws Exception`, or recursion. Its instance methods capture `jcsSession`,
  `jcsOut`, and `jcsErr` directly from the enclosing block — no need to pass them in.
- **A lambda** (`Function`, `BiFunction`, `Consumer`, `Predicate`) for short, single-expression
  helpers such as a lookup-and-validate.

Only reach for a compiled `JobDefinition_*` class extending `*Stub` when the code specifically
must live in a compiled Job Definition's class body rather than a Shell/ad-hoc script — that
shape still exists and is documented in `references/runtime-and-shapes.md`, but it is the
exception here, not the default.

## Non-negotiable rules

These four cause the majority of failures. Apply them to anything written, before consulting
any reference.

1. **Query the Object Model, never the database.** Use `jcsSession.executeObjectQuery(...)`
   against entity names (`Job`, `JobDefinition`, `ObjectTag`). Underlying DB table and column
   names are unstable and bypass security contexts.
2. **Trim every string before persisting.** Redwood rejects any string attribute ending in
   whitespace; `jcsSession.persist()` throws. `String safe = raw != null ? raw.trim() : "";`
3. **Nothing is saved until `persist()`.** Guard with
   `if (jcsSession.hasDirtyObjects()) jcsSession.persist();` and call `jcsSession.reset()`
   in catch/cleanup blocks.
4. **Verify type strings, never infer them from names.** A job named `JSAP_XOE_011_...` has
   `getJobDefinitionType().getName()` of `"SAPR3"`. Print the real value for a sample object
   before filtering on it.

## Routing

| If the task involves…                                                                            | Read                                     |
| :----------------------------------------------------------------------------------------------- | :--------------------------------------- |
| Which globals exist (`jcsSession`, `jcsJob`, `jcsOut`); the bare-script vs. compiled-class shape | `references/runtime-and-shapes.md`       |
| Choosing an entity, finding a getter, resolving an object by name or UniqueId                    | `scripts/lookup.py` (see `references/entities-and-lookup.md`) |
| Writing a query: joins, status codes, time cutoffs, duplicate rows, bind parameters              | `references/object-queries.md`           |
| Submitting jobs, setting parameters, building or traversing chains, Redwood tables               | `references/job-and-chain-operations.md` |
| UC4 ↔ RMJ correlation, `UC4ExternalBusinessKey`, split objects, master vs branched               | `references/uc4-object-tags.md`          |
| An error, or an empty/wrong result set to diagnose                                               | `references/troubleshooting.md`          |

## Workflow

1. **Default to the bare-script shape** unless context makes clear the code must live inside a
   compiled Job Definition class body. See `references/runtime-and-shapes.md` for both shapes
   and when the compiled-class one actually applies.
2. **Before calling any getter/creator you haven't used in this conversation, check it's
   real.** Run `python scripts/lookup.py session <Entity>` (how to get/create one) and
   `python scripts/lookup.py class <Entity>` (what it has once you have one) against the
   bundled data-model dump rather than recalling a method name from memory — see
   `references/entities-and-lookup.md`. This is what replaces guessing.
3. **Confirm the partition and object names exist** before writing logic around them. Every
   `get*ByName` returns `null` when not found.
4. **Adapt the nearest example** from the matching reference rather than composing from
   scratch. Each reference holds one canonical, complete version of its patterns, already in
   the bare-script + local-class/lambda form.
5. **Apply the four rules above** to whatever gets written.
6. **When a query returns 0 rows or a filter misses,** consult
   `references/troubleshooting.md` before rewriting the logic — the cause is usually listed
   there, and it is usually an assumption about a string value that was never printed.

## Writing guidance

- Default to a bare `{ ... }` script. Use a local (non-static) class for reusable or recursive
  helper logic, and lambdas for short single-expression helpers. Reach for a compiled
  `*Stub`-extending class only when the target genuinely is a compiled Job Definition body.
- Static members inside a local class require Java 16+. Unless the Redwood scheduler's JDK
  version is known, use instance methods and let them capture `jcsSession`/`jcsOut` from the
  enclosing block instead of declaring them `static`.
- Prefer bind parameters (`?` with an `Object[]`) over string concatenation whenever a value
  reaches the query from a Job Definition parameter or any caller-supplied source.
- Null-check every lookup and every `getJobParameterByName` result; undeclared names return
  `null` rather than throwing.
- Guard chain traversal with a `visited` set — Redwood chains can reference each other
  cyclically. A local class's instance methods can recurse directly; an explicit `Deque` is
  only needed as a manual stack if recursion depth becomes a concern.
