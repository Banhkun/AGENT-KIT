# RunMyJobs Query Cookbook

Ready-to-use canonical SQL queries against the RunMyJobs (Redwood) Object Model.
These patterns are directly compatible with the Redwood Support Query Console, SQL Query Web UI,
and `jcsSession.executeObjectQuery(...)` / `jcsSession.executeQuery(...)`.

---

## Table of Contents
1. [Search For Use (Find Parent Chains)](#1-search-for-use-find-parent-chains)
2. [List Steps in Job Chains](#2-list-steps-in-job-chains)
3. [RMJ ⇄ UC4 Name Lookup](#3-rmj--uc4-name-lookup)
4. [Find Siblings (Shared UC4 Tag)](#4-find-siblings-shared-uc4-tag)
5. [Search Content (Parameters & Script Source)](#5-search-content-parameters--script-source)
6. [List Parameters](#6-list-parameters)
7. [Retention Audit & Configuration](#7-retention-audit--configuration)
8. [Folder / Application Hierarchy](#8-folder--application-hierarchy)
9. [Job Execution Status & History](#9-job-execution-status--history)

---

## 1. Search For Use (Find Parent Chains)

**Intent**: Given one or more child `JobDefinition` names, find every parent `JobChain` that includes them as a step.

### Canonical Query
```sql
SELECT DISTINCT jd.Name AS JobDefinitionName,
       jd1.Name AS ParentChainName
FROM JobDefinition jd
JOIN JobChainCall jcc
     ON jcc.JobDefinition = jd.UniqueId
JOIN JobChainStep jcs
     ON jcc.JobChainStep = jcs.UniqueId
JOIN JobChain jc
     ON jcs.JobChain = jc.UniqueId
JOIN JobDefinition jd1
     ON jc.JobDefinition = jd1.UniqueId
WHERE jd.Name IN ('SAP_SD_ORDER_EXTRACT', 'SAP_MM_INVOICE_POST')
  AND jd.BranchedLLPVersion = -1
  AND jd1.BranchedLLPVersion = -1
ORDER BY JobDefinitionName, ParentChainName
```

### Key Considerations
- `JobChainCall` links a `JobDefinition` to a `JobChainStep`.
- `JobChain` also has its own outer `JobDefinition` (`jd1`), which represents the chain definition itself.
- `BranchedLLPVersion = -1` guarantees you only query approved master definitions, filtering out unpublished drafts.

---

## 2. List Steps in Job Chains

**Intent**: Given one or more parent `JobChain` names, return all steps, their sequence numbers, target job definitions, restart configurations, and status handlers.

### Canonical Query
```sql
SELECT jcd.Partition AS PartitionName,
       jcd.Name AS ChainName,
       jcs.SequenceNumber,
       jd.Name AS StepJobName,
       jcss.Action AS StatusAction,
       jcs.RestartCount,
       jcs.RestartDelayAmount,
       jcs.RestartDelayUnits
FROM JobChain jc
JOIN JobDefinition jcd
     ON jcd.UniqueId = jc.JobDefinition
JOIN JobChainStep jcs
     ON jcs.JobChain = jc.UniqueId
LEFT JOIN JobChainStepStatusHandler jcss
     ON jcs.UniqueId = jcss.JobChainStep
JOIN JobChainCall jcc
     ON jcc.JobChainStep = jcs.UniqueId
JOIN JobDefinition jd
     ON jcc.JobDefinition = jd.UniqueId
WHERE jcd.Name IN ('NIGHTLY_BILLING_CHAIN', 'DAILY_INVENTORY_CHAIN')
  AND jcd.BranchedLLPVersion = -1
  AND jd.BranchedLLPVersion = -1
ORDER BY ChainName, jcs.SequenceNumber
```

### Notes
- `LEFT JOIN` on `JobChainStepStatusHandler` preserves steps that use default error handling.
- `jcs.SequenceNumber` orders execution order inside the chain.

---

## 3. RMJ ⇄ UC4 Name Lookup

**Intent**: Cross-reference RunMyJobs JobDefinitions with their legacy UC4 object names via `ObjectTag`.

### Direction A: RMJ → UC4
Find the UC4 tag for specific RMJ JobDefinitions:
```sql
SELECT jd.Name        AS RMJName,
       jd.Partition   AS PartitionName,
       ot.Value       AS FullTagValue
FROM JobDefinition jd
JOIN ObjectTag ot
     ON ot.RefUniqueId = jd.UniqueId
JOIN ObjectTagDefinition otd
     ON otd.UniqueId = ot.ObjectTagDefinition
JOIN ObjectDefinition od
     ON od.UniqueId = ot.ObjectDefinition
WHERE otd.Name = 'UC4ExternalBusinessKey'
  AND od.ObjectName = 'JobDefinition'
  AND jd.UniqueId = jd.MasterJobDefinition
  AND jd.Name IN ('JOB_FIN_001', 'JOB_HR_002')
```

### Direction B: UC4 → RMJ
Find RMJ JobDefinitions matching UC4 object names (mirrors `%, <UC4Name>` convention):
```sql
SELECT jd.Name        AS RMJName,
       jd.Partition   AS PartitionName,
       ot.Value       AS FullTagValue
FROM JobDefinition jd
JOIN ObjectTag ot
     ON ot.RefUniqueId = jd.UniqueId
JOIN ObjectTagDefinition otd
     ON otd.UniqueId = ot.ObjectTagDefinition
JOIN ObjectDefinition od
     ON od.UniqueId = ot.ObjectDefinition
WHERE otd.Name = 'UC4ExternalBusinessKey'
  AND od.ObjectName = 'JobDefinition'
  AND jd.UniqueId = jd.MasterJobDefinition
  AND (ot.Value LIKE '%, UC4_EXTRACT_JOB'
    OR ot.Value LIKE '%, UC4_POST_JOB')
```

### Tag Format
- UC4 tags are structured as `Client, ParentName, JobName` or similar comma-separated triples.
- `jd.UniqueId = jd.MasterJobDefinition` ensures you target the master object instead of variants/branches.

---

## 4. Find Siblings (Shared UC4 Tag)

**Intent**: Find twin or split JobDefinitions that share the exact same `UC4ExternalBusinessKey` tag value.

### Canonical Query
```sql
SELECT src.Name       AS SourceRMJName,
       sib.Name       AS SiblingRMJName,
       sib.Partition  AS SiblingPartition,
       ot2.Value      AS SiblingFullTagValue
FROM JobDefinition src
JOIN ObjectTag ot1
     ON ot1.RefUniqueId = src.UniqueId
JOIN ObjectTagDefinition otd1
     ON otd1.UniqueId = ot1.ObjectTagDefinition
JOIN ObjectDefinition od1
     ON od1.UniqueId = ot1.ObjectDefinition
JOIN ObjectTag ot2
     ON ot2.ObjectTagDefinition = ot1.ObjectTagDefinition
    AND ot2.ObjectDefinition = ot1.ObjectDefinition
    AND ot2.Value = ot1.Value
JOIN JobDefinition sib
     ON sib.UniqueId = ot2.RefUniqueId
    AND sib.UniqueId = sib.MasterJobDefinition
WHERE otd1.Name = 'UC4ExternalBusinessKey'
  AND od1.ObjectName = 'JobDefinition'
  AND src.UniqueId = src.MasterJobDefinition
  AND sib.UniqueId <> src.UniqueId
  AND src.Name IN ('SOURCE_SPLIT_JOB_A')
```

---

## 5. Search Content (Parameters & Script Source)

**Intent**: Search text across parameter default values and/or script source code for matching strings.

### Canonical Query (Combined with UNION ALL)
```sql
-- 1. Search in Parameter Defaults
SELECT 'Parameter'          AS MatchSource,
       jd.Partition          AS PartitionName,
       jd.Name               AS JobDefinitionName,
       jp.Name               AS DetailName,
       jp.DefaultExpression  AS MatchText,
       1                     AS MatchOccurrence
FROM JobDefinitionParameter jp
JOIN JobDefinition jd
     ON jd.UniqueId = jp.JobDefinition
WHERE jd.BranchedLLPVersion = -1
  AND jp.DefaultExpression <> ' '
  AND (jp.DefaultExpression LIKE '%/apps/data/finance%'
    OR jp.DefaultExpression LIKE '%ORA-12154%')

UNION ALL

-- 2. Search in Script Lines
SELECT 'Script'              AS MatchSource,
       jd.Partition          AS PartitionName,
       jd.Name               AS JobDefinitionName,
       jdt.Name              AS DetailName,
       sl.LineText           AS MatchText,
       COUNT(*)              AS MatchOccurrence
FROM JobDefinition jd,
     JobDefinitionType jdt,
     Script s,
     ScriptSourceLine sl,
     ScriptSourceLine sl2
WHERE jd.JobDefinitionType = jdt.UniqueId
  AND jd.UniqueId = s.JobDefinition
  AND jdt.Name IN ('JDBC', 'BASH', 'CMD', 'RedwoodScript', 'CSH', 'KSH', 'SQLPLUS', 'PERL')
  AND jd.BranchedLLPVersion = -1
  AND s.UniqueId = sl.Script
  AND jd.LastModificationTime > NOW('set hour 0 subtract 365 days')
  AND (sl.LineText LIKE '%/apps/data/finance%' OR sl.LineText LIKE '%ORA-12154%')
  AND sl2.Script = sl.Script
  AND (sl2.LineText LIKE '%/apps/data/finance%' OR sl2.LineText LIKE '%ORA-12154%')
  AND sl2.LineNumber <= sl.LineNumber
GROUP BY jd.UniqueId, jdt.Name, jd.Name, jd.Partition, jd.CreationTime, s.RunAsUser, s.RemoteRunAsUser, sl.LineText, sl.LineNumber
ORDER BY JobDefinitionName, MatchSource
```

---

## 6. List Parameters

**Intent**: Inspect parameter names and their default expressions across JobDefinitions.

### Canonical Query
```sql
SELECT jd.Name               AS JobDefinitionName,
       jd.Partition          AS PartitionName,
       jp.Name               AS ParameterName,
       jp.DefaultExpression  AS Value
FROM JobDefinitionParameter jp
JOIN JobDefinition jd
     ON jd.UniqueId = jp.JobDefinition
WHERE jd.Name IN ('JOB_SAP_REPORT', 'JOB_DB_CLEANUP')
  AND jp.Name IN ('ENV', 'DATABASE_NAME', 'OUTPUT_PATH')
  AND jd.BranchedLLPVersion = -1
ORDER BY JobDefinitionName, ParameterName
```

---

## 7. Retention Audit & Configuration

**Intent**: Audit retention settings (`KeepAmount`, `KeepType`, `KeepUnits`, status retention) and last modifier.

### Canonical Query
```sql
SELECT jd.Partition         AS PartitionName,
       jd.Name              AS Name,
       jd.KeepAmount        AS KeepAmount,
       jd.KeepType          AS KeepType,
       jd.KeepUnits         AS KeepUnits,
       jd.KeepInStatusAmount AS KeepInStatusAmount,
       jd.KeepInStatusUnit  AS KeepInStatusUnit,
       jd.KeepJobsInStatus  AS KeepJobsInStatus,
       s.Name               AS LastModifier
FROM JobDefinition jd
LEFT JOIN Subject s
     ON s.UniqueId = jd.LastModifierSubject
WHERE jd.BranchedLLPVersion = -1
  AND jd.Name IN ('JOB_RETAIN_30_DAYS', 'JOB_LOG_ROTATE')
```

---

## 8. Folder / Application Hierarchy

**Intent**: Preview or audit the Application folder and Partition of JobDefinitions.

### Canonical Query
```sql
SELECT jd.Name               AS JobDefinitionName,
       p.Name                AS PartitionName,
       app.Name              AS ApplicationName
FROM JobDefinition jd
JOIN Partition p
     ON p.UniqueId = jd.Partition
LEFT JOIN Application app
     ON app.UniqueId = jd.ParentApplication
WHERE jd.Name IN ('JOB_EXTRACT_DATA', 'JOB_LOAD_WAREHOUSE')
  AND jd.BranchedLLPVersion = -1
```

> [!TIP]
> Notice how `Partition` and `ParentApplication` are joined with `Partition p` and `Application app` on `.UniqueId`. In Redwood, these reference columns store numeric IDs, so joining to the target table is required to display or filter on human-readable names.
