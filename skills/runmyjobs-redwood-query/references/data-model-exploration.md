# Automated Data Model Exploration

Guide to using `scripts/explore.py` to explore the 462 Redwood entities, trace relationship graphs, and generate joins.

---

## The "Bundle and Query" Architecture

In accordance with the repository rule `large_data_models.md`, the entire schema is bundled offline in `assets/model.json` (462 entities, thousands of fields, reverse references).

**Never attempt to dump or read `model.json` directly into your context window.** Instead, invoke `scripts/explore.py` via CLI to extract only the relevant slice needed for the query.

---

## Exploration Commands

### 1. Inspect Entity Details
Inspect all fields, data types, and highlight **Reference Columns** (foreign keys that store `UniqueId`):
```bash
python scripts/explore.py inspect JobDefinition
```
**Output highlights:**
- Reference columns (e.g. `Partition -> Partition.UniqueId`, `ParentApplication -> Application.UniqueId`)
- Scalar columns directly filterable in `WHERE` clauses
- Other entities pointing at this entity (reverse references)

### 2. Auto-Generate ANSI SQL Joins
To join two entities where you don't know the intermediate tables:
```bash
python scripts/explore.py join JobDefinition JobChain
```
**Output:**
```sql
-- ANSI JOIN Syntax:
SELECT jd.*
FROM JobDefinition jd
JOIN JobChain jc
     ON jc.JobDefinition = jd.UniqueId
WHERE jd.BranchedLLPVersion = -1
```

For traversing from step job definitions to parent chains:
```bash
python scripts/explore.py join JobDefinition JobChainCall
```

### 3. Find Relationship Paths
Find multi-hop connection paths through the entity graph:
```bash
python scripts/explore.py path JobDefinition Script --limit 3
```

### 4. Search Entities and Fields
Search entity names and field names by wildcard or pattern:
```bash
python scripts/explore.py find chain
python scripts/explore.py find tag
```

### 5. Find Which Entity Carries a Specific Field
```bash
python scripts/explore.py field KeepAmount
python scripts/explore.py field DefaultExpression
```

### 6. Lint and Validate SQL Queries
Before running a complex query, run it through the linter:
```bash
python scripts/explore.py check "SELECT jd.* FROM JobDefinition jd WHERE jd.Partition = 'GLOBAL'"
```
**Detected Issues:**
- Direct string comparison against reference columns (`Partition`, `ParentApplication`, etc.)
- Missing `BranchedLLPVersion = -1`
- Bare `SELECT *` without alias qualification
- Joins not referencing `.UniqueId`
