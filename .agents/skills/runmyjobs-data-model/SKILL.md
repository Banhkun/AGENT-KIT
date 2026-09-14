---
name: runmyjobs-data-model
description: >-
  Extracts and guides how Java (RedwoodScript) code interacts with the RunMyJobs (Redwood) Data Model.
  Use this skill whenever reading, writing, querying, updating, or debugging Java code that interacts with
  RunMyJobs / Redwood objects, SchedulerSession (jcsSession), Object Queries, JobDefinitions, JobChains,
  parameters, tables, transaction persistence, and UC4 <-> RMJ ObjectTag correspondence (UC4ExternalBusinessKey).
---

# RunMyJobs (Redwood) Data Model Java Interaction Guide

This skill provides patterns, API guidelines, query structures, and best practices for writing Java code (RedwoodScript) that interacts with the RunMyJobs (RMJ) Data Model, including UC4-to-RMJ object correlation via Object Tags.

For complete entity tables and query recipes, see the [Data Model Reference](./references/data_model_reference.md).

---

## 1. Runtime Environment & Predefined Variables

RedwoodScript executes within a managed Java runtime with predefined global variables automatically injected into the script context:

| Variable | Class | Purpose |
| :--- | :--- | :--- |
| `jcsSession` | `SchedulerSession` | Primary API session: querying, object lookup, factory creation, and transaction management (`persist()`, `reset()`). |
| `jcsJob` | `Job` | The currently running `Job` execution instance in Redwood. |
| `jcsOut` | `PrintStream` | Redwood standard output log stream (visible in Redwood UI / stdout log). |
| `jcsErr` | `PrintStream` | Redwood standard error log stream (visible in Redwood UI / stderr log). |
| Script Parameters | *Typed objects* | Defined on the Job Definition (e.g. `pWorkflowName`, `pPeriod`, `pCommit`), accessible directly by name. |

---

## 2. Querying the Data Model (`executeObjectQuery`)

### Critical Rule: Query the Data Model, NOT Database Tables
Always query the Redwood Object Model using ANSI '92 SQL subset via `jcsSession`. Never attempt to query underlying database tables directly (table names and column names are unstable and lack security contexts).

### Query Execution Signatures
```java
// 1. Untyped Iterator (most common)
String q = "select j.* from Job j where j.Status in ('E', 'C', 'W') and j.ParentJob is null";
for (Iterator it = jcsSession.executeObjectQuery(q, null); it.hasNext();) {
  Job j = (Job) it.next();
  // process job
}

// 2. Typed RWIterable
String sql = "select t.* from Table t where t.Name = 'CT_CONFIG'";
for (Table tb : jcsSession.executeObjectQuery(Table.TYPE, sql, null)) {
  // process table
}
```

### Essential Query Clauses & Joins
1. **Joins via `UniqueId`**:
   Object relationships are joined on `UniqueId` rather than arbitrary foreign keys:
   ```sql
   select j.* 
   from Job j, JobDefinition jd, Application a 
   where (j.JobDefinition = jd.UniqueId)
     and (jd.ParentApplication = a.UniqueId and a.Name like '%FINANCE%')
     and (j.JobChainStep is null)
     and j.Status in ('E', 'C', 'W')
     and j.ScheduledStartTime > '1773000000000'
   order by j.JobId desc
   ```

2. **Job Status Filter**:
   - `'C'`: Completed
   - `'E'`: Error
   - `'W'`: Waiting
   - `'Q'`: Queued
   - `'R'`: Running
   - `'S'`: Scheduled
   - `'X'`: Killed / Canceled

3. **Top-Level vs Child / Step Jobs**:
   - `j.ParentJob is null`: Excludes child jobs spawned by parent jobs.
   - `j.JobChainStep is null`: Excludes job executions that run as steps inside a Job Chain.

4. **Time Window & Cutoff Queries**:
   Redwood Object Query accepts epoch millisecond timestamps in single quotes for `ScheduledStartTime`:
   ```java
   Instant cutoff = Instant.now().minus(24, ChronoUnit.HOURS).truncatedTo(ChronoUnit.SECONDS);
   String cutoffEpoch = String.valueOf(cutoff.toEpochMilli());
   String q = "select j.* from Job j where j.ScheduledStartTime > '" + cutoffEpoch + "'";
   ```

5. **Safe Deduplication Pattern**:
   When joining multiple tables, duplicate rows can occur. Deduplicate using a composite key:
   ```java
   Set<String> seen = new HashSet<>();
   for (Iterator it = jcsSession.executeObjectQuery(q, null); it.hasNext();) {
     Job j = (Job) it.next();
     String dedupKey = j.getJobDefinition().getUniqueId() + "|" + j.getCreationTime();
     if (!seen.add(dedupKey)) {
       continue; // skip duplicate row
     }
     // process distinct job
   }
   ```

---

## 3. Object Lookup Methods on `jcsSession`

### Lookup by Name & Partition
Most configuration objects belong to a `Partition` (e.g. `GLOBAL` or tenant-specific):
```java
Partition global = jcsSession.getPartitionByName("GLOBAL");
Partition projectPart = jcsSession.getPartitionByName("P1113");

JobDefinition jd = jcsSession.getJobDefinitionByName(projectPart, "MY_JOB_DEF");
Queue queue = jcsSession.getQueueByName(projectPart, "SAP_BATCH_QUEUE");
Table table = jcsSession.getTableByName(projectPart, "MY_LOOKUP_TABLE");
TimeWindow tw = jcsSession.getTimeWindowByName(global, "TW_WORKING_HOURS");
ObjectTagDefinition uc4TagDef = jcsSession.getObjectTagDefinitionByName(global, "UC4ExternalBusinessKey");
```

### Lookup by UniqueId / JobId
```java
Job job = jcsSession.getJobByJobId(1234567L);
JobDefinition jd = jcsSession.getJobDefinitionByUniqueId(987654L);
Alert alert = jcsSession.getAlertByUniqueId(555123L);
SchedulerEntity se = jcsSession.getSchedulerEntityByObjectTypeUniqueId("JobDefinition", uniqueId);
```

---

## 4. Job Submission & Manipulation

### Preparing and Submitting a Job
```java
// 1. Prepare job instance from definition
JobDefinition jd = jcsSession.getJobDefinitionByName(partition, "System_Mail_Send");
Job job = jd.prepare();

// 2. Set queue, description, and status
job.setQueue(targetQueue);
job.setDescription("Automated notification job");

// 3. Set input parameters
JobParameter jp = job.getJobParameterByName("RECIPIENT");
if (jp != null) {
  jp.setInValue("admin@example.com");
}

// 4. Persist to schedule/submit
jcsSession.persist();

// 5. (Optional) Synchronously wait for child jobs to complete
jcsSession.waitForAllChildren(jcsJob);
```

---

## 5. Building Job Chains Programmatically

```java
// 1. Create Job Definition and Job Chain
JobDefinition chainJd = jcsSession.createJobDefinition();
chainJd.setName("MY_NEW_JOB_CHAIN");
chainJd.setPartition(partition);

JobChain chain = jcsSession.createJobChain();
chainJd.setJobChain(chain);

// 2. Create Steps and Step Calls
JobChainStep step1 = chain.createJobChainStep();
step1.setSequenceNumber(1L);

JobChainCall call1 = step1.createJobChainCall();
call1.setJobDefinition(firstJd);
call1.setSequenceNumber(1L);

// 3. Add Step Status Handlers (e.g., Error Handling)
JobChainStepStatusHandler handler = step1.createJobChainStepStatusHandler();
handler.setStatus(JobStatus.ERROR);
handler.setAction(JobChainStepStatusHandlerAction.CONTINUE); // or RETRY / ABORT

// 4. Commit changes
jcsSession.persist();
```

---

## 6. UC4 to RunMyJobs Mapping via Object Tags (`UC4ExternalBusinessKey`)

During and following migration from Automic UC4 / AE to RunMyJobs, objects maintain their mapping and lineage using Redwood `ObjectTag`s.

### Tag Definition & Value Format
- **Definition Name**: `UC4ExternalBusinessKey` (resides in `Partition.GLOBAL`).
- **Tag Value Structure**: 4 comma-separated fields:
  ```
  "<PackageId>, <UC4System>, <UC4Client>, <UC4ObjectName>"
  ```
  | Field Index | Name | Meaning | Example |
  | :--- | :--- | :--- | :--- |
  | `0` | **Package ID** | Migration package / Wave ID | `MIG_WAVE_2` |
  | `1` | **UC4 System** | UC4 server / environment name | `PROD_AE` |
  | `2` | **UC4 Client** | UC4 client number | `0100` |
  | `3` | **UC4 Object Name** | Original UC4 job / chain name | `JOBS_SAP_FI_POST` |

### Bidirectional Lookup Patterns

1. **RMJ -> UC4 Lookup** (Inspect RMJ `JobDefinition`):
   ```java
   for (ObjectTag tag : jd.getObjectTags()) {
     if ("UC4ExternalBusinessKey".equals(tag.getObjectTagDefinition().getName())) {
       String[] parts = tag.getValue().split(",");
       String uc4Name = parts.length > 3 ? parts[3].trim() : "";
       String uc4System = parts.length > 1 ? parts[1].trim() : "";
       // Map or log UC4 details
     }
   }
   ```

2. **UC4 -> RMJ Reverse Lookup** (Find RMJ `JobDefinition` from UC4 Name):
   ```sql
   select ot.RefUniqueId, ot.Value, ot.Partition
   from ObjectTag ot
   where ot.ObjectTagDefinition = ?
     and ot.ObjectDefinition = (select od.UniqueId from ObjectDefinition od where od.ObjectName = 'JobDefinition')
     and ot.Value like ?
     and ot.RefUniqueId in (select jd.UniqueId from JobDefinition jd where jd.UniqueId = jd.MasterJobDefinition)
   ```
   *Pass parameter 1 = `uc4TagDef.getUniqueId()`, parameter 2 = `"% , " + uc4Name` (or `"%," + uc4Name`), and verify `tagValue.endsWith(", " + uc4Name)` in callback.*

3. **Split Objects / Siblings**:
   In UC4 migration, a single UC4 job may be divided into multiple RMJ `JobDefinition`s (split objects). All siblings share the same UC4 object name in their `UC4ExternalBusinessKey` tag. Querying by the UC4 name and excluding `jd.getUniqueId()` retrieves all sibling definitions.

4. **Master vs Branched / Versioned Definitions**:
   Always filter for master definitions (`jd.getUniqueId().equals(jd.getMasterJobDefinition().getUniqueId())` or `jd.getBranchedLLPVersion() < 0`) to avoid targeting temporary or branched LLP instances.

---

## 7. Transaction Rules & Critical Gotchas

> [!CAUTION]
> ### 1. Trailing Whitespace Restriction
> Due to underlying database constraints in Redwood, strings cannot end with whitespace (`" "` or `"\t"`). Attempting to persist any object (e.g. Queue, Description, TableValue, ObjectTag value) with a trailing space will cause `jcsSession.persist()` to fail with an exception. Always sanitize inputs:
> ```java
> String cleanValue = rawValue != null ? rawValue.trim() : "";
> ```

> [!IMPORTANT]
> ### 2. Session Persistence Lifecycle
> - `jcsSession.hasDirtyObjects()`: Returns `true` if any modified, created, or deleted objects are pending.
> - `jcsSession.persist()`: Writes and commits all modified objects in the session.
> - `jcsSession.reset()`: Discards all unpersisted changes in the current session.
> - `jcsSession.deleteObject(obj)`: Marks an object for removal upon `persist()`.

> [!TIP]
> ### 3. DateTime Formatting & Parsing
> Redwood `DateTime` objects convert to string format `yyyy/MM/dd HH:mm:ss,SSS VV` or `yyyy/MM/dd HH:mm:ss,SSS z`.
> To parse safely into Java 8 `Instant`:
> ```java
> if (j.getScheduledStartTime() != null) {
>   String raw = j.getScheduledStartTime().toString();
>   DateTimeFormatter f = DateTimeFormatter.ofPattern("yyyy/MM/dd HH:mm:ss,SSS VV");
>   Instant instant = ZonedDateTime.parse(raw, f).toInstant();
> }
> ```

