# Core Entities & Object Lookup

Read this to pick the right entity, resolve an object by name/UniqueId, or understand
the most common getters on SchedulerSession.

## Most-used entities

| Entity | Typical use |
|--------|-------------|
| Job | Running or completed instance |
| JobDefinition | Template / definition |
| JobChain | Chain of JobDefinitions |
| JobParameter / JobDefinitionParameter | Parameters |
| ObjectTag | UC4 correlation, custom tags |
| Partition | Isolation boundary |
| Queue | Submission target |
| Status | Job / Action status |

## Resolving objects

Always null-check. `get*ByName` returns null when not found.

```java
JobDefinition jd = jcsSession.getJobDefinitionByName("MY_JD");
if (jd == null) {
  jcsOut.println("JobDefinition not found");
  return;
}
```

Prefer UniqueId when you already have it:

```java
Job job = jcsSession.getJobByUniqueId(uniqueId);
```

## Using the lookup script

Before writing a getter you have not used in this conversation:

```bash
python scripts/lookup.py class JobDefinition
python scripts/lookup.py session getJob*
python scripts/lookup.py find *Chain*
```

Never invent method names. The model dump is the source of truth.
