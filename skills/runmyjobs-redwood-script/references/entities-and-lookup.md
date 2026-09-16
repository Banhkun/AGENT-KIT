# Core Entities & Object Lookup

Read this to pick the right entity, resolve an object by name or id, or find a getter
without guessing at its name.

## Contents

- [Look up the real fields and methods first](#look-up-the-real-fields-and-methods-first)
- [Entities at a glance](#entities-at-a-glance)
- [Lookup by name and partition](#lookup-by-name-and-partition)
- [Lookup by UniqueId / JobId](#lookup-by-uniqueid--jobid)
- [Relationships that have no direct getter](#relationships-that-have-no-direct-getter)

## Look up the real fields and methods first

This skill bundles `scripts/lookup.py` and `assets/model.json` — a machine-generated
dump of the actual Redwood Data Model (462 entities, their fields, and the ~600
`SchedulerSession` lookup/creation methods), built from the live JavaDoc rather than
hand-transcribed. It answers the two questions that otherwise get guessed at:

```
python scripts/lookup.py session JobDefinition   # how do I get/create one of these?
python scripts/lookup.py class JobDefinition     # what fields/methods does it have?
python scripts/lookup.py refs JobDefinition      # what points AT this entity?
python scripts/lookup.py path JobChain Subject   # how do I navigate from A to B?
```

Run `session <Entity>` before writing a lookup, and `class <Entity>` before writing
anything that calls a getter/setter on an entity you haven't used yet — printing the
real method name costs one command and prevents a `NoSuchMethodError` or a silently
wrong guess (e.g. `getJobDefinitionByName` vs a guessed `findJobDefinitionByName`).
`class` also lists every field with a `->` marker for reference-typed columns (see the
Partition note below and `object-queries.md` rule 4 for why that matters in queries).

The model doesn't yet include the supertype hierarchy (Partition tree data wasn't part
of this build), so `extends/implements` may print empty even for entities that do
inherit fields — treat an empty result there as "not recorded," not "has no supertype."

## Entities at a glance

For orientation before reaching for the script. Not exhaustive — run `lookup.py find
<pattern>` to see what else exists (e.g. `find alert`, `find sap`).

| Entity                       | What it is                                              |
| :---------------------------- | :------------------------------------------------------ |
| `Job`                          | An execution instance of a job or chain.                 |
| `JobDefinition`                | The definition/template of a job or workflow.            |
| `JobParameter`                 | Runtime parameter of a `Job` execution.                  |
| `JobDefinitionParameter`       | Parameter definition on a `JobDefinition`.                |
| `JobChain` / `JobChainStep` / `JobChainCall` | Workflow container, its steps, and each step's invocation of a `JobDefinition`. |
| `Partition`                    | Logical isolation namespace (`GLOBAL` or custom).         |
| `Application`                  | Functional grouping of job definitions ("folder").       |
| `Queue`                        | Execution queue for running jobs.                        |
| `Table` / `TableValue`         | Redwood key-value configuration store and its entries.   |
| `TimeWindow`                   | Allowed execution windows / calendars.                    |
| `ObjectTag` / `ObjectTagDefinition` | Tag instance and its schema (e.g. `UC4ExternalBusinessKey`). |
| `PartitionableObject`          | Base interface for objects that can hold tags & partitions. |

## Lookup by name and partition

Most configuration objects belong to a `Partition` (`GLOBAL` or tenant-specific). Resolve the
partition first.

```java
Partition global      = jcsSession.getPartitionByName("GLOBAL");
Partition projectPart = jcsSession.getPartitionByName("P1113");

JobDefinition jd       = jcsSession.getJobDefinitionByName(projectPart, "MY_JOB_DEF");
Queue queue            = jcsSession.getQueueByName(projectPart, "SAP_BATCH_QUEUE");
Table table            = jcsSession.getTableByName(projectPart, "MY_LOOKUP_TABLE");
TimeWindow tw          = jcsSession.getTimeWindowByName(global, "TW_WORKING_HOURS");
ObjectTagDefinition otd = jcsSession.getObjectTagDefinitionByName(global, "UC4ExternalBusinessKey");
```

Every one of these returns `null` when not found — check before dereferencing. The five
shown here are the common ones; run `python scripts/lookup.py session <Entity>` for
anything not listed rather than guessing the by-name method exists.

`getPartition()`, `getJobDefinitionType()`, and similar getters return the real object, so
this pitfall doesn't arise when working through the Java API directly. It only bites inside a
query string — `references/object-queries.md` (rule 4) covers why `jd.Partition = 'P1112'`
fails silently and what to write instead.

## Lookup by UniqueId / JobId

```java
Job job            = jcsSession.getJobByJobId(1234567L);
JobDefinition jd   = jcsSession.getJobDefinitionByUniqueId(987654L);
Alert alert        = jcsSession.getAlertByUniqueId(555123L);
SchedulerEntity se = jcsSession.getSchedulerEntityByObjectTypeUniqueId("JobDefinition", uniqueId);
```

`getSchedulerEntityByObjectTypeUniqueId` returns the generic `SchedulerEntity` — cast only
after an `instanceof` check. This is the standard way to turn `ObjectTag.RefUniqueId` values
back into real objects.

## Relationships that have no direct getter

`JobDefinition` has **no** `getJobChain()` method. To find the `JobChain` belonging to a
`JobDefinition`, query for it:

```java
RWIterable<JobChain> chains = jcsSession.executeObjectQuery(
    JobChain.TYPE,
    " where o.JobDefinition = ?",
    jd.getUniqueId()
);
Iterator<JobChain> it = chains.iterator();
JobChain chain = it.hasNext() ? it.next() : null;   // null => jd is a leaf, not a chain
```

A null result is the correct and only reliable test for "this JobDefinition is a leaf".
Confirmed traversal getters: `JobChain.getJobChainSteps()`, `JobChainStep.getJobChainCalls()`,
`JobChainCall.getJobDefinition()`.
