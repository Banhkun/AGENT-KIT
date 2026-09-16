# Object Queries (`executeObjectQuery`)

Read this when writing or debugging a query against the Redwood Data Model.

## Contents

- [Critical rule](#critical-rule)
- [Execution signatures](#execution-signatures)
- [Query syntax rules](#query-syntax-rules)
- [Job status codes](#job-status-codes)
- [Hierarchy filters](#hierarchy-filters)
- [Time cutoffs](#time-cutoffs)
- [Deduplication](#deduplication)
- [Parameterised queries with a callback](#parameterised-queries-with-a-callback)

## Critical rule

Query the Redwood **Object Model** using the ANSI SQL'92 subset via `jcsSession`. Never query
underlying database tables directly — table and column names are unstable across versions and
direct access bypasses security contexts.

## Execution signatures

```java
// 1. Untyped Iterator (most common)
String q = "select j.* from Job j where j.Status in ('E', 'C', 'W') and j.ParentJob is null";
for (Iterator it = jcsSession.executeObjectQuery(q, null); it.hasNext();) {
  Job j = (Job) it.next();
  // process job
}

// 2. Typed RWIterable, full SQL
String sql = "select t.* from Table t where t.Name = 'CT_CONFIG'";
for (Table tb : jcsSession.executeObjectQuery(Table.TYPE, sql, null)) {
  // process table
}

// 3. Typed RWIterable, where-fragment with bind parameters
RWIterable<JobChain> chains = jcsSession.executeObjectQuery(
    JobChain.TYPE, " where o.JobDefinition = ?", jd.getUniqueId());
```

In form 3 the alias is always `o`, and the fragment starts with a leading space and `where`.

## Query syntax rules

1. Reference **entity names** (`Job`, `JobDefinition`, `Application`, `ObjectTag`), not DB
   table names.
2. Wildcard selects must be alias-qualified: `select j.* from Job j` — bare `select *` fails.
3. Entities join on `UniqueId`, not on arbitrary foreign keys:

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

   `jd.ParentApplication` above is exactly the pattern the next rule generalises — a
   reference column that has to be joined rather than compared to text.

4. **A reference-typed column holds a `UniqueId`, not the name it displays as.**
   `JobDefinition.Partition`, `.JobDefinitionType`, `.ParentApplication`, and
   `.LastModifierSubject` are the common ones. Tools like the Support Query page render
   these as the target object's name, which makes `jd.Partition = 'P1112'` look like it
   should work. It doesn't — that compares a `UniqueId` against a string and silently
   matches nothing.

   ```sql
   -- Wrong: Partition is a UniqueId, not text
   select jd.* from JobDefinition jd where jd.Partition = 'P1112'

   -- Right: join to the Partition entity and filter on its Name
   select jd.*
   from JobDefinition jd, Partition p
   where jd.Partition = p.UniqueId
     and p.Name = 'P1112'
   ```

   In plain Java this is usually avoidable entirely — resolve the object first with
   `jcsSession.getPartitionByName(...)` (see `references/entities-and-lookup.md`) and bind
   its `UniqueId` directly:

   ```java
   Partition partition = jcsSession.getPartitionByName("P1112");
   String q = "select jd.* from JobDefinition jd where jd.Partition = ?";
   for (Iterator it = jcsSession.executeObjectQuery(q, new Object[] { partition.getUniqueId() }); it.hasNext();) {
     JobDefinition jd = (JobDefinition) it.next();
   }
   ```

   The join form is only needed when the query itself has to filter or display the name
   (e.g. a `like` on partition name) rather than an exact match you already hold the object
   for.

5. Date/time fields (`ScheduledStartTime`, `CreationTime`) are compared against **epoch
   milliseconds enclosed in single quotes**.
6. Subqueries are supported — see `references/uc4-object-tags.md` for the `ObjectDefinition`
   subquery pattern.

## Job status codes

| Code  | Meaning           |
| :---- | :---------------- |
| `'C'` | Completed         |
| `'E'` | Error             |
| `'W'` | Waiting           |
| `'Q'` | Queued            |
| `'R'` | Running           |
| `'S'` | Scheduled         |
| `'X'` | Killed / Canceled |

## Hierarchy filters

- `j.ParentJob is null` — excludes child jobs spawned by a parent job.
- `j.JobChainStep is null` — excludes executions running as a step inside a Job Chain.

Omitting these is the usual reason a "list of jobs" query returns far more rows than expected,
mixing standalone jobs with internal step executions.

## Time cutoffs

```java
Instant cutoff = Instant.now().minus(24, ChronoUnit.HOURS).truncatedTo(ChronoUnit.SECONDS);
String cutoffEpoch = String.valueOf(cutoff.toEpochMilli());
String q = "select j.* from Job j where j.ScheduledStartTime > '" + cutoffEpoch + "'";
```

Going the other way — Redwood `DateTime` to Java `Instant` — the string format is
`yyyy/MM/dd HH:mm:ss,SSS VV` (sometimes `… z`). `getScheduledStartTime()` is null for jobs
that were never scheduled, so check before parsing. Because it catches its own exception and
takes one argument, this is a good candidate for a `Function` lambda rather than a local class:

```java
Function<Job, Instant> parseRwdDateTime = j -> {
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
};

Instant when = parseRwdDateTime.apply(job);
```

## Deduplication

Multi-table joins can project the same logical object across several rows. Deduplicate on a
composite key rather than trusting the row count:

```java
Set<String> seen = new HashSet<>();
for (Iterator it = jcsSession.executeObjectQuery(q, null); it.hasNext();) {
  Job j = (Job) it.next();
  String dedupKey = j.getJobDefinition().getUniqueId() + "|" + j.getCreationTime();
  if (!seen.add(dedupKey)) {
    continue; // duplicate projection of an already-processed job
  }
  // process distinct job
}
```

## Parameterised queries with a callback

For raw column projection (rather than whole objects), use `executeQuery` with an
`APIResultSetCallback`. Bind parameters with `?` and pass an `Object[]`:

```java
jcsSession.executeQuery(sql, params, new APIResultSetCallback() {
  public boolean callback(ResultSet rs, ObjectGetter og) throws SQLException {
    // rs column indexes are 1-based, matching the select list order
    return true;  // false stops iteration early
  }
  public void start() {}
  public void finish() {}
});
```

`like` patterns are matched loosely by the database — re-verify the match in the callback
(e.g. `value.endsWith(suffix)`) rather than relying on the pattern alone.

## Complete pattern: filtered job load with deduplication

Combines every rule above — entity names, alias-qualified wildcard, `UniqueId` joins,
hierarchy filter, status filter, epoch cutoff, dedup. `throws Exception` and several
parameters make this a local-class method rather than a lambda, in the default bare-script
shape (see `references/runtime-and-shapes.md`):

```java
import com.redwood.scheduler.api.model.*;
import java.util.*;
import java.time.*;
import java.time.temporal.*;
{
  class JobQueries {
    Map<String, List<Job>> loadRmjJobs(long hoursBack, String appFilter) throws Exception {
      Instant cutoff = Instant.now().minus(hoursBack, ChronoUnit.HOURS).truncatedTo(ChronoUnit.SECONDS);
      String cutoffEpoch = String.valueOf(cutoff.toEpochMilli());

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
  }

  Map<String, List<Job>> jobsByName = new JobQueries().loadRmjJobs(24, "FINANCE");
}
```

> [!WARNING]
> `appFilter` is concatenated into the query string. When the value originates from a Job
> Definition parameter or any caller-supplied source, use the bind-parameter form instead —
> see the callback pattern above and the reverse-lookup query in
> `references/uc4-object-tags.md`.
