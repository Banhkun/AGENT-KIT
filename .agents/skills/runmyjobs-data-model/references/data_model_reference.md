# RunMyJobs (Redwood) Data Model Detailed Reference

This document provides in-depth reference documentation, entity tables, query syntax rules, and complete code recipes for interacting with the RunMyJobs Data Model in Java (RedwoodScript).

---

## 1. Core Data Model Entities

In Redwood, entities represent objects in the scheduling engine and are accessed through the Object Model layer.

| Entity | Description | Key Methods & Properties |
| :--- | :--- | :--- |
| **`Job`** | An execution instance of a job or chain. | `getJobId()`, `getJobDefinition()`, `getStatus()`, `getScheduledStartTime()`, `getCreationTime()`, `getParentJob()`, `getJobChainStep()`, `getQueue()`, `getJobFiles()`, `getJobParameterByName(name)` |
| **`JobDefinition`** | The definition/template of a job or workflow. | `getName()`, `getUniqueId()`, `getParentApplication()`, `getPartition()`, `getDefaultQueue()`, `getJobDefinitionType()`, `getParameters()`, `prepare()` |
| **`JobParameter`** | Runtime parameter of a `Job` execution. | `getName()`, `getInValue()`, `setInValue(String)`, `getOutValue()` |
| **`JobDefinitionParameter`**| Parameter definition on a `JobDefinition`. | `getName()`, `getDefaultValue()`, `setDefaultValue(String)`, `getDataType()`, `getDirection()` |
| **`JobChain`** | Workflow container holding steps. | `createJobChainStep()`, `getJobChainSteps()` |
| **`JobChainStep`** | A sequential or parallel step in a `JobChain`. | `getSequenceNumber()`, `setSequenceNumber(Long)`, `createJobChainCall()`, `createJobChainStepStatusHandler()` |
| **`JobChainCall`** | An invocation of a `JobDefinition` within a step. | `setJobDefinition(JobDefinition)`, `setSequenceNumber(Long)`, `createJobChainCallInExpressionParameter()` |
| **`JobChainStepStatusHandler`** | Step-level error/status handling behavior. | `setStatus(JobStatus)`, `setAction(JobChainStepStatusHandlerAction)` |
| **`Partition`** | Logical isolation namespace (`GLOBAL` or custom). | `getName()`, `getUniqueId()` |
| **`Application`** | Functional grouping of job definitions. | `getName()`, `getUniqueId()`, `getParentApplication()` |
| **`Queue`** | Execution queue for running jobs. | `getName()`, `getUniqueId()`, `getPartition()`, `getStatus()` |
| **`Table`** | Redwood key-value / configuration table. | `getName()`, `getPartition()`, `getTableValues()` |
| **`TableValue`** | Entry inside a Redwood table. | `getTable()`, `getCol1()` ... `getColN()`, `getValue()` |
| **`TimeWindow`** | Defines allowed execution windows / calendars. | `getName()`, `getPartition()`, `isOpen(DateTime)` |
| **`ObjectTag`** | Tag instance attached to a `PartitionableObject`. | `getValue()`, `setValue(String)`, `getObjectTagDefinition()`, `getParentSchedulerEntities()`, `deleteObject()` |
| **`ObjectTagDefinition`** | Definition / schema of an object tag (e.g. `UC4ExternalBusinessKey`). | `getName()`, `getUniqueId()`, `getPartition()` |
| **`PartitionableObject`** | Base interface for objects that can hold tags & partitions. | `getObjectTags()`, `getObjectTagByObjectTagDefinition(otd)`, `createObjectTag(otd)` |

---

## 2. Object Query Language (ANSI SQL'92 Subset)

Redwood uses `jcsSession.executeObjectQuery(sql, parameters)` to query the Data Model.

### Object Query Rules
1. Always reference **Entity names** (e.g. `Job`, `JobDefinition`, `Application`, `ObjectTag`), not DB table names.
2. Wildcard selects must specify the table alias: `select j.* from Job j`.
3. Entity relationships are joined via `UniqueId`:
   ```sql
   select j.*
   from Job j, JobDefinition jd, Application a
   where (j.JobDefinition = jd.UniqueId)
     and (jd.ParentApplication = a.UniqueId)
     and (a.Name like '%FINANCE%')
   ```
4. Date / Time fields (`ScheduledStartTime`, `CreationTime`) can be queried with epoch milliseconds enclosed in single quotes:
   ```sql
   and j.ScheduledStartTime > '1773000000000'
   ```
5. Status codes:
   - `'C'`: Completed
   - `'E'`: Error
   - `'W'`: Waiting
   - `'Q'`: Queued
   - `'R'`: Running
   - `'S'`: Scheduled
   - `'X'`: Killed / Canceled

---

## 3. Practical Code Recipes

### Recipe 1: Querying Top-Level RMJ Jobs with Time Cutoff & Deduplication

```java
private Map<String, List<Job>> loadRmjJobs(long hoursBack, String appFilter) throws Exception {
  // 1. Calculate cutoff time in epoch millis
  Instant cutoff = Instant.now().minus(hoursBack, ChronoUnit.HOURS).truncatedTo(ChronoUnit.SECONDS);
  String cutoffEpoch = String.valueOf(cutoff.toEpochMilli());

  // 2. Build ANSI SQL query for the Redwood Data Model
  String q = "select j.*"
           + " from Job j, JobDefinition jd, Application a"
           + " where (j.JobDefinition = jd.UniqueId)"
           + " and (jd.ParentApplication = a.UniqueId and a.Name like '%" + appFilter + "%')"
           + " and (j.JobChainStep is null)"
           + " and j.Status in ('E','C','W')"
           + " and j.ScheduledStartTime > '" + cutoffEpoch + "'"
           + " order by j.JobId desc";

  Map<String, List<Job>> map = new HashMap<>();
  Set<String> seenKeys = new HashSet<>();
  int duplicateCount = 0;

  for (Iterator it = jcsSession.executeObjectQuery(q, null); it.hasNext();) {
    Job j = (Job) it.next();
    String name = j.getJobDefinition().getName();

    // Prevent duplicate rows from joins
    String dedupKey = j.getJobDefinition().getUniqueId() + "|" + j.getCreationTime();
    if (!seenKeys.add(dedupKey)) {
      duplicateCount++;
      continue;
    }

    map.computeIfAbsent(name, k -> new ArrayList<>()).add(j);
  }

  jcsOut.println("Loaded " + map.size() + " job groups (skipped " + duplicateCount + " duplicates)");
  return map;
}
```

---

### Recipe 2: Safe Parsing of Redwood DateTime to Java `Instant`

Redwood `DateTime` objects output string values in the format `yyyy/MM/dd HH:mm:ss,SSS VV`:

```java
private Instant parseRwdDateTime(Job j) {
  try {
    if (j.getScheduledStartTime() == null) {
      return null;
    }

    String raw = j.getScheduledStartTime().toString();
    DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy/MM/dd HH:mm:ss,SSS VV");

    return ZonedDateTime.parse(raw, formatter).toInstant();
  } catch (Exception e) {
    jcsErr.println("Failed to parse ScheduledStartTime for JobId=" + j.getJobId() + ": " + e.getMessage());
    return null;
  }
}
```

---

### Recipe 3: Submitting a Job Definition with Parameters

```java
public Job submitJob(String partitionName, String jobDefName, String queueName, Map<String, String> parameters) throws Exception {
  Partition partition = jcsSession.getPartitionByName(partitionName);
  JobDefinition jd = jcsSession.getJobDefinitionByName(partition, jobDefName);
  Queue queue = jcsSession.getQueueByName(partition, queueName);

  if (jd == null) throw new IllegalArgumentException("JobDefinition not found: " + jobDefName);
  if (queue == null) throw new IllegalArgumentException("Queue not found: " + queueName);

  // Prepare job execution
  Job job = jd.prepare();
  job.setQueue(queue);
  job.setDescription("Submitted via RedwoodScript automation");

  // Populate parameters
  if (parameters != null) {
    for (Map.Entry<String, String> entry : parameters.entrySet()) {
      JobParameter jp = job.getJobParameterByName(entry.getKey());
      if (jp != null) {
        // Sanitize string to prevent trailing whitespace error
        String val = entry.getValue() != null ? entry.getValue().trim() : "";
        jp.setInValue(val);
      }
    }
  }

  // Commit and schedule
  jcsSession.persist();
  jcsOut.println("Submitted JobId=" + job.getJobId() + " for " + jobDefName);
  return job;
}
```

---

### Recipe 4: Creating a Job Chain with Status Handlers

```java
public JobDefinition createChainWithErrorHandler(Partition partition, String chainName, JobDefinition step1Jd) throws Exception {
  // 1. Create outer JobDefinition
  JobDefinition chainJd = jcsSession.createJobDefinition();
  chainJd.setName(chainName);
  chainJd.setPartition(partition);

  // 2. Create and attach JobChain
  JobChain chain = jcsSession.createJobChain();
  chainJd.setJobChain(chain);

  // 3. Create Step 1
  JobChainStep step1 = chain.createJobChainStep();
  step1.setSequenceNumber(1L);

  // 4. Create Call in Step 1
  JobChainCall call = step1.createJobChainCall();
  call.setJobDefinition(step1Jd);
  call.setSequenceNumber(1L);

  // 5. Add Step Status Handler (continue workflow on error)
  JobChainStepStatusHandler handler = step1.createJobChainStepStatusHandler();
  handler.setStatus(JobStatus.ERROR);
  handler.setAction(JobChainStepStatusHandlerAction.CONTINUE);

  // 6. Commit to Redwood repository
  jcsSession.persist();
  jcsOut.println("Created Job Chain: " + chainName);
  return chainJd;
}
```

---

### Recipe 5: Interacting with Redwood Configuration Tables

```java
public void updateTableEntry(Partition partition, String tableName, String key, String value) throws Exception {
  Table table = jcsSession.getTableByName(partition, tableName);
  if (table == null) {
    throw new IllegalArgumentException("Table not found: " + tableName);
  }

  // Query table values using ANSI SQL
  String sql = "select tv.* from TableValue tv where tv.Table = " + table.getUniqueId() + " and tv.Col1 = '" + key + "'";
  Iterator it = jcsSession.executeObjectQuery(sql, null);

  if (it.hasNext()) {
    TableValue tv = (TableValue) it.next();
    // Trim trailing whitespace to comply with Redwood database constraints
    tv.setCol2(value != null ? value.trim() : "");
  } else {
    // Create new table entry if not exists
    TableValue newTv = table.createTableValue();
    newTv.setCol1(key.trim());
    newTv.setCol2(value != null ? value.trim() : "");
  }

  if (jcsSession.hasDirtyObjects()) {
    jcsSession.persist();
    jcsOut.println("Updated table " + tableName + " key=" + key);
  }
}
```

---

### Recipe 6: Reading UC4 Object Metadata from an RMJ JobDefinition

```java
public static class Uc4Metadata {
  public String packageId;
  public String uc4System;
  public String uc4Client;
  public String uc4Name;
  public String rawTagValue;
}

public Uc4Metadata getUc4Metadata(JobDefinition jd) {
  for (ObjectTag tag : jd.getObjectTags()) {
    if ("UC4ExternalBusinessKey".equals(tag.getObjectTagDefinition().getName())) {
      String raw = tag.getValue();
      if (raw == null || raw.trim().isEmpty()) return null;

      String[] parts = raw.split(",");
      Uc4Metadata meta = new Uc4Metadata();
      meta.rawTagValue = raw;
      meta.packageId = parts.length > 0 ? parts[0].trim() : "";
      meta.uc4System  = parts.length > 1 ? parts[1].trim() : "";
      meta.uc4Client  = parts.length > 2 ? parts[2].trim() : "";
      meta.uc4Name    = parts.length > 3 ? parts[3].trim() : "";
      return meta;
    }
  }
  return null; // No UC4 tag found
}
```

---

### Recipe 7: Reverse Lookup: Find RMJ JobDefinition(s) from a UC4 Name

```java
public List<JobDefinition> findRmjJobDefinitionsByUc4Name(String uc4Name, Partition optionalPartition) throws Exception {
  Partition global = jcsSession.getPartitionByName("GLOBAL");
  ObjectTagDefinition uc4TagDef = jcsSession.getObjectTagDefinitionByName(global, "UC4ExternalBusinessKey");
  if (uc4TagDef == null) {
    throw new IllegalStateException("ObjectTagDefinition 'UC4ExternalBusinessKey' not found in GLOBAL partition");
  }

  String likePattern = "%, " + uc4Name.trim();
  String sql = "select ot.RefUniqueId, ot.Value, ot.Partition "
             + "from ObjectTag ot "
             + "where ot.ObjectTagDefinition = ? "
             + "  and ot.ObjectDefinition = (select od.UniqueId from ObjectDefinition od where od.ObjectName = 'JobDefinition') "
             + "  and ot.Value like ? "
             + "  and ot.RefUniqueId in (select jd.UniqueId from JobDefinition jd where jd.UniqueId = jd.MasterJobDefinition) "
             + (optionalPartition != null ? "  and ot.Partition = ? " : "");

  Object[] params = optionalPartition != null
      ? new Object[] { uc4TagDef.getUniqueId(), likePattern, optionalPartition.getUniqueId() }
      : new Object[] { uc4TagDef.getUniqueId(), likePattern };

  List<Long> matchedIds = new ArrayList<>();
  jcsSession.executeQuery(sql, params, new APIResultSetCallback() {
    public boolean callback(ResultSet rs, ObjectGetter og) throws SQLException {
      String tagValue = rs.getString(2);
      if (tagValue != null && tagValue.endsWith(", " + uc4Name.trim())) {
        matchedIds.add(rs.getLong(1));
      }
      return true;
    }
    public void start() {}
    public void finish() {}
  });

  List<JobDefinition> result = new ArrayList<>();
  for (Long id : matchedIds) {
    SchedulerEntity se = jcsSession.getSchedulerEntityByObjectTypeUniqueId("JobDefinition", id);
    if (se instanceof JobDefinition) {
      result.add((JobDefinition) se);
    }
  }
  return result;
}
```

---

### Recipe 8: Finding Split Object Siblings

When a UC4 job has been split into multiple RMJ `JobDefinition`s during migration, find all other RMJ definitions that originated from the same UC4 job:

```java
public List<JobDefinition> findSiblings(JobDefinition sourceJd) throws Exception {
  Uc4Metadata meta = getUc4Metadata(sourceJd);
  if (meta == null || meta.uc4Name.isEmpty()) {
    return Collections.emptyList();
  }

  List<JobDefinition> allMatches = findRmjJobDefinitionsByUc4Name(meta.uc4Name, null);
  List<JobDefinition> siblings = new ArrayList<>();
  for (JobDefinition match : allMatches) {
    if (!match.getUniqueId().equals(sourceJd.getUniqueId())) {
      siblings.add(match);
    }
  }
  return siblings;
}
```

---

### Recipe 9: Assigning or Updating `UC4ExternalBusinessKey` on a JobDefinition

```java
public void setUc4ExternalBusinessKey(JobDefinition jd, String packageId, String uc4System, String uc4Client, String uc4Name) throws Exception {
  Partition global = jcsSession.getPartitionByName("GLOBAL");
  ObjectTagDefinition uc4TagDef = jcsSession.getObjectTagDefinitionByName(global, "UC4ExternalBusinessKey");
  if (uc4TagDef == null) {
    uc4TagDef = jcsSession.createObjectTagDefinition();
    uc4TagDef.setName("UC4ExternalBusinessKey");
    uc4TagDef.setPartition(global);
  }

  ObjectTag ot = jd.getObjectTagByObjectTagDefinition(uc4TagDef);
  if (ot == null) {
    ot = jd.createObjectTag(uc4TagDef);
  }

  // Sanitize parts to prevent trailing whitespace errors
  String safePackage = packageId != null ? packageId.trim() : "";
  String safeSystem  = uc4System != null ? uc4System.trim() : "";
  String safeClient  = uc4Client != null ? uc4Client.trim() : "";
  String safeName    = uc4Name   != null ? uc4Name.trim()   : "";

  String tagValue = safePackage + ", " + safeSystem + ", " + safeClient + ", " + safeName;
  ot.setValue(tagValue);

  jcsSession.persist();
  jcsOut.println("Set UC4ExternalBusinessKey on " + jd.getName() + " -> " + tagValue);
}
```

---

## 4. Troubleshooting & Gotchas Summary

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| `PersistenceException: String ends with whitespace` | A String attribute (description, parameter, table value, object tag value) ends with `' '` or `'\t'`. | Apply `.trim()` on all string inputs before setting attributes. |
| Duplicate rows returned in query loop | Multi-table joins (e.g. `Job`, `JobDefinition`, `Application`) returning multiple row projections. | Deduplicate using a `Set<String>` with `JobDefinition.getUniqueId() + "|" + CreationTime`. |
| Child jobs or step calls mixed with standalone jobs | Query missing hierarchy filters. | Add `and j.ParentJob is null` and/or `and j.JobChainStep is null`. |
| Changes not saved in Redwood | Forgot to call `jcsSession.persist()`. | Check `if (jcsSession.hasDirtyObjects()) jcsSession.persist();`. |
| Corrupted or uncommitted session changes | Previous exception left objects dirty. | Call `jcsSession.reset();` in catch/cleanup blocks before next action. |
| UC4 lookup returns unexpected versions or draft objects | Matching non-master JobDefinition records. | Add condition `jd.UniqueId = jd.MasterJobDefinition` or `jd.getBranchedLLPVersion() < 0`. |
| UC4 name lookup returns multiple RMJ JobDefinitions | The UC4 job was split into multiple RMJ JobDefinitions during migration. | Loop over all matches or resolve siblings using `findSiblings()`. |

