---
name: rel-generator
description: Generate and troubleshoot Redwood Expression Language (REL) expressions for Redwood/UC4 Automation Engine (job scheduling, RunMyJobs, Automation Engine, Cloud Automation) — things like job definition parameter defaults, job chain preconditions, parameter mappings, return code mappings, event raiser comments, mail/alert subject and body text, file path construction, and table/variable/database lookups. Use this whenever the user asks to write, fix, or explain a REL expression (text starting with `=`), mentions REL, RedwoodScript, Redwood/UC4 job scheduling, Automation Engine job definitions/chains, or shows an error/example involving things like `Time.format(...)`, `Logic.if(...)`, `String.concat(...)`, `parameters.X`, `Table.getColumnString(...)`, or similar Redwood function calls — even if they don't say "REL" by name.
---

# REL Generator

Redwood Expression Language (REL) is the small expression language used throughout Redwood/UC4 Automation Engine (job definitions, job chains, alerts, mail jobs, etc.) to compute dynamic values — parameter defaults, mail subjects/bodies, file paths, preconditions, and so on. This skill helps write correct, idiomatic REL for a given scripting context.

Two reference files back this skill:
- `references/function-reference.md` — the full built-in function catalog and the implicit objects available in each scripting context (job definition default, job chain precondition, mail job, alert source, etc.). Read this whenever you need to confirm a function's exact signature or what objects (like `jobId`, `parameters.X`, `waitEvents.X`) are available in the context the user is working in.
- `references/pattern-library.md` — real-world example expressions pulled from a large production system, organized by task (building alert emails, constructing file paths, formatting dates, looking up config tables, querying job status, conditional logic, credential handling). Skim this for a template close to what the user wants before writing from scratch — REL has some idioms (especially around escaping and string building) that are much easier to copy correctly than to derive.

## Before writing an expression

1. **Identify the scripting context.** REL is embedded in specific fields (parameter default, job chain precondition, parameter mapping, return code mapping, alert source comment, mail job subject/body, constraint LOV, etc.), and each context exposes a different set of implicit objects (`jobId`, `parameters.X`, `chainParameters.X`, `waitEvents.X.raiserJobId`, `outParameters.X`, `$` for partition, and so on). Check `references/function-reference.md`'s "RedwoodExpressionLanguage Contexts" section to confirm what's actually available before referencing an object — using an object that isn't in scope for the context will fail silently or error at runtime.
2. **Figure out the shape of the output.** Is this a string (subject line, path, message body), a boolean (precondition), or a number/date? This determines which function family to reach for.
3. **Check the pattern library first.** Because REL expressions in production tend to follow a handful of recurring idioms (mail templates, path templates, date stamps, table lookups), it's usually faster and safer to adapt a close match from `references/pattern-library.md` than to write one from the function reference alone.

## Core syntax rules

- **Every REL expression starts with `=`.** This is not optional — `=Time.now()` is a valid expression, `Time.now()` typed into a REL field is not.
- **String concatenation uses `+`**, and mixes freely with function calls: `='Job ' + parameters.jobname + ' failed'`.
- **String literals use single quotes.** A literal single quote inside a string must be escaped as `\'`. A literal backslash must be doubled (`\\`), and since `\\` is itself the REL escape character, a literal single backslash in the *output* (e.g. one segment of a Windows path) usually needs to be written as `\\` in the expression, and a true UNC-style double backslash prefix (`\\server`) needs four backslashes in the expression (`\\\\server`). When in doubt about escaping depth, find the closest example in the pattern library rather than guessing — it's easy to under- or over-escape.
- **Comparison operators are triple-character:** `===`, `!==` (not `==`/`!=`). Standard `>`, `>=`, `<`, `<=` work as expected.
- **Logical operators:** `&&`, `||`, `!`.
- **No native `if/else` statement** — use `Logic.if(condition, trueValue, falseValue)` for a single branch, or `Logic.case(expr, match1, result1, ..., matchN, resultN, defaultResult)` for multi-way branching. Nested `Logic.if(...)` calls are the standard way to express else-if chains; the pattern library has several deeply nested real examples if you need to see the shape.
- **Two calling styles exist for String functions** — a dot-method style (`'Hello'.substring(1)`) and a prefixed static style (`String.substring('Hello', 1)`). Both work identically; prefer whichever matches surrounding code, or default to the `String.xxx(instance, ...)` style since it composes more predictably inside nested calls.
- **Function prefixes matter.** Functions are namespaced by prefix (`Time.`, `String.`, `Logic.`, `Table.`, `Query.`, `Variable.`, `Credential.`, `JobChainParameters.`, `Array.`, `Math.`, `Range.`, `Event.`, `SAP.`, `JDBC.`, `PLSQL.`, `Constraint.`, `Loop.`, `UserMessage.`, `Repository.`). A few functions (string basics, casts, `getSystemId()`) have no prefix. See `references/function-reference.md` for the full list per prefix.

## Common building blocks (see pattern-library.md for full examples)

- **Current system id / client:** `getSystemId()`, `Custom_REL_Functions.getUC4Client(jobId)` (site-specific helper library function — note custom libraries like `Custom_REL_Functions` are common in real systems; if the user's system has its own function library, ask or infer from context rather than assuming only built-ins exist).
- **Date/time stamps:** `Time.format(Time.now(), 'yyyyMMdd')` and variants using `Time.expressionNow('subtract 1 month')`, `Time.expressionNow('truncate month')`, etc. — the time-expression mini-language (`add`/`subtract`/`set`/`truncate` + specifier) is worth learning since it covers most "last month", "first/last day of month", "N days ago" needs without manual date math.
- **Config/table lookups:** `Table.getColumnString('$.TableName', 'rowKey', 'ColumnName')` (use `$.` for the current partition) or `Table.lookup('Partition', 'TableName', 'rowKey', 'ColumnName')`.
- **System variables:** `Variable.getString('KEY')`.
- **Credentials:** `Credential.getProtectedPasswordByProtocolRealUser('Partition', 'login', 'endpoint', 'user')`.
- **Job/database queries:** `Query.getString('select ... from Job where Job.JobId = ?', [parameters.RUNID], 'n')` — bind variables are positional `?` placeholders, and the optional trailing type string (`'n'`/`'s'` per bind var) is needed on some databases.
- **Cross-job-chain values:** `JobChainParameters.getOutValueString('Step 1, Job 1', 'ParamName')`, `JobChainParameters.getJobId('Step name, Job N')`, `JobChainParameters.getJobStatus(...)`.
- **Conditional value / mail text:** nested `Logic.if(...)` or `Logic.case(...)`; multi-line mail bodies are almost always built by concatenating a parameter that holds a newline character (commonly named `parameters.NL`, `parameters.NewLine`, or `parameters.CRLF` in the job definition) between literal string segments, e.g. `='Hello,' + parameters.NL + parameters.NL + 'The job has failed.'`.

## After writing an expression

- Double check the expression **begins with `=`**.
- Double check every implicit object referenced (`parameters.X`, `jobId`, `waitEvents.X`, `$`, etc.) is actually available in the target scripting context per `references/function-reference.md`.
- Double check quote/backslash escaping, especially for file paths and nested quoted strings — this is the single most common source of subtle bugs in real REL expressions.
- If the expression is long or deeply nested (common with chained `Logic.if`/`Logic.case` or multi-segment `String.concat`), consider whether it would be clearer restructured, but match the existing style in the user's system if they've shown you other expressions from it.
