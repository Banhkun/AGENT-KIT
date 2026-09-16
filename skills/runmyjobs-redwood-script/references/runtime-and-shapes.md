# Runtime Environment & Code Shapes

Read this when you need to know what globals are available, or before choosing how to
structure a piece of RedwoodScript.

## Predefined globals

RedwoodScript executes inside a managed Java runtime that injects these into the script
context automatically. Do not declare or instantiate them.

| Variable          | Class              | Purpose                                                                                     |
| :---------------- | :----------------- | :------------------------------------------------------------------------------------------- |
| `jcsSession`      | `SchedulerSession` | Primary API session: queries, object lookup, factory creation, transactions (`persist()`, `reset()`). |
| `jcsJob`          | `Job`              | The currently running `Job` execution instance.                                             |
| `jcsOut`          | `PrintStream`      | Redwood stdout log stream (visible in the Redwood UI).                                       |
| `jcsErr`          | `PrintStream`      | Redwood stderr log stream.                                                                   |
| Script parameters | *typed objects*    | Declared on the Job Definition (e.g. `pWorkflowName`, `pPeriod`, `pCommit`), referenced directly by name. |

## Default shape: function-oriented bare script

A standalone `{ ... }` block, run from the `Shell` tool or as an ad-hoc script body — no
class, no `extends *Stub`, no `execute()`. This is the default shape for everything in this
skill unless a task specifically requires a compiled Job Definition class.

```java
import com.redwood.scheduler.api.model.*;
import com.redwood.scheduler.api.model.enumeration.*;
import com.redwood.scheduler.api.model.interfaces.*;
import java.util.*;
import java.util.function.*;
{
  jcsOut.println("running ad-hoc script");
}
```

`jcsSession`, `jcsOut`, `jcsErr`, and script parameters are available as local variables in
this scope.

### Decomposing logic inside the block

A bare block is not limited to one flat sequence of statements. Two patterns cover everything
the reference examples need:

**Lambdas**, for a short, single-purpose helper — typically a lookup-and-validate that returns
one value:

```java
BiFunction<Partition, String, JobDefinition> getJobDef = (part, name) -> {
  JobDefinition jd = jcsSession.getJobDefinitionByName(part, name);
  if (jd == null) throw new RuntimeException("JobDefinition not found: " + name);
  return jd;
};

Partition part = jcsSession.getPartitionByName("GLOBAL");
JobDefinition jd = getJobDef.apply(part, "System_Mail_Send");
jcsOut.println("Found: " + jd.getName());
```

Standard functional interfaces (`Function`, `BiFunction`, `Consumer`, `Predicate`, etc.) cannot
declare a checked `throws Exception` on their abstract method, so lambdas that need to raise
one either wrap it in an unchecked exception (as above) or catch and log internally.

**A local class**, for anything with several parameters, a checked `throws Exception`, or
recursion:

```java
{
  class JobOps {
    JobDefinition requireJobDefinition(Partition partition, String name) throws Exception {
      JobDefinition jd = jcsSession.getJobDefinitionByName(partition, name);
      if (jd == null) throw new IllegalArgumentException("JobDefinition not found: " + name);
      return jd;
    }
  }

  JobOps ops = new JobOps();
  Partition partition = jcsSession.getPartitionByName("GLOBAL");
  JobDefinition jd = ops.requireJobDefinition(partition, "System_Mail_Send");
  jcsOut.println("Found: " + jd.getName());
}
```

A local class's instance methods capture `jcsSession`, `jcsOut`, and `jcsErr` directly from
the enclosing block (they only need to be effectively final, which they are as script
globals) — there's no need to pass them in as parameters. Its methods can also call each
other and recurse normally, using ordinary Java method calls; see
`references/job-and-chain-operations.md` for a recursive chain traversal built this way.

> [!IMPORTANT]
> Static members inside a local class require Java 16+ (JEP 395). Unless the Redwood
> scheduler's JDK version is confirmed, declare instance methods rather than `static` ones —
> instance methods work on any Java version and can still capture the enclosing locals.

## Alternate shape: compiled JobDefinition class

The script body of an `Edit Job Definition`, when the target genuinely is a compiled class
rather than a Shell/ad-hoc script: a full class extending a `*Stub` base class with an
`execute()` method.

- Private helper methods and recursion are available the same way they are in a local class.
- Parameters declared on the Job Definition are accessible as typed fields rather than as
  script-scope locals.
- Use this shape only when the surrounding context requires it (e.g. the code is being pasted
  directly into a Job Definition's script attribute that Redwood expects to compile as a
  class). Everything in this skill's references defaults to the bare-script shape instead.

## Standard imports

```java
import com.redwood.scheduler.api.model.*;
import com.redwood.scheduler.api.model.enumeration.*;
import com.redwood.scheduler.api.model.interfaces.*;
import java.util.*;
import java.util.function.*;
```

Add `java.time.*` and `java.time.format.*` when working with cutoffs or `DateTime` parsing,
and `java.sql.*` when using `executeQuery` with an `APIResultSetCallback`.
