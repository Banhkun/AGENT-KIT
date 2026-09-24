---
name: uc4-standalone-python
description: Write standalone Python code, automation scripts, and utilities to interact with UC4 / Automic Automation Engine (AE). Use this skill whenever the user asks to connect to UC4/Automic using Python, query or inspect UC4 objects (JOBS, JOBP, JSCH, VARA, JOBF), bulk update scripts or attributes, trigger job executions, monitor run status and download reports, manage variables, parse XML documentation (_STRUKTUR/_BSH), or build standalone Python tools leveraging the automic_rest library or direct Automic REST API endpoints.
---

# UC4 / Automic Automation Standalone Python Skill

Provides guidance, architectures, best practices, and code patterns for writing standalone Python scripts and notebook cells that interact with UC4 / Automic Automation Engine (AE) via the `automic_rest` library.

---

## 1. Core Operating Rule: Plug-and-Play Logic Only

> [!IMPORTANT]
> **Connection and Authentication are strictly owned and decided by the USER.**
>
> - **DO NOT** generate connection code (`automic.connection(...)`), login prompts, credential retrieval (`keyring`, `getpass`, environment variables), endpoint URLs, or environment selection (`eup4`, `eup6`, etc.).
> - **DO NOT** include session setup boilerplate or helper functions that configure hosts or passwords.
> - **ALWAYS assume** `automic.connection(...)` has already been run and the target client ID (`CLIENT_ID` or `client_id`) is already in scope.
> - **ALL generated code must be plug-and-play**: pure Automic library manipulation, object inspection, batch processing, data transformation, and reporting that can be immediately pasted into a notebook cell or script and executed directly.

---

## 2. Environment & Runtime Context

- **Python Virtual Environment**: UC4 tools and scripts typically run within the user's dedicated virtual environment:
  - Path: `c:\Users\DIM3HC\.virtualenvironment\AutomicTools\Scripts\python.exe`
- **Core Libraries**:
  - `automic_rest`: High-level Automic client library.
  - `requests`: Direct REST and batch operations.
  - `pandas` / `openpyxl`: Tabular data processing and Excel reporting.

---

## 3. Workflow Decision Matrix

| Goal | Primary Method | Pattern / Details |
| :--- | :--- | :--- |
| **Search objects by name/regex/type** | `automic.findObjects(client_id, body=...)` | Pass filter dicts, paginate or filter results. |
| **Fetch full object definition** | `automic.getObjects(client_id, object_name=...)` | Returns complete JSON definition (`jobp`, `jsch`, `jobs`, `vara`). |
| **Save or update object** | `automic.postObjects(client_id, body=..., query="overwrite_existing_objects=true")` | Strip read-only fields (`metadata`, timestamps) before saving. |
| **Trigger execution & wait for OK** | `automic.executeObject(...)` + `automic.getExecution(...)` | Trigger run ID, poll status, check 1900 vs 1800-1899. |
| **Download execution report/logs** | `automic.listReportContent(client_id, run_id=..., report_type="REP")` | Fetch logs (`REP`, `ACT`, `PLOG`). |
| **Inspect workflow dependencies** | Parse `workflow_definitions` & `line_conditions` | Map line numbers, predecessor links, calendar conditions. |
| **Read or write VARA values** | Inspect/update `static_values` | Access or mutate `static_values[key]['value_1']`. |
| **Find callers / where-used** | `automic.usageObject(client_id, object_name=...)` | Parse `response['references']` for parent `JSCH` or `JOBP`. |
| **Execute ad-hoc script block** | `automic.activateScript(client_id, body=...)` | Run dynamic script lines without creating a persistent job. |

---

## 4. Critical Rules & UC4 Quirks

### 1. URL Encoding of Object Names
UC4 object names often contain `#`, `/`, or other special characters (e.g. `JOBS.WIN.APP#01`).
- Direct REST requests **must** URL-encode `#` as `%23` (using `urllib.parse.quote(name, safe="")`).
- Failure to encode `#` truncates the URL path in the web engine, causing 404 or 400 errors.

### 2. Stripping Read-Only Metadata on Update
When fetching an object via `getObjects()` and submitting updates via `postObjects()`:
- Strip or pop read-only metadata fields:
  ```python
  obj_data.pop("metadata", None)
  # In general_attributes, do NOT alter:
  # 'created_by', 'created_on', 'modified_by', 'modified_on'
  ```
- Always include `query="overwrite_existing_objects=true"` in `postObjects`.

### 3. Execution Status Code Interpretation
- `1900`: `ENDED_OK` (Success).
- `1800` – `1899`: `ABEND` / Error (Abnormal termination, script fault, timeout).
- `1500` – `1600`: `RUNNING` / Active on agent.
- `1300` – `1499` & `1681` – `1712`: `WAITING` (Predecessor, queue slot, calendar condition, manual release).
- Detailed numeric lookup: See [Status Codes Reference](file:///c:/Users/DIM3HC/.agents/skills/uc4-standalone-python/references/status_codes.md).

### 4. Structured Documentation (`_STRUKTUR` / `_BSH`)
- Standard clients use `_STRUKTUR`; clients `1111` and `2222` use `_BSH`.
- Stored as XML strings inside `documentation[0]['content']`.
- Use Python's `xml.etree.ElementTree` to inspect or append version history tags (`<ver_hist><entry .../></ver_hist>`) rather than raw string hacking.
- Schema details: See [Object Schemas](file:///c:/Users/DIM3HC/.agents/skills/uc4-standalone-python/references/object_schemas.md#6-structured-documentation-_struktur--_bsh).

### 5. UC4 Script Variables (`&VAR#`)
- Variables in UC4 syntax begin with `&` and end with `#`.
- When passing variables in Python strings or regexes, beware of escape characters and unintended string interpolation.

### 6. Where-Used & Schedule Grouping Pattern
- When analyzing many child jobs across schedules, query `automic.usageObject(client_id, obj_name)` first to identify parent schedules (`ref['type'] == 'JSCH'`).
- Group jobs by parent scheduler name (`scheduler_to_jobs[jsch_name].append(job)`), then fetch each unique scheduler **only once** via `automic.getObjects(client_id, jsch_name)` to avoid redundant API calls.

---

## 5. Reference Documentation Links

Consult these dedicated documents for detailed specs:

- **[API Reference](file:///c:/Users/DIM3HC/.agents/skills/uc4-standalone-python/references/api_reference.md)**: Method signatures and parameters for `automic_rest` manipulation.
- **[Object Schemas](file:///c:/Users/DIM3HC/.agents/skills/uc4-standalone-python/references/object_schemas.md)**: Complete JSON layout of `JOBS`, `JOBP`, `JSCH`, `VARA`, `JOBF`, and XML docs.
- **[Status Codes](file:///c:/Users/DIM3HC/.agents/skills/uc4-standalone-python/references/status_codes.md)**: Full numeric status code dictionary and classification helpers.
- **[Code Recipes](file:///c:/Users/DIM3HC/.agents/skills/uc4-standalone-python/references/code_recipes.md)**: End-to-end plug-and-play recipes for search, execution, polling, report extraction, and mass updates.
