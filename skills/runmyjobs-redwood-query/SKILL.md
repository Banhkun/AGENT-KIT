---
name: runmyjobs-redwood-query
description: >-
  Explores the RunMyJobs (Redwood) Data Model and builds ANSI SQL'92 Object Queries for the Redwood
  scheduler. Use this skill whenever searching, querying, inspecting, reporting, or analyzing Redwood
  objects including JobDefinitions, JobChains, JobChainSteps, JobChainCalls, parameters, script source code,
  retention policies, folder applications, and UC4 ⇄ RMJ mappings (UC4ExternalBusinessKey, sibling lookups).
  Always trigger this skill when the user asks for Redwood SQL queries, Object Queries, search-for-use,
  chain step listings, parameter matrices, or asks how entities connect in the Redwood schema.
---

# RunMyJobs (Redwood) Data Model & Object Query Guide

Skill for **exploring the Redwood Data Model** and **crafting ANSI SQL'92 Object Queries** against the RunMyJobs scheduler.

This skill bundles:
- `scripts/explore.py`: Automated CLI explorer and SQL join generator.
- `assets/model.json`: Complete dump of all 462 Redwood entities, fields, and relationships.
- `references/`: Canonical recipes and syntax guides.

> [!IMPORTANT]
> **Adhere to the "Bundle and Query, Don't Inline" Rule**:
> Never load `assets/model.json` directly into context. It contains hundreds of classes and thousands of lines. Run `scripts/explore.py` via CLI to inspect entities and generate joins dynamically on-demand.

---

## Non-Negotiable Rules

1. **Reference columns hold `UniqueId`, not names.**
   `Partition`, `ParentApplication`, `JobDefinitionType`, and `LastModifierSubject` store numeric IDs.
   - ❌ WRONG: `WHERE jd.Partition = 'P1112'` (silently returns 0 rows).
   - ✔️ RIGHT: `JOIN Partition p ON p.UniqueId = jd.Partition WHERE p.Name = 'P1112'`.
2. **Always filter `BranchedLLPVersion = -1`** on versioned entities (`JobDefinition`, `JobChain`) to target active, committed master definitions rather than draft revisions.
3. **Always alias-qualify wildcards:** `SELECT jd.* FROM JobDefinition jd` (bare `SELECT *` is rejected).
4. **All entity joins must connect via `UniqueId`** (e.g. `JOIN JobChainCall jcc ON jcc.JobDefinition = jd.UniqueId`).
5. **Add `jd.UniqueId = jd.MasterJobDefinition`** when querying `ObjectTag` or resolving siblings to prevent duplicate rows across split/branched variants.
6. **No scalar string functions (`LENGTH()`, `SUBSTRING()`, etc.) are supported.** To filter by string length, use `LIKE` with underscore wildcards instead:
   - At least N chars: `LIKE` N underscores + `%` (e.g. `LIKE '__________%'` for ≥10).
   - At most N chars: `NOT LIKE` (N+1) underscores + `%` (watch for `NULL` rows being excluded).
   - Exactly N chars: N underscores with no trailing `%`.
   See [SQL Syntax & Rules §8](file:///references/sql-syntax-and-rules.md#8-no-scalar-string-functions--filtering-by-length-via-like) for details.
7. **Order by output column aliases when using `SELECT ... AS alias` with JOINs:**
   When projecting columns with aliases across multiple joined tables (especially columns like `Name` present in multiple entities), ordering by the raw column reference (e.g. `ORDER BY jd.Name` or `ORDER BY Name`) causes Redwood's underlying SQL generator to produce ambiguous SQL in Oracle:
   `JCS-122035: Unable to persist: ORA-00918: column ambiguously defined`.
   - ❌ WRONG: `SELECT jd.Name AS JobDefinitionName ... ORDER BY jd.Name`
   - ✔️ RIGHT: `SELECT jd.Name AS JobDefinitionName ... ORDER BY JobDefinitionName`


---

## Routing & Query Index

| Task / Query Intent | Canonical Query Pattern | Exploration Command | Reference |
| :--- | :--- | :--- | :--- |
| **Search For Use** (Find parent chains containing a job) | `JobDefinition jd` → `JobChainCall jcc` → `JobChainStep jcs` → `JobChain jc` → `JobDefinition parent` | `python scripts/explore.py path JobDefinition JobChain` | [Cookbook: Search For Use](file:///references/query-cookbook.md#1-search-for-use-find-parent-chains) |
| **List Steps** (Step jobs, sequence, restart, status actions) | `JobChain jc` → `JobChainStep jcs` → `JobChainCall jcc` → `JobDefinition jd` + status handler | `python scripts/explore.py inspect JobChainStep` | [Cookbook: List Steps](file:///references/query-cookbook.md#2-list-steps-in-job-chains) |
| **RMJ ⇄ UC4 Lookup** (Bidirectional name mapping) | `JobDefinition` → `ObjectTag` (`otd.Name = 'UC4ExternalBusinessKey'`) | `python scripts/explore.py path JobDefinition ObjectTag` | [Cookbook: RMJ ⇄ UC4](file:///references/query-cookbook.md#3-rmj--uc4-name-lookup) |
| **Find Siblings** (Jobs sharing same UC4 tag / split objects) | `src (JobDefinition)` → `ot1` → `ot2` (same tag value) → `sib (JobDefinition)` | `python scripts/explore.py inspect ObjectTag` | [Cookbook: Find Siblings](file:///references/query-cookbook.md#4-find-siblings-shared-uc4-tag) |
| **Search Content** (Search parameter defaults & script lines) | `UNION ALL` of `JobDefinitionParameter` + (`JobDefinition` + `Script` + `ScriptSourceLine`) | `python scripts/explore.py join JobDefinition Script` | [Cookbook: Search Content](file:///references/query-cookbook.md#5-search-content-parameters--script-source) |
| **List Parameters** (Matrix or tabular parameter dump) | `JobDefinitionParameter jp` joined with `JobDefinition jd` | `python scripts/explore.py inspect JobDefinitionParameter` | [Cookbook: List Parameters](file:///references/query-cookbook.md#6-list-parameters) |
| **Retention Policy Audit** | Audit `KeepAmount`, `KeepType`, `KeepUnits`, joined with modifier `Subject` | `python scripts/explore.py field KeepAmount` | [Cookbook: Retention](file:///references/query-cookbook.md#7-retention-audit--configuration) |
| **Folder / Application Hierarchy** | `ParentApplication` and `Partition` resolution via `UniqueId` | `python scripts/explore.py inspect JobDefinition` | [Cookbook: Folder Hierarchy](file:///references/query-cookbook.md#8-folder--application-hierarchy) |
| **Connecting Unknown Entities** | Dynamic path search across all 462 entities | `python scripts/explore.py path <Start> <End>` | [Data Model Exploration](file:///references/data-model-exploration.md) |
| **Syntax, Functions, Dialect** | ANSI SQL'92 dialect, epoch dates, `NOW(...)`, joins | `python scripts/explore.py check "<SQL>"` | [SQL Syntax & Rules](file:///references/sql-syntax-and-rules.md) |
| **Running in Java / Web UI** | Support Query Console, `executeObjectQuery`, `executeQuery` | N/A | [Execution Modes](file:///references/execution-modes.md) |

---

## Standard Workflow

When asked to write or optimize a RunMyJobs query:

1. **Check if a canonical pattern exists** in [query-cookbook.md](file:///references/query-cookbook.md).
2. **If connecting unfamiliar entities, auto-explore**:
   - Run `python scripts/explore.py path <StartEntity> <EndEntity>` to find the join path.
   - Run `python scripts/explore.py join <StartEntity> <EndEntity>` to get the starter join syntax.
   - Run `python scripts/explore.py inspect <Entity>` to check whether fields are references (requiring a join) or scalars.
3. **Verify against the Non-Negotiable Rules**:
   - Run `python scripts/explore.py check "<Your SQL>"` to lint for reference column traps or missing version filters.
4. **Choose Execution Mode**:
   - Pure SQL for the Redwood Web UI / Support Console.
   - `jcsSession.executeObjectQuery(...)` if iterating full entity objects in Java.
   - `jcsSession.executeQuery(sql, params, callback)` if extracting tabular projections or aggregates.
