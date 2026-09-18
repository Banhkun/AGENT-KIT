# Redwood Object Query — ANSI SQL'92 Syntax & Rules

Essential rules and syntax nuances for writing queries against the RunMyJobs (Redwood) Object Query engine.

---

## 1. Query the Object Model, Not the Database

In RunMyJobs, SQL queries run against the **Scheduler Object Model**, NOT directly against the relational database tables.

- Table names in your query are **Entity Names** (`JobDefinition`, `JobChain`, `Job`, `Application`, `ObjectTag`).
- Physical database tables have underlying naming schemes that vary across versions and bypass Redwood security layers.

---

## 2. Reference Columns Store `UniqueId`, Not Text Names

This is the **most common mistake** in Redwood SQL.

Columns that link to other entities store the target entity's `UniqueId` (a numeric identifier), **not** the human-readable string name shown in the UI.

### Common Reference Columns:

| Entity          | Column                | Target Entity         | Why it matters                                      |
| :-------------- | :-------------------- | :-------------------- | :-------------------------------------------------- |
| `JobDefinition` | `Partition`           | `Partition`           | `jd.Partition = 'GLOBAL'` matches nothing!          |
| `JobDefinition` | `ParentApplication`   | `Application`         | `jd.ParentApplication = 'FINANCE'` matches nothing! |
| `JobDefinition` | `JobDefinitionType`   | `JobDefinitionType`   | `jd.JobDefinitionType = 'BASH'` matches nothing!    |
| `JobDefinition` | `LastModifierSubject` | `Subject`             | Must join `Subject` to filter by user               |
| `JobDefinition` | `DefaultQueue`        | `Queue`               | Must join `Queue` to filter by queue name           |
| `Job`           | `JobDefinition`       | `JobDefinition`       | Points to `JobDefinition.UniqueId`                  |
| `ObjectTag`     | `ObjectTagDefinition` | `ObjectTagDefinition` | Stores tag definition ID                            |
| `ObjectTag`     | `ObjectDefinition`    | `ObjectDefinition`    | Stores entity definition ID                         |

### Wrong vs Right Example:

```sql
-- ❌ WRONG: Fails or returns 0 rows because Partition is a UniqueId
SELECT jd.* FROM JobDefinition jd WHERE jd.Partition = 'GLOBAL'

-- ✔️ RIGHT: Join to Partition entity and filter on p.Name
SELECT jd.*
FROM JobDefinition jd
JOIN Partition p ON p.UniqueId = jd.Partition
WHERE p.Name = 'GLOBAL'
```

---

## 3. Wildcard Selects Must Be Alias-Qualified

Bare `SELECT *` is invalid in Redwood Object Query.

```sql
-- ❌ WRONG
SELECT * FROM JobDefinition

-- ✔️ RIGHT
SELECT jd.* FROM JobDefinition jd
```

When projecting specific columns, alias them clearly:

```sql
SELECT jd.Name AS JobName, p.Name AS PartitionName
FROM JobDefinition jd
JOIN Partition p ON p.UniqueId = jd.Partition
```

---

## 4. Master vs Branched Versions (`BranchedLLPVersion`)

Redwood supports versioning and draft branching for objects like `JobDefinition` and `JobChain`.

- `BranchedLLPVersion = -1`: The object is the active, committed, master version.
- `BranchedLLPVersion > -1`: The object is a working draft or branched variant.

Unless your intent is specifically to inspect uncommitted drafts:

```sql
WHERE jd.BranchedLLPVersion = -1
```

For `ObjectTag` and sibling resolution, also ensure you filter on:

```sql
WHERE jd.UniqueId = jd.MasterJobDefinition
```

This ensures queries do not return duplicate tags or sibling entries for intermediate branched records.

---

## 5. Joining Entities

All entity relationships in RunMyJobs join on `UniqueId`:

```sql
-- Linking Job Definition to its Parameters
FROM JobDefinition jd
JOIN JobDefinitionParameter jp ON jp.JobDefinition = jd.UniqueId

-- Linking Job Chain Call to Job Definition
FROM JobChainCall jcc
JOIN JobDefinition jd ON jcc.JobDefinition = jd.UniqueId
```

---

## 6. Date & Time Expressions

### Epoch Milliseconds

Date and time fields (e.g. `ScheduledStartTime`, `CreationTime`, `LastModificationTime`) are compared against epoch millisecond timestamps enclosed in single quotes:

```sql
WHERE j.ScheduledStartTime > '1773000000000'
```

### Built-in `NOW(...)` Function

Redwood's query engine supports relative date calculation using `NOW(...)`:

```sql
-- Modified in the last 30 days
WHERE jd.LastModificationTime > NOW('set hour 0 subtract 30 days')

-- Modified within the last year
WHERE jd.LastModificationTime > NOW('set hour 0 subtract 365 days')
```

---

## 7. String Searching & Case Sensitivity

- Use `LIKE '%term%'` for case-sensitive or database-collation-dependent matching.
- For case-insensitive searches where supported, use `LOWER(column) LIKE LOWER('%term%')`.
- Escape single quotes in string values by doubling them: `'O''Reilly'`.

---

## 8. No Scalar String Functions — Filtering by Length via `LIKE`

Redwood's Object Query engine does **not** support scalar SQL functions like `LENGTH()`, `SUBSTRING()`, `CHAR_LENGTH()`, etc. Attempting to use them fails ("length is not allowed").

To filter by the length of a string column (e.g. `jd.Comment`), use `LIKE` with underscore (`_`) wildcards, since each `_` matches exactly one character and `%` matches zero or more characters:

- **At least N characters:** `LIKE` a pattern of N underscores followed by `%`.
  ```sql
  -- Comment has at least 40 characters
  WHERE jd.Comment LIKE '________________________________________%'  -- 40 underscores + %
  ```
- **At most N characters:** `NOT LIKE` a pattern of (N+1) underscores followed by `%` — i.e. exclude anything with N+1 or more characters.
  ```sql
  -- Comment has at most 40 characters
  WHERE jd.Comment NOT LIKE '_________________________________________%'  -- 41 underscores + %
  ```
  Caution: if `jd.Comment` can be `NULL`, `NULL NOT LIKE anything` evaluates to unknown/false in most dialects, silently excluding those rows. Add `OR jd.Comment IS NULL` if nulls should count as satisfying "at most N".
- **Exactly N characters:** N underscores with **no** trailing `%` (a bare underscore pattern with no `%` must match the full string length exactly).
  ```sql
  WHERE jd.Comment LIKE '________________________________________'  -- exactly 40 characters
  ```
- **Range [N, M]:** combine both bounds.
  ```sql
  WHERE jd.Comment LIKE '__________%'              -- at least 10
  AND jd.Comment NOT LIKE '___________________________________________%'  -- at most 40 (41 underscores)
  ```

Tip: count underscores programmatically rather than by eye, e.g. `'_' * 40` in Python, to avoid off-by-one errors.

---

## 9. ORDER BY with Column Aliases (ORA-00918 Prevention)

When writing queries that project specific column aliases (e.g. `SELECT jd.Name AS JobDefinitionName`) across joined entities (such as `JobDefinition` and `JobDefinitionParameter`, both of which have a `Name` column):

- Always use the **column alias** in the `ORDER BY` clause, **not** the table-qualified column name or bare column name.
- If you order by `jd.Name` or `Name` when multiple tables share that column name, Redwood's underlying SQL query translator produces an Oracle ambiguity error:
  `JCS-122035: Unable to persist: JCS-XXXXX: @locale2@:(com.redwood.scheduler.exception.Class.persistence.api.PersistenceException$RecoveryFailedException 'ORA-00918: column ambiguously defined')`

### Wrong vs Right Example:

```sql
-- ❌ WRONG: Causes ORA-00918 in Oracle
SELECT jd.Name AS JobDefinitionName, jp.Name AS ParameterName
FROM JobDefinition jd
JOIN JobDefinitionParameter jp ON jd.UniqueId = jp.JobDefinition
WHERE jd.BranchedLLPVersion = -1
ORDER BY jd.Name, jp.Name

-- ✔️ RIGHT: Reference the projected column aliases
SELECT jd.Name AS JobDefinitionName, jp.Name AS ParameterName
FROM JobDefinition jd
JOIN JobDefinitionParameter jp ON jd.UniqueId = jp.JobDefinition
WHERE jd.BranchedLLPVersion = -1
ORDER BY JobDefinitionName, ParameterName
```

---

## 10. Query Validation Checklist

Before executing an Object Query, verify:

- [ ] Are all wildcards alias-qualified (e.g. `jd.*`)?
- [ ] Are reference columns (`Partition`, `ParentApplication`, `JobDefinitionType`) properly joined instead of compared directly to text?
- [ ] Is `BranchedLLPVersion = -1` specified on `JobDefinition` / `JobChain`?
- [ ] Are joins matching on `.UniqueId`?
- [ ] If querying `ObjectTag` on `JobDefinition`, is `UniqueId = MasterJobDefinition` included?
- [ ] Are `ORDER BY` clauses using output column aliases (e.g. `ORDER BY JobDefinitionName`) instead of table-qualified column names when projection aliases are defined (prevents `ORA-00918`)?
- [ ] Are any string-length filters using `LIKE '____%'` underscore patterns instead of unsupported functions like `LENGTH()`?
