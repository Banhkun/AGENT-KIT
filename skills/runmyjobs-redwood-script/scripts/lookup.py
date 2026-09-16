#!/usr/bin/env python3
"""Query the bundled Redwood model.json instead of loading it into context.

The full model (~450 entities, thousands of fields, ~700 SchedulerSession lookup
methods) is far too large to read as a reference file. Call this to pull only the
slice needed for the task at hand.

Usage:
  python lookup.py class JobDefinition      # fields, methods, supertypes
  python lookup.py find '*chain*'           # entities matching pattern
  python lookup.py session getJob*          # SchedulerSession methods
  python lookup.py related Job              # relations from/to an entity
"""

import argparse
import json
import re
import sys
from pathlib import Path

MODEL = Path(__file__).resolve().parent.parent / "assets" / "model.json"

def load():
    with open(MODEL, encoding="utf-8") as f:
        return json.load(f)

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["class", "find", "session", "related"])
    p.add_argument("query", help="Entity name, pattern, or method prefix")
    args = p.parse_args()
    model = load()

    if args.command == "class":
        classes = model.get("classes", {})
        key = None
        for k in classes:
            if k.lower() == args.query.lower():
                key = k
                break
        if not key:
            for k in classes:
                if args.query.lower() in k.lower():
                    key = k
                    break
        if not key:
            print(f"No class matching {args.query!r}")
            sys.exit(1)
        cls = classes[key]
        print(f"=== {key} ===")
        if cls.get("extends"):
            print("extends:", ", ".join(cls["extends"]))
        print("\nFields:")
        for f in cls.get("fields", []):
            extra = " (ref)" if f.get("ref") else ""
            print(f"  {f['name']}: {f.get('type', '?')}{extra}")
        print("\nMethods:")
        for m in cls.get("methods", []):
            print(f"  {m.get('name')}{m.get('signature', '()')}")

    elif args.command == "find":
        pat = args.query.replace("*", ".*")
        rx = re.compile(pat, re.I)
        for name in sorted(model.get("classes", {})):
            if rx.search(name):
                print(name)

    elif args.command == "session":
        methods = model.get("session_methods", {})
        q = args.query.lower()
        for name, info in sorted(methods.items()):
            if q in name.lower() or q in str(info.get("returns", "")).lower():
                print(f"{name}{info.get('signature', '()')} -> {info.get('returns', '?')}")

    elif args.command == "related":
        classes = model.get("classes", {})
        key = None
        for k in classes:
            if k.lower() == args.query.lower():
                key = k
                break
        if not key:
            print(f"No class matching {args.query!r}")
            sys.exit(1)
        rels = classes[key].get("relations", [])
        if not rels:
            print("(no relations listed)")
        for r in rels:
            print(f"  {r.get('name')} -> {r.get('relates_to')} ({r.get('verb', '')})")

if __name__ == "__main__":
    main()
