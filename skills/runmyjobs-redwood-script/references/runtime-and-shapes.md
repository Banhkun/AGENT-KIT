# Runtime Environment & Code Shapes

Read this when you need to know what globals are available, or before choosing how to
structure a piece of RedwoodScript.

## Available globals in a script

In a bare script (Shell / ad-hoc / parameter default / precondition / event raiser body):

- `jcsSession` – the `SchedulerSession`
- `jcsJob` – the current `Job` (may be null in some contexts)
- `jcsOut` / `jcsErr` – print streams
- `jcsParameters` – map of Job Definition parameters (when applicable)

In a compiled Job Definition class extending a `*Stub`:

- Same as above, plus the generated setter/getter methods for the parameters declared on that Job Definition.

## Two code shapes

### 1. Bare script (default)

```java
{
  // your logic here
  jcsOut.println("hello");
}
```

Use a local (non-static) class for reusable or multi-line helpers:

```java
{
  class Helper {
    void doSomething(String name) throws Exception {
      JobDefinition jd = jcsSession.getJobDefinitionByName(name);
      // ...
    }
  }
  new Helper().doSomething("MY_JD");
}
```

Or a short lambda:

```java
{
  java.util.function.Function<String, JobDefinition> lookup =
      n -> jcsSession.getJobDefinitionByName(n);
  JobDefinition jd = lookup.apply("MY_JD");
}
```

### 2. Compiled Job Definition class (exception)

Only when the code must live inside a compiled Job Definition body:

```java
public class JobDefinition_MyJob extends JobDefinition_MyJobStub {
  public void execute() throws Exception {
    // ...
  }
}
```

Prefer the bare-script shape unless the surrounding context forces the compiled class.
