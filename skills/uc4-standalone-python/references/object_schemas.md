# UC4 / Automic Object JSON Schemas & Data Structures

This document provides schema breakdowns and JSON payload structures for UC4 object types commonly inspected and modified via Python scripts.

---

## 1. `JOBS` (Executable Jobs)

Jobs represent executable tasks running on specific Agents (UNIX, Windows, SAP, SQL, etc.).

### Top-Level JSON Structure

```json
{
  "name": "JOBS.WIN.DATA_SYNC",
  "type": "JOBS_WIN",
  "title": "Synchronize daily warehouse files",
  "general_attributes": {
    "title": "Synchronize daily warehouse files",
    "archive_key1": "WAREHOUSE",
    "archive_key2": "DAILY",
    "cost_center": "CC_9981",
    "queue": "CLIENT_QUEUE",
    "priority": 200,
    "active": true
  },
  "job_attributes": {
    "host": "WIN_AGENT_01",
    "login": "LOGIN.PROD.APPUSER",
    "platform": "WINDOWS",
    "auto_deactivate": "ALWAYS",
    "priority": 200
  },
  "runtime_attributes": {
    "max_runtime": {
      "active": true,
      "value": "01:00:00",
      "action": "CANCEL"
    },
    "min_runtime": {
      "active": false,
      "value": "00:01:00"
    }
  },
  "scripts": {
    "pre_process": ":PUT_ATT QUEUE = 'CLIENT_QUEUE'",
    "process": "@echo off\npython -m app.sync --date &DATE#\nif %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%",
    "post_process": ":IF &RETCODE# NE 0\n:  SEND_MAIL 'admin@bosch.com',,'Job Failed'\n:ENDIF"
  },
  "documentation": [
    {
      "type": "_STRUKTUR",
      "content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><Content ...>...</Content>"
    }
  ]
}
```

### Script Tabs
- **`pre_process`**: Executed during generation phase inside the Automation Engine. Cannot execute agent OS commands; used for `:PUT_ATT`, reading variables, setting queues.
- **`process`**: Main execution script passed to the target agent OS interpreter.
- **`post_process`**: Executed after the agent finishes. Evaluates `:GET_UC_OBJECT_STATUS()` and return codes (`&RETCODE#`).

---

## 2. `JOBP` (Workflows)

Workflows orchestrate tasks, parallel branches, conditions, and dependencies.

### Top-Level Structure

```json
{
  "name": "JOBP.NIGHTLY.ETL",
  "type": "JOBP",
  "general_attributes": {
    "title": "Nightly ETL Orchestration",
    "queue": "CLIENT_QUEUE"
  },
  "workflow_definitions": [
    {
      "line_number": 1,
      "object_name": "<START>",
      "object_type": "<START>",
      "row": 1,
      "column": 1,
      "active": true
    },
    {
      "line_number": 2,
      "object_name": "JOBS.UNIX.EXTRACT",
      "object_type": "JOBS_UNIX",
      "alias": "STEP_1_EXTRACT",
      "row": 1,
      "column": 2,
      "active": true,
      "calendar_conditions": [
        {
          "calendar_name": "CAL.GERMANY.WORKDAYS",
          "calendar_keyword": "WORKDAYS",
          "action": "EXECUTE"
        }
      ]
    },
    {
      "line_number": 3,
      "object_name": "JOBS.UNIX.LOAD",
      "object_type": "JOBS_UNIX",
      "alias": "STEP_2_LOAD",
      "row": 1,
      "column": 3,
      "active": true
    },
    {
      "line_number": 4,
      "object_name": "<END>",
      "object_type": "<END>",
      "row": 1,
      "column": 4,
      "active": true
    }
  ],
  "line_conditions": [
    {
      "workflow_line_number": 2,
      "predecessor_line_number": 1,
      "ok_status": "ANY_OK",
      "else_action": "BLOCK"
    },
    {
      "workflow_line_number": 3,
      "predecessor_line_number": 2,
      "ok_status": "ENDED_OK",
      "else_action": "ABEND"
    },
    {
      "workflow_line_number": 4,
      "predecessor_line_number": 3,
      "ok_status": "ENDED_OK",
      "else_action": "ABEND"
    }
  ]
}
```

### Inspecting Workflow Dependencies
- `workflow_definitions` defines each node by `line_number`.
- `line_conditions` links node `workflow_line_number` back to `predecessor_line_number`.
- When inserting a new task, find the max `line_number`, assign `max_line + 1`, and update existing `line_conditions` to redirect edges.

---

## 3. `JSCH` (Schedules)

Schedules trigger jobs or workflows on predefined time intervals or calendar schedules.

```json
{
  "name": "JSCH.HOURLY.COLLECTOR",
  "type": "JSCH",
  "general_attributes": {
    "title": "Hourly Data Collector Schedule",
    "queue": "CLIENT_QUEUE"
  },
  "tasks": [
    {
      "task_number": 1,
      "object_name": "JOBP.DATA.SYNC",
      "start_time": "08:00:00",
      "active": true,
      "calendar": "CAL.GLOBAL.STANDARD",
      "calendar_keyword": "ALL_DAYS"
    },
    {
      "task_number": 2,
      "object_name": "JOBP.DATA.CLEANUP",
      "start_time": "22:00:00",
      "active": true
    }
  ]
}
```

---

## 4. `VARA` (Variables)

Variable objects store static key-values, SQL lookups, file lists, or system configs.

### Static VARA (`VARA.STATIC`)
```json
{
  "name": "VARA.SYSTEM.ENDPOINTS",
  "type": "VARA",
  "variable_attributes": {
    "variable_type": "STATIC",
    "data_type": "STRING",
    "scope": "LOCAL"
  },
  "static_values": {
    "PROD_API": { "value_1": "https://api.prod.example.com", "value_2": "TokenA" },
    "DEV_API":  { "value_1": "https://api.dev.example.com",  "value_2": "TokenB" }
  }
}
```

### SQL VARA (`VARA.SQL`)
```json
{
  "name": "VARA.SQL.ACTIVE_USERS",
  "type": "VARA",
  "variable_attributes": {
    "variable_type": "SQL",
    "connection": "CONN.DB.ORACLE_HR",
    "sql_statement": "SELECT user_id, user_email FROM employees WHERE status = 'ACTIVE'"
  }
}
```

---

## 5. `JOBF` (File Transfers)

Transfers files between agents.

```json
{
  "name": "JOBF.SEND.CSV",
  "type": "JOBF",
  "file_transfer_attributes": {
    "source_host": "LINUX_SOURCE_AGENT",
    "source_login": "LOGIN.LINUX.USER",
    "source_file": "/var/data/export_*.csv",
    "destination_host": "WIN_DEST_AGENT",
    "destination_login": "LOGIN.WIN.USER",
    "destination_file": "D:\\Incoming\\export_*.csv",
    "code_table": "UC_STANDARD",
    "overwrite_existing_file": true
  }
}
```

---

## 6. Structured Documentation (`_STRUKTUR` / `_BSH`)

In Bosch UC4 environments, object documentation is frequently stored in structured XML format inside `documentation`:
- Standard clients: Key `_STRUKTUR`
- Clients `1111` and `2222`: Key `_BSH`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Content>
    <HINTS_CHARACTERISTICS>
        <Hint key="Application">Warehouse Logistics</Hint>
        <Hint key="Responsible">Team Alpha</Hint>
        <Hint key="Contact">team-alpha@bosch.com</Hint>
    </HINTS_CHARACTERISTICS>
    <ver_hist>
        <entry author="DIM3HC" date="2026-09-24 10:15:00" comment="Updated batch processing parameters"/>
    </ver_hist>
</Content>
```

### Parsing & Modifying Documentation in Python
```python
import xml.etree.ElementTree as ET

def append_version_history(doc_xml_str: str, author: str, comment: str, date_str: str) -> str:
    """Appends a new version entry to structured XML documentation."""
    root = ET.fromstring(doc_xml_str)
    hist = root.find("ver_hist")
    if hist is None:
        hist = ET.SubElement(root, "ver_hist")
    entry = ET.SubElement(hist, "entry")
    entry.set("author", author)
    entry.set("date", date_str)
    entry.set("comment", comment)
    return ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
```
