# Transaction Rules & Troubleshooting

Read this when something throws, saves nothing, or returns the wrong number of rows.

## Transaction lifecycle

| Call                             | Effect                                                             |
| :------------------------------- | :----------------------------------------------------------------- |
| `jcsSession.hasDirtyObjects()`   | `true` if any modified, created, or deleted objects are pending.    |
| `jcsSession.persist()`           | Writes and commits all modified objects in the session.             |
| `jcsSession.reset()`             | Discards all unpersisted changes in the current session.            |
| `jcsSession.deleteObject(obj)`   | Marks an object for removal on the next `persist()`.                |

Nothing reaches Redwood until `persist()`. After an exception, the session still holds dirty
objects — call `reset()` in the catch or cleanup block before doing anything else, or the next
`persist()` will commit partial state from the failed operation.

## Trailing whitespace restriction

Underlying database constraints mean **no string attribute may end in whitespace** (`" "` or
`"\t"`). Persisting a queue name, description, table value, parameter value, or object tag
value with a trailing space makes `jcsSession.persist()` throw.

```java
String cleanValue = rawValue != null ? rawValue.trim() : "";
```

Apply this at the point of assignment, not once at the top of the script — values assembled by
concatenation (like `UC4ExternalBusinessKey`) need each component trimmed individually.

## DateTime formatting

Redwood `DateTime` renders as `yyyy/MM/dd HH:mm:ss,SSS VV` or `yyyy/MM/dd HH:mm:ss,SSS z`.
Parse defensively — the null check matters, since `getScheduledStartTime()` is null for jobs
that were never scheduled:

```java
if (j.getScheduledStartTime() != null) {
  String raw = j.getScheduledStartTime().toString();
  DateTimeFormatter f = DateTimeFormatter.ofPattern("yyyy/MM/dd HH:mm:ss,SSS VV");
  Instant instant = ZonedDateTime.parse(raw, f).toInstant();
}
```

## Symptom table

| Problem                                                                                  | Cause                                                                                                        | Fix                                                                                                                            |
| :--------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------ |
| `PersistenceException: String ends with whitespace`                                      | A string attribute ends in `' '` or `'\t'`.                                                                  | `.trim()` every string input before setting it.                                                                                 |
| Duplicate rows in the query loop                                                         | Multi-table joins projecting the same object more than once.                                                 | Deduplicate with a `Set<String>` keyed on `JobDefinition.getUniqueId() + "\|" + CreationTime`.                                   |
| Child jobs or step calls mixed in with standalone jobs                                   | Query missing hierarchy filters.                                                                             | Add `and j.ParentJob is null` and/or `and j.JobChainStep is null`.                                                              |
| Changes not saved in Redwood                                                             | `persist()` never called.                                                                                    | `if (jcsSession.hasDirtyObjects()) jcsSession.persist();`                                                                       |
| Corrupted or uncommitted session state                                                   | A previous exception left objects dirty.                                                                     | `jcsSession.reset()` in catch/cleanup before the next action.                                                                   |
| UC4 lookup returns draft or versioned objects                                            | Matching non-master `JobDefinition` records.                                                                 | Add `jd.UniqueId = jd.MasterJobDefinition`, or filter `jd.getBranchedLLPVersion() < 0`.                                          |
| UC4 name lookup returns multiple RMJ `JobDefinition`s                                    | The UC4 job was split into several RMJ definitions during migration.                                         | Loop over all matches; resolve siblings — see `uc4-object-tags.md`.                                                  |
| A UC4 name lookup matches the wrong object                                               | The `like` pattern matched a name that merely ends similarly.                                                | Re-verify with `tagValue.endsWith(", " + uc4Name)` inside the callback.                                                         |
| Type-based filter (e.g. matching `"JSAP"`) always returns 0 results                      | Filtering on a naming-convention prefix instead of the real `JobDefinitionType`. A job named `JSAP_…` has type `SAPR3`. | Print `jd.getJobDefinitionType().getName()` for a sample object and filter on the real string.                                  |
| A query filtering `jd.Partition = 'SOME_NAME'` (or `.JobDefinitionType`, `.ParentApplication`, `.LastModifierSubject`) returns 0 rows even though objects with that value clearly exist | The column is a `UniqueId` reference, not the display text — UI tools render it as a name, which is misleading. | Join to the target entity and filter on its `Name` (`Partition p where jd.Partition = p.UniqueId and p.Name = ...`), or resolve the object first and bind its `UniqueId`. See `object-queries.md` rule 4.                       |
| `NullPointerException` or "not a job chain" on a `JobDefinition` you expect to be a chain | Assuming a `jd.getJobChain()` getter exists.                                                                 | Query it: `executeObjectQuery(JobChain.TYPE, " where o.JobDefinition = ?", jd.getUniqueId())`; null means leaf.                  |
| `JCS-122035: Unable to persist ... ORA-00918: column ambiguously defined`                | Multi-table query with column aliases ordering by raw table column (e.g. `ORDER BY jd.Name`) instead of the alias. | Use the projected column alias in `ORDER BY` (e.g. `SELECT jd.Name AS JobDefName ... ORDER BY JobDefName`).                     |
| Chain traversal hangs or repeats nodes                                                   | Circular chain references.                                                                                   | Keep a `visited` set keyed on `getUniqueId().toString()` and skip nodes already seen.                                           |
| Bare script won't compile — "cannot declare static method"                               | A `static` method or field declared inside a local class in a top-level `{ }` script.                       | Local classes only allow `static` members on Java 16+. Make the method an instance method instead. See `runtime-and-shapes.md`. |

## Debugging an empty result set

When a filter returns 0 rows, print the values actually flowing through **before** the filter
rather than adjusting the predicate by guesswork:

```java
jcsOut.println("Called: " + calledJd.getName() + " | type=" + typeName);
```

This is exactly how the `SAPR3`-vs-`JSAP` mismatch above was found. Assume nothing about
string values you have not printed.
