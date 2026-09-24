# UC4 / Automic Automation Execution Status Codes

In UC4 / Automic Automation Engine, executions are identified by a unique `run_id` and report numeric status codes (`status` / `status_code`) accompanied by textual status descriptions (`status_text`).

---

## Status Code Ranges Overview

| Range | General Category | Typical Action / Handling |
| :--- | :--- | :--- |
| **1900** | **ENDED_OK** | Normal successful completion. Safe to proceed. |
| **1800 – 1899** | **Abnormal End / ABEND** | Failure (e.g., script error, OS return code, fault). Alert / Retry / Investigate. |
| **1500 – 1600** | **Active / Running** | Currently executing on agent or in engine. Poll and wait. |
| **1300 – 1499** | **Waiting / Blocked** | Waiting for predecessor, sync, resource, queue, or prompt. |
| **1681 – 1712** | **Waiting / Conditions** | Waiting for start time, manual release, host, or calendar. |
| **1910 – 1999** | **Ended with Warning / Canceled** | Ended with custom return code, user canceled, skipped, or deactivated. |

---

## Complete Status Code Reference Table

| Code | Status Text | Description & Script Handling |
| :--- | :--- | :--- |
| **1300** | `WAITING_FOR_PREDECESSOR` | Workflow task waiting for predecessor task(s) to finish. |
| **1301** | `WAITING_FOR_SYNC` | Task is waiting for a Sync object state. |
| **1510** | `TRANSFERRED` | File transfer or job data transferred to target agent. |
| **1520** | `READY_FOR_GENERATION` | Task queued for script generation. |
| **1540** | `STARTING` | Task is initializing and being dispatched to agent. |
| **1550** | `ACTIVE` | Task is currently running. |
| **1560** | `WAITING_FOR_AGENT` | Agent busy or queue slot waiting. |
| **1570** | `GENERATING` | Pre-process script generation in progress. |
| **1572** | `WAITING_FOR_ROLLBACK` | Waiting for rollback action execution. |
| **1590** | `WAITING_FOR_PROMPT` | Interactive prompt set / PRPT waiting for human input. |
| **1681** | `WAITING_FOR_START_TIME` | Scheduled for a specific future start time. |
| **1686** | `WAITING_FOR_HOST` | Target Agent / Host is offline or unavailable. |
| **1687** | `WAITING_FOR_QUEUE` | Queue limit reached; waiting for available slot. |
| **1690** | `WAITING_FOR_MANUAL_RELEASE`| Task held manually (`HOLD` / breakpoint); requires manual unhold. |
| **1700** | `WAITING_FOR_CALENDAR` | Task calendar condition not met; waiting for valid date. |
| **1710** | `BLOCKED` | Workflow branch blocked due to predecessor condition failure. |
| **1800** | `ENDED_NOT_OK` | General abnormal termination (ABEND). OS exit code > 0. |
| **1801** | `ENDED_VANISHED` | Agent lost contact or process disappeared unexpectedly. |
| **1802** | `ENDED_FAULT` | Engine fault, missing include, or syntax error in script. |
| **1810** | `ENDED_TIMEOUT` | Task exceeded max runtime (MRT). |
| **1815** | `ENDED_TOO_EARLY` | Task finished before min runtime (SRT). |
| **1820** | `FAULT_AGENT_INACTIVE` | Target agent was inactive when job attempted to launch. |
| **1821** | `FAULT_LOGIN` | Invalid login object, user, or password on target agent. |
| **1850** | `ENDED_CANCEL` | Task canceled by user or workflow rule. |
| **1851** | `ENDED_INACTIVATED` | Task deactivated while in error state. |
| **1856** | `ENDED_STOPPED` | Job stopped due to engine emergency stop. |
| **1900** | `ENDED_OK` | Normal successful completion (Return Code 0). |
| **1910** | `ENDED_SKIPPED` | Workflow task skipped per condition or calendar rule. |
| **1911** | `ENDED_ROLLBACK` | Task rolled back successfully. |
| **1920** | `ENDED_CUSTOM_RC` | Ended with custom return code configured as OK. |
| **1930** | `ENDED_FORCE` | Task was forced to completion by operator. |

---

## Helper Function for Python Scripts

```python
def classify_status(status_code: int) -> str:
    """Classifies UC4 numeric execution status."""
    if status_code == 1900:
        return "SUCCESS"
    elif 1800 <= status_code <= 1899:
        return "ABEND"
    elif 1500 <= status_code <= 1600:
        return "RUNNING"
    elif 1300 <= status_code <= 1499 or 1681 <= status_code <= 1712:
        return "WAITING"
    elif status_code in (1910, 1920, 1930):
        return "COMPLETED_SPECIAL"
    return "UNKNOWN"

def is_terminal_status(status_code: int) -> bool:
    """Returns True if the execution has reached a final state."""
    return status_code >= 1800
```
