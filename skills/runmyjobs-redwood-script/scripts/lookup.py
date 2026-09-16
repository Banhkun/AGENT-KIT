#!/usr/bin/env python3
"""Query the bundled Redwood model.json instead of loading it into context.

The full model (~450 entities, thousands of fields, ~700 SchedulerSession lookup
methods) is far too large to read as a reference file. Call this to pull only the
slice needed for the task at hand.

Usage:
  python scripts/lookup.py session <Entity>     # how to get/create one
  python scripts/lookup.py class <Entity>       # fields + methods once you have one
  python scripts/lookup.py search <substring>   # find entities by name
  python scripts/lookup.py methods <substring>  # find SchedulerSession methods
"""

import json
import sys
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent.parent / "assets" / "model.json"

def load_model():
    with open(MODEL_PATH, encoding="utf-8") as f:
        return json.load(f)

def cmd_session(model, entity):
    """Print SchedulerSession methods that return or create the entity."""
    methods = model.get("session_methods", {})
    hits = []
    for name, info in methods.items():
        ret = info.get("returns", "")
        if entity.lower() in ret.lower() or entity.lower() in name.lower():
            hits.append((name, info))
    if not hits:
        print(f"No session methods found for {entity}")
        return
    for name, info in sorted(hits):
        print(f"{name}{info.get('signature', '()')}")
        if info.get("doc"):
            print(f"  {info['doc'][:200]}")

def cmd_class(model, entity):
    """Print fields and methods of the entity class."""
    classes = model.get("classes", {})
    # fuzzy match
    key = None
    for k in classes:
        if k.lower() == entity.lower():
            key = k
            break
    if not key:
        for k in classes:
            if entity.lower() in k.lower():
                key = k
                break
    if not key:
        print(f"Entity not found: {entity}")
        return
    cls = classes[key]
    print(f"=== {key} ===")
    if cls.get("extends"):
        print(f"extends: {', '.join(cls['extends'])}")
    print("\nFields:")
    for f in cls.get("fields", []):
        t = f.get("type", "?")
        ref = " (ref)" if f.get("ref") else ""
        print(f"  {f['name']}: {t}{ref}")
    print("\nMethods:")
    for m in cls.get("methods", []):
        print(f"  {m.get('name', '?')}{m.get('signature', '()')}")

def cmd_search(model, substr):
    classes = model.get("classes", {})
    hits = [k for k in classes if substr.lower() in k.lower()]
    for h in sorted(hits):
        print(h)

def cmd_methods(model, substr):
    methods = model.get("session_methods", {})
    hits = [(n, i) for n, i in methods.items() if substr.lower() in n.lower()]
    for name, info in sorted(hits):
        print(f"{name}{info.get('signature', '()')}")

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1].lower()
    arg = sys.argv[2]
    model = load_model()
    if cmd == "session":
        cmd_session(model, arg)
    elif cmd == "class":
        cmd_class(model, arg)
    elif cmd == "search":
        cmd_search(model, arg)
    elif cmd == "methods":
        cmd_methods(model, arg)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
