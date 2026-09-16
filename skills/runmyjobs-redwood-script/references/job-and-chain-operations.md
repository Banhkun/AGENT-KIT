# Job Submission, Chains & Tables

Read this when creating or modifying objects that involve submission, chains, or Redwood tables.

## Submitting a job

```java
{
  JobDefinition jd = jcsSession.getJobDefinitionByName("MY_JD");
  if (jd == null) {
    jcsOut.println("JD not found");
    return;
  }
  Job job = jcsSession.createJob(jd);
  // set parameters if needed
  JobParameter p = job.getJobParameterByName("PARAM1");
  if (p != null) {
    p.setInValue("value");
  }
  if (jcsSession.hasDirtyObjects()) {
    jcsSession.persist();
  }
  jcsOut.println("Submitted: " + job.getUniqueId());
}
```

## Working with chains

Guard against cycles with a visited set. Prefer a local class for recursive helpers.

## Redwood tables

Use `jcsSession.getTableByName(...)` and the table APIs. Prefer Object Queries over direct table scans when possible.
