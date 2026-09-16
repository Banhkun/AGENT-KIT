#!/usr/bin/env python3
"""Query the bundled Redwood model.json instead of loading it into context.

The full model (~450 entities, thousands of fields, ~700 SchedulerSession lookup
methods) is far too large to read as a reference file. Call this to pull only the
slice needed for the task at hand.

  python lookup.py class JobDefinition      # fields, methods, supertypes
  python lookup.py find '*chain*'           # class names matching a glob
  python lookup.py field Partition          # every class carrying that field
  python lookup.py refs JobDefinition       # classes/methods pointing AT this one
  python lookup.py session JobDefinition    # SchedulerSession methods that
                                             #   create/look up/relate to this class
  python lookup.py path JobChain Subject    # shortest traversal(s) between classes

Start with `session <Entity>` for "how do I get one of these in the first place",
then `class <Entity>` for "what can I call once I have it", then `path` if getting
from one entity to another isn't a single hop.
"""

import argparse
import fnmatch
import json
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL = os.path.join(HERE, "..", "assets", "model.json")


def load_model(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except OSError:
        sys.exit(
            f"model not found at {path}\n"
            "Generate it with scripts/build_model.py from the API Explorer's "
            "schema.md / relations.json (and pkg-tree.json if available)."
        )


def resolve(model, name):
    """Case-insensitive exact match, else suggest near misses."""
    classes = model["classes"]
    if name in classes:
        return name
    lowered = {k.lower(): k for k in classes}
    if name.lower() in lowered:
        return lowered[name.lower()]
    near = [k for k in classes if name.lower() in k.lower()][:10]
    sys.exit(
        f"unknown class {name!r}"
        + (f" — did you mean: {', '.join(near)}" if near else "")
    )


def cmd_class(model, args):
    name = resolve(model, args.name)
    info = model["classes"][name]
    print(f"# {name}")
    if info["extends"]:
        print(f"extends/implements: {', '.join(info['extends'])}")
    if info["fields"]:
        print("\n## fields")
        for f in info["fields"]:
            arrow = "  ->" if f["ref"] else "   "
            print(f"  {f['name']}: {f['type']}{arrow}")
    if info["methods"]:
        print("\n## methods returning/creating other model classes")
        for m in info["methods"]:
            tag = f" [{m['verb']}]" if m.get("verb") else ""
            print(f"  {m['name']}(){tag} -> {m['returns']}")
    if not info["fields"] and not info["methods"]:
        print("(no fields or relations recorded — check the source dump)")


def cmd_find(model, args):
    pat = args.pattern if any(c in args.pattern for c in "*?[") else f"*{args.pattern}*"
    hits = sorted(
        k for k in model["classes"] if fnmatch.fnmatch(k.lower(), pat.lower())
    )
    print("\n".join(hits) if hits else "(no matches)")


def cmd_field(model, args):
    hits = []
    for name, info in sorted(model["classes"].items()):
        for f in info["fields"]:
            if f["name"].lower() == args.name.lower():
                hits.append(f"{name}.{f['name']}: {f['type']}")
    print("\n".join(hits) if hits else "(no class carries that field)")


def cmd_refs(model, args):
    name = resolve(model, args.name)
    rows = model.get("reverse", {}).get(name, [])
    if not rows:
        print(f"(nothing points at {name})")
        return
    print(f"# classes/methods referencing {name}")
    for r in rows:
        print(f"  {r['from']}.{r['field']}")


def cmd_session(model, args):
    """SchedulerSession methods that create, look up, or otherwise relate to a class.

    `relates_to` mixes return types and parameter types as scraped from the raw
    JavaDoc signature — it answers "what SchedulerSession method involves this
    class" without distinguishing which side of the call it's on. Read the method
    name to tell (getXByY almost always returns X; createX almost always creates X).
    """
    name = resolve(model, args.name)
    rows = [m for m in model.get("session", []) if m["relates_to"] == name]
    if not rows:
        print(f"(no SchedulerSession method involves {name})")
        return
    print(f"# SchedulerSession methods involving {name}")
    for m in rows:
        print(f"  jcsSession.{m['name']}(...)  [{m['verb']}]")


def neighbours(model, name):
    """Forward field refs, class-level methods, and reverse refs as one edge set."""
    info = model["classes"].get(name, {})
    out = []
    for f in info.get("fields", []):
        if f["ref"]:
            out.append((f["type"], f"{name}.{f['name']}", "forward"))
    for m in info.get("methods", []):
        if m["returns"] in model["classes"]:
            out.append((m["returns"], f"{name}.{m['name']}()", "method"))
    for r in model.get("reverse", {}).get(name, []):
        out.append((r["from"], f"{r['from']}.{r['field']}", "reverse"))
    return out


def cmd_path(model, args):
    start = resolve(model, args.start)
    end = resolve(model, args.end)
    if start == end:
        print("same class")
        return
    queue = deque([(start, [])])
    seen = {start}
    found = []
    depth_limit = args.max_hops
    while queue:
        node, trail = queue.popleft()
        if len(trail) >= depth_limit:
            continue
        for nxt, via, kind in neighbours(model, node):
            step = (nxt, via, kind)
            if nxt == end:
                found.append(trail + [step])
                if len(found) >= args.limit:
                    queue.clear()
                    break
                continue
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, trail + [step]))
    if not found:
        print(f"no path from {start} to {end} within {depth_limit} hops")
        return
    for trail in found:
        parts = [start] + [f"--[{via}, {kind}]--> {nxt}" for nxt, via, kind in trail]
        print(" ".join(parts))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("class"); p.add_argument("name"); p.set_defaults(fn=cmd_class)
    p = sub.add_parser("find"); p.add_argument("pattern"); p.set_defaults(fn=cmd_find)
    p = sub.add_parser("field"); p.add_argument("name"); p.set_defaults(fn=cmd_field)
    p = sub.add_parser("refs"); p.add_argument("name"); p.set_defaults(fn=cmd_refs)
    p = sub.add_parser("session"); p.add_argument("name"); p.set_defaults(fn=cmd_session)
    p = sub.add_parser("path")
    p.add_argument("start"); p.add_argument("end")
    p.add_argument("--max-hops", type=int, default=4)
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(fn=cmd_path)

    args = ap.parse_args()
    args.fn(load_model(args.model), args)


if __name__ == "__main__":
    main()
