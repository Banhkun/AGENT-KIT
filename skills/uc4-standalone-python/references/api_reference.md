# Automic REST API & `automic_rest` Python Library Reference

This reference covers the `automic_rest` Python library functions for querying, modifying, executing, and analyzing UC4 / Automic Automation Engine objects.

---

## 1. Plug-and-Play Operational Model

All code in this reference assumes:
- `automic.connection(...)` has **already been initialized** by the user.
- The target `client_id` (integer or numeric string) is already defined in scope.
- No connection setup, login prompts, credentials lookups, or environment selection should be generated.

---

## 2. Core `automic_rest` API Functions

### `getObjects`
Fetches the full JSON definition of an object.

```python
obj = automic.getObjects(
    client_id=client_id,
    object_name="JOBP.DAILY.BACKUP",
    query="folder_info=true" # optional query string
)
# Access data dictionary:
obj_data = obj.response.get("data", {})
# e.g., obj_data.get("jobp") or obj_data.get("jsch")
```
- **Return Value**: Response object where `obj.status` is HTTP status code (200, 404, etc.) and `obj.response` is the parsed `dict` containing complete object structure (attributes, scripts, workflow definitions, etc.).
- **Gotcha**: If `object_name` contains `#`, encode it as `%23` before passing if required by raw HTTP.

### `findObjects`
Searches for objects matching criteria in the UC4 database.

```python
search_payload = {
    "filters": [
        {"field": "name", "op": "contains", "value": "SAP"},
        {"field": "type", "op": "equals", "value": "JOBS"}
    ],
    "max_results": 9999
}

results = automic.findObjects(
    client_id=client_id,
    body=search_payload
)
# Returns a dict or response with "data": [{"name": "...", "type": "...", "title": "..."}, ...]
```

### `postObjects`
Creates a new object or overwrites an existing object definition.

```python
response = automic.postObjects(
    client_id=client_id,
    body=object_dict_payload,
    query="overwrite_existing_objects=true" # Allows updating existing object
)
```
- **Gotcha**: When updating an existing object via `postObjects`, strip internal read-only fields (`created_by`, `modified_by`, `metadata`, `system_attributes`) before sending.

### `executeObject`
Triggers immediate or scheduled execution of an object (JOBS, JOBP, JSCH, SCRE, etc.).

```python
exec_payload = {
    "object_name": "JOBP.EOD.PROCESS",
    "execution_option": "execute", # or "queue"
    "inputs": {
        "&ENV#": "PROD",
        "&NOTIFY_EMAIL#": "team@example.com"
    }
}

result = automic.executeObject(
    client_id=client_id,
    body=exec_payload
)
run_id = result.get("run_id")
```

### `getExecution`
Retrieves live runtime details of an ongoing or completed execution.

```python
execution = automic.getExecution(
    client_id=client_id,
    run_id=run_id
)
status_code = execution.get("status")       # e.g., 1900, 1800
status_text = execution.get("status_text")  # e.g., "ENDED_OK"
```

### `listExecutions`
Queries execution history with filters.

```python
history = automic.listExecutions(
    client_id=client_id,
    query=f"max_results=50&name={object_name}&include_deactivated=true&time_frame_from=2026-01-01T00:00:00Z"
)
runs = history.response.get("data", [])
```

### `listReportContent`
Fetches execution output logs and reports.

```python
report_text = automic.listReportContent(
    client_id=client_id,
    run_id=run_id,
    report_type="REP" # Options: 'REP' (Report/Output), 'ACT' (Activation Log), 'PLOG' (Agent Job Log)
)
```

### `usageObject`
Performs a "Where-Used" search to find which workflows, schedules, or scripts reference this object.

```python
usage_data = automic.usageObject(
    client_id=client_id,
    object_name=object_name
)
# References list:
references = usage_data.response.get("references", [])
# Each ref has: "name", "type" (e.g. "JSCH", "JOBP"), "folderpath", "lastmodified"
```

### `activateScript`
Executes an ad-hoc UC4 script block on the Automation Engine without saving a persistent JOBS object.

```python
script_payload = {
    "script": ":PRINT 'Testing ad-hoc execution from Python'\n:SET &NOW# = SYS_TIME()",
    "queue": "CLIENT_QUEUE"
}
res = automic.activateScript(client_id=client_id, body=script_payload)
```
