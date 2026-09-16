# Job Submission, Chains & Tables

Read this when creating or modifying objects rather than just reading them. Everything here
ends in `jcsSession.persist()` — see `references/troubleshooting.md` for the transaction
lifecycle.

All examples use the default bare-script shape (see `references/runtime-and-shapes.md`): a
local class defined at the top of a `{ ... }` block, with instance methods that capture
`jcsSession`/`jcsOut` from the enclosing scope.

## Contents

- [Submitting a job](#submitting-a-job)
- [Building a job chain](#building-a-job-chain)
- [Step status handlers](#step-status-handlers)
- [Configuration tables](#configuration-tables)
- [Traversing an existing chain](#traversing-an-existing-chain)

## Submitting a job

`JobDefinition.prepare()` creates an unsubmitted `Job` instance. Configure it, then persist.

```java
import com.redwood.scheduler.api.model.*;
import com.redwood.scheduler.api.model.interfaces.*;
import java.util.*;
{
  class JobOps {
    Job submitJob(String partitionName, String jobDefName, String queueName, Map<String, String> parameters) throws Exception {
      Partition partition = jcsSession.getPartitionByName(partitionName);
      JobDefinition jd = jcsSession.getJobDefinitionByName(partition, jobDefName);
      Queue queue = jcsSession.getQueueByName(partition, queueName);

      if (jd == null) throw new IllegalArgumentException("JobDefinition not found: " + jobDefName);
      if (queue == null) throw new IllegalArgumentException("Queue not found: " + queueName);

      // Prepare job execution
      Job job = jd.prepare();
      job.setQueue(queue);
      job.setDescription("Submitted via RedwoodScript automation");

      // Populate parameters (trim - Redwood rejects trailing whitespace)
      if (parameters != null) {
        for (Map.Entry<String, String> entry : parameters.entrySet()) {
          JobParameter jp = job.getJobParameterByName(entry.getKey());
          if (jp != null) {
            jp.setInValue(entry.getValue() != null ? entry.getValue().trim() : "");
          }
        }
      }

      // Commit and schedule
      jcsSession.persist();
      jcsOut.println("Submitted JobId=" + job.getJobId() + " for " + jobDefName);
      return job;
    }
  }

  JobOps ops = new JobOps();
  Map<String, String> params = new HashMap<>();
  params.put("RECIPIENT", "admin@example.com");
  Job job = ops.submitJob("P1112", "System_Mail_Send", "SAP_BATCH_QUEUE", params);

  // Optional: block until spawned children finish
  jcsSession.waitForAllChildren(jcsJob);
}
```

`getJobParameterByName` returns `null` for a parameter that isn't declared on the definition —
always null-check rather than assuming the name exists.

## Building a job chain

A chain is a `JobChain` object attached to an outer `JobDefinition`. Steps hold calls; calls
point at the `JobDefinition` to run.

```java
{
  class ChainOps {
    // 5. Status handler: continue the workflow on error (alternatives: RETRY, ABORT)
    JobDefinition createChainWithErrorHandler(Partition partition, String chainName, JobDefinition step1Jd) throws Exception {
      // 1. Outer JobDefinition
      JobDefinition chainJd = jcsSession.createJobDefinition();
      chainJd.setName(chainName);
      chainJd.setPartition(partition);

      // 2. Create and attach the JobChain
      JobChain chain = jcsSession.createJobChain();
      chainJd.setJobChain(chain);

      // 3. Step 1
      JobChainStep step1 = chain.createJobChainStep();
      step1.setSequenceNumber(1L);

      // 4. Call inside step 1
      JobChainCall call = step1.createJobChainCall();
      call.setJobDefinition(step1Jd);
      call.setSequenceNumber(1L);

      JobChainStepStatusHandler handler = step1.createJobChainStepStatusHandler();
      handler.setStatus(JobStatus.ERROR);
      handler.setAction(JobChainStepStatusHandlerAction.CONTINUE);

      // 6. Commit
      jcsSession.persist();
      jcsOut.println("Created Job Chain: " + chainName);
      return chainJd;
    }
  }

  ChainOps ops = new ChainOps();
  Partition partition = jcsSession.getPartitionByName("P1112");
  JobDefinition step1Jd = jcsSession.getJobDefinitionByName(partition, "STEP1_JOB");
  ops.createChainWithErrorHandler(partition, "MY_NEW_JOB_CHAIN", step1Jd);
}
```

Sequence numbers are `Long`. Steps run in sequence-number order; multiple calls within one
step run in parallel.

## Step status handlers

Attach error/status behaviour per step (shown assembled above):

```java
JobChainStepStatusHandler handler = step1.createJobChainStepStatusHandler();
handler.setStatus(JobStatus.ERROR);
handler.setAction(JobChainStepStatusHandlerAction.CONTINUE);  // or RETRY / ABORT
```

## Configuration tables

Redwood tables are key-value stores scoped to a partition. Entries are `TableValue` rows with
columns `Col1`…`ColN`.

```java
{
  class TableOps {
    void updateTableEntry(Partition partition, String tableName, String key, String value) throws Exception {
      Table table = jcsSession.getTableByName(partition, tableName);
      if (table == null) {
        throw new IllegalArgumentException("Table not found: " + tableName);
      }

      // Bind the key rather than concatenating it, if it comes from caller input
      String sql = "select tv.* from TableValue tv where tv.Table = ? and tv.Col1 = ?";
      Iterator it = jcsSession.executeObjectQuery(sql, new Object[] { table.getUniqueId(), key });

      if (it.hasNext()) {
        TableValue tv = (TableValue) it.next();
        tv.setCol2(value != null ? value.trim() : "");
      } else {
        TableValue newTv = table.createTableValue();
        newTv.setCol1(key.trim());
        newTv.setCol2(value != null ? value.trim() : "");
      }

      if (jcsSession.hasDirtyObjects()) {
        jcsSession.persist();
        jcsOut.println("Updated table " + tableName + " key=" + key);
      }
    }
  }

  TableOps ops = new TableOps();
  Partition partition = jcsSession.getPartitionByName("P1112");
  ops.updateTableEntry(partition, "MY_LOOKUP_TABLE", "some_key", "some_value");
}
```

## Traversing an existing chain

To walk a chain that already exists, resolve the `JobChain` by query (there is no
`jd.getJobChain()` — see `references/entities-and-lookup.md`), then descend through
`getJobChainSteps()` → `getJobChainCalls()` → `getJobDefinition()`.

A local class's methods can call each other and recurse normally, so the traversal reads as
ordinary recursive Java — no manual stack needed. **Guard against circular references** with a
`visited` set keyed on `getUniqueId().toString()`, since chains can and do reference each
other in cycles.

### Worked example: collect leaf JobDefinitions of a given type

```java
import com.redwood.scheduler.api.model.*;
import com.redwood.scheduler.api.model.enumeration.*;
import com.redwood.scheduler.api.model.interfaces.*;
import java.util.*;
{
  class ChainWalker {
    Set<String> jsapNames = new LinkedHashSet<>();
    Set<String> visited = new HashSet<>();

    JobChain findChainFor(JobDefinition jd) throws Exception {
      RWIterable<JobChain> chains = jcsSession.executeObjectQuery(
          JobChain.TYPE, " where o.JobDefinition = ?", jd.getUniqueId());
      Iterator<JobChain> it = chains.iterator();
      return it.hasNext() ? it.next() : null;  // null => jd is a leaf, not a chain
    }

    void walk(JobChain chain) throws Exception {
      for (JobChainStep step : chain.getJobChainSteps()) {
        for (JobChainCall call : step.getJobChainCalls()) {
          JobDefinition calledJd = call.getJobDefinition();
          if (calledJd == null) continue;

          JobChain nestedChain = findChainFor(calledJd);
          if (nestedChain != null) {
            String key = calledJd.getUniqueId().toString();
            if (visited.contains(key)) {
              jcsOut.println("    *** CIRCULAR REFERENCE on " + calledJd.getName() + " - skipping ***");
              continue;
            }
            visited.add(key);
            walk(nestedChain);  // recurse into the nested chain
          } else {
            String typeName = calledJd.getJobDefinitionType() != null
                ? calledJd.getJobDefinitionType().getName() : "";
            // Returning 0 results? Uncomment to see the real type strings:
            // jcsOut.println("Called: " + calledJd.getName() + " | type=" + typeName);
            if ("SAPR3".equalsIgnoreCase(typeName)) {
              jsapNames.add(calledJd.getName());
            }
          }
        }
      }
    }

    void run(Partition partition, String chainName) throws Exception {
      JobDefinition rootJd = jcsSession.getJobDefinitionByName(partition, chainName);
      if (rootJd == null) {
        jcsOut.println("ERROR: Job definition not found: " + chainName);
        return;
      }

      JobChain rootChain = findChainFor(rootJd);
      if (rootChain == null) {
        jcsOut.println("  ERROR: Not a job chain: " + rootJd.getName());
        return;
      }

      visited.add(rootJd.getUniqueId().toString());
      jcsOut.println("Chain: " + rootJd.getName());
      walk(rootChain);

      jcsOut.println("  SAPR3 job definitions found: " + jsapNames.size());
      for (String name : jsapNames) {
        jcsOut.println("    - " + name);
      }
    }
  }

  String chainNamesInput = "WF_XOE_SINGLE_0045DY_LE_011_ERS_AND_CONSI"; // space-separated root chains
  String partitionName   = "P1112";

  Partition partition = jcsSession.getPartitionByName(partitionName);
  if (partition == null) {
    jcsOut.println("ERROR: Partition not found: " + partitionName);
  } else {
    for (String rawName : chainNamesInput.split(" ")) {
      String chainName = rawName.trim();
      if (chainName.isEmpty()) continue;
      new ChainWalker().run(partition, chainName);  // fresh visited/jsapNames per root
    }
  }
  jcsOut.println("=== SCRIPT COMPLETE ===");
}
```

> [!WARNING]
> `"JSAP_..."` is a naming convention, not a type. The real `JobDefinitionType` name is
> `"SAPR3"`. Never filter on a name prefix — print the type for a sample object first.

> [!TIP]
> Recursion here uses the ordinary JVM call stack, which is fine for realistic chain depths.
> If a chain is deep enough to risk a `StackOverflowError`, replace `walk`'s recursion with an
> explicit `Deque<JobChain>` used as a manual stack — the traversal logic is otherwise
> identical, just iterative instead of recursive.
