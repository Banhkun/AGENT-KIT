# Plug-and-Play Python Code Recipes for UC4 / Automic

All recipes in this guide assume that `automic.connection(...)` has **already been initialized** by the user and `client_id` is passed or available in scope.

---

## Table of Contents
1. [Recipe 1: Bulk Object Search & Export to Excel/CSV](#recipe-1-bulk-object-search--export-to-excelcsv)
2. [Recipe 2: Execute Job, Poll Status & Pull Report](#recipe-2-execute-job-poll-status--pull-report)
3. [Recipe 3: Batch Script Search & Regex Replacement](#recipe-3-batch-script-search--regex-replacement)
4. [Recipe 4: Workflow (JOBP) Hierarchy & Dependency Inspection](#recipe-4-workflow-jobp-hierarchy--dependency-inspection)
5. [Recipe 5: Mass Update Static Variable (VARA) Entries](#recipe-5-mass-update-static-variable-vara-entries)
6. [Recipe 6: Ad-hoc UC4 Script Runner](#recipe-6-ad-hoc-uc4-script-runner)
7. [Recipe 7: Where-Used & Scheduler Grouping Query](#recipe-7-where-used--scheduler-grouping-query)

---

## Recipe 1: Bulk Object Search & Export to Excel/CSV

Searches for all objects of a given type and regex pattern, extracting attributes into a pandas DataFrame.

```python
import re
import pandas as pd
import automic_rest as automic

def search_and_export_objects(client_id, obj_type="JOBS", pattern=r"^JOBS\.SAP\..*"):
    regex = re.compile(pattern)
    
    payload = {
        "filters": [
            {"field": "type", "op": "equals", "value": obj_type}
        ],
        "max_results": 9999
    }
    
    search_res = automic.findObjects(client_id=int(client_id), body=payload)
    items = search_res.get("data", [])
    
    matched_records = []
    for item in items:
        name = item.get("name", "")
        if regex.search(name):
            matched_records.append({
                "name": name,
                "type": item.get("type"),
                "title": item.get("title", ""),
                "folder": item.get("folder", "")
            })
            
    df = pd.DataFrame(matched_records)
    df.to_csv("matching_objects.csv", index=False)
    return df
```

---

## Recipe 2: Execute Job, Poll Status & Pull Report

Triggers execution of a job or workflow, polls the status until completion, and downloads the execution report if it fails or completes.

```python
import time
import automic_rest as automic

def run_job_and_wait(client_id, object_name="JOBS.WIN.SAMPLE_TEST", poll_interval=5, max_wait=300):
    client = int(client_id)
    
    exec_res = automic.executeObject(
        client_id=client,
        body={"object_name": object_name, "execution_option": "execute"}
    )
    
    run_id = exec_res.get("run_id")
    if not run_id:
        raise RuntimeError(f"Failed to execute {object_name}: {exec_res}")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        exec_info = automic.getExecution(client_id=client, run_id=run_id)
        status_code = exec_info.get("status")
        status_text = exec_info.get("status_text")
        
        # 1900 = ENDED_OK
        if status_code == 1900:
            report = automic.listReportContent(client_id=client, run_id=run_id, report_type="REP")
            return True, status_code, report
        
        # 1800 - 1899 = ABEND / Failure
        if 1800 <= status_code <= 1899:
            report = automic.listReportContent(client_id=client, run_id=run_id, report_type="REP")
            return False, status_code, report
        
        time.sleep(poll_interval)
        
    raise TimeoutError(f"Job {object_name} timed out after {max_wait} seconds.")
```

---

## Recipe 3: Batch Script Search & Regex Replacement

Safely searches inside `process` scripts across multiple JOBS objects and replaces strings with dry-run support.

```python
import re
import automic_rest as automic

def mass_replace_in_jobs(
    client_id,
    job_names=None,
    search_regex=r"/data/old_path/",
    replacement_str="/data/new_path/",
    dry_run=True
):
    client = int(client_id)
    compiled_re = re.compile(search_regex)
    
    for job_name in (job_names or []):
        try:
            resp = automic.getObjects(client_id=client, object_name=job_name)
            if resp.status != 200 or not resp.response:
                continue
            
            obj_data = resp.response.get("data", {}).get("jobs", {})
            scripts = obj_data.get("scripts", {})
            process_script = scripts.get("process", "")
            
            if not compiled_re.search(process_script):
                continue
                
            new_script = compiled_re.sub(replacement_str, process_script)
            
            if dry_run:
                print(f"[DRY-RUN] Match found in {job_name}, would update.")
            else:
                scripts["process"] = new_script
                obj_data["scripts"] = scripts
                obj_data.pop("metadata", None)
                
                automic.postObjects(
                    client_id=client,
                    body=obj_data,
                    query="overwrite_existing_objects=true"
                )
                print(f"[UPDATED] Successfully updated {job_name}")
        except Exception as e:
            print(f"[ERROR] Failed processing {job_name}: {e}")
```

---

## Recipe 4: Workflow (JOBP) Hierarchy & Dependency Inspection

Traverses a `JOBP` workflow definition and extracts its tasks and dependency chains.

```python
import automic_rest as automic

def inspect_workflow_tasks(client_id, workflow_name="JOBP.NIGHTLY.ETL"):
    resp = automic.getObjects(client_id=int(client_id), object_name=workflow_name)
    jobp_data = resp.response.get("data", {}).get("jobp", {}) if resp.response else {}
    
    nodes = jobp_data.get("workflow_definitions", [])
    edges = jobp_data.get("line_conditions", [])
    
    node_map = {n["line_number"]: n.get("object_name", "<UNKNOWN>") for n in nodes}
    
    tasks = []
    for node in nodes:
        line_no = node["line_number"]
        name = node.get("object_name")
        alias = node.get("alias", "")
        tasks.append({
            "line_number": line_no,
            "object_name": name,
            "alias": alias,
            "active": node.get("active", 1)
        })
        
    deps = []
    for edge in edges:
        deps.append({
            "target": node_map.get(edge["workflow_line_number"]),
            "predecessor": node_map.get(edge["predecessor_line_number"]),
            "status": edge.get("ok_status", "ANY_OK")
        })
        
    return tasks, deps
```

---

## Recipe 5: Mass Update Static Variable (VARA) Entries

Reads and updates key-value pairs in a `VARA.STATIC` object.

```python
import automic_rest as automic

def update_vara_static(client_id, vara_name="VARA.CONFIG.PARAMS", new_entries=None):
    """
    Updates or inserts key-value pairs into a VARA.STATIC object.
    new_entries format: {"KEY1": "VALUE1", "KEY2": "VALUE2"}
    """
    client = int(client_id)
    resp = automic.getObjects(client_id=client, object_name=vara_name)
    vara_obj = resp.response.get("data", {}).get("vara", {})
    
    static_vals = vara_obj.setdefault("static_values", {})
    for k, v in (new_entries or {}).items():
        if k in static_vals and isinstance(static_vals[k], dict):
            static_vals[k]["value_1"] = str(v)
        else:
            static_vals[k] = {"value_1": str(v)}
            
    vara_obj.pop("metadata", None)
    
    res = automic.postObjects(
        client_id=client,
        body=vara_obj,
        query="overwrite_existing_objects=true"
    )
    return res
```

---

## Recipe 6: Ad-hoc UC4 Script Runner

Executes dynamic UC4 script blocks directly in the engine without needing a saved JOBS definition.

```python
import automic_rest as automic

def execute_adhoc_script(client_id, script_code, queue="CLIENT_QUEUE"):
    payload = {
        "script": script_code,
        "queue": queue
    }
    return automic.activateScript(client_id=int(client_id), body=payload)
```

---

## Recipe 7: Where-Used & Scheduler Grouping Query

Finds parent schedulers for a batch of jobs, groups them by scheduler to avoid duplicate queries, and retrieves their line configuration (including the `active` flag).

```python
from collections import defaultdict
import automic_rest as automic

def get_jobs_parent_scheduler_status(client_id, job_names):
    client = int(client_id)
    scheduler_to_jobs = defaultdict(list)
    no_parent_jobs = []

    # 1. Map each job to its parent JSCH(s)
    for job in job_names:
        usage = automic.usageObject(client_id=client, object_name=job)
        refs = usage.response.get("references", []) if (usage.status == 200 and usage.response) else []
        jschs = [r["name"] for r in refs if r.get("type") == "JSCH"]
        if jschs:
            for s in jschs:
                scheduler_to_jobs[s].append(job)
        else:
            no_parent_jobs.append(job)

    # 2. Fetch each unique scheduler only once
    rows = []
    for jsch_name, jobs in scheduler_to_jobs.items():
        resp = automic.getObjects(client_id=client, object_name=jsch_name)
        if resp.status != 200 or not resp.response:
            continue
        
        jsch_data = resp.response.get("data", {}).get("jsch", {})
        wf_defs = jsch_data.get("workflow_definitions", [])

        for job in jobs:
            matches = [d for d in wf_defs if d.get("object_name") == job]
            for m in matches:
                raw_active = m.get("active")
                rows.append({
                    "job_name": job,
                    "scheduler": jsch_name,
                    "active_in_sched": (raw_active in (1, True, "1")),
                    "active_raw": raw_active,
                    "line_number": m.get("line_number"),
                    "start_time": m.get("earliest_start_time")
                })

    for job in no_parent_jobs:
        rows.append({
            "job_name": job,
            "scheduler": "NONE",
            "active_in_sched": False,
            "active_raw": None,
            "line_number": None,
            "start_time": None
        })

    return rows
```
