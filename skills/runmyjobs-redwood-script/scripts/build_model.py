#!/usr/bin/env python3
"""Convert Redwood API Explorer artifacts into model.json for the skill's lookup.py.

Inputs:
  schema.md       "## ClassName" headers + "FieldName: FieldType" lines (one class
                   per header). Ships as a single line with literal \\n escapes in
                   some hosted copies -- handled the same way the explorer's own
                   parseSchemaMd() handles it.
  relations.json  {"edges": [{"from","method","to"}, ...]}. `method` is a raw
                   signature fragment such as "RWIterable<JobChainStep> getJobChainSteps"
                   or "JobDefinition getJobDefinitionByName" -- the trailing
                   whitespace-separated token is the method name; everything before
                   it is return-type/modifier noise and is discarded.
  pkg-tree.json   optional. {"classHierarchy": [...], "interfaceHierarchy": [...]}
                   supertype tree. Safe to omit -- classes just get an empty
                   "extends" list until it's supplied.

The crawl produces two very different populations of `from` classes:
  - ~450 real data-model entities (JobDefinition, JobChain, ...) -- these become
    model["classes"].
  - SchedulerSession -- the API entry point. Its ~700 edges are exactly the
    getXByName/getXByUniqueId/createX lookups a script needs and are otherwise
    undocumented anywhere but the live JavaDoc, so they get their own top-level
    model["session"] list rather than being dropped.
  - Everything else (BusinessKeyResolver, *Callback, *Comp mixins, internal
    plumbing interfaces) is internal machinery, not something a script calls
    directly, and is dropped. See DROP_PREFIXES / KEEP_EXTRA below if a future
    task needs one of them back.

Usage:
  python build_model.py --schema schema.md --relations relations.json \
                        [--tree pkg-tree.json] --out model.json
"""

import argparse
import json
import re
import sys
from collections import defaultdict

# Classes worth keeping even though they're not in schema.md and aren't
# SchedulerSession -- real interfaces referenced in the skill's own prose
# (entities-and-lookup.md's PartitionableObject row, etc).
KEEP_EXTRA = {"PartitionableObject", "SchedulerEntity", "NamedRootObject"}


def parse_schema_md(text):
    """Mirrors the explorer's parseSchemaMd(), including the escaped-newline case."""
    normalized = text.strip().strip("'\"")
    normalized = re.sub(r"\\r\\n|\\n", "\n", normalized)
    classes, current = defaultdict(list), None
    for raw in normalized.splitlines():
        line = raw.strip()
        if not line:
            continue
        header = re.match(r"^##\s+(.+)$", line)
        if header:
            current = header.group(1).strip()
            classes.setdefault(current, [])
            continue
        if current is None:
            continue
        field = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+)$", line)
        if field:
            classes[current].append(
                {"name": field.group(1), "type": field.group(2).strip()}
            )
    return dict(classes)


def clean_method_name(raw):
    """'RWIterable<JobChainStep> getJobChainSteps' -> 'getJobChainSteps'.

    The trailing whitespace-separated token is always the identifier -- return
    types and modifiers never contain a space inside their own token (generics
    use <> with no internal space in this dump), so this is safe even for
    '<T extends SchedulerEntity> RWIterable<T> executeObjectQuery'.
    """
    return raw.split()[-1] if raw.strip() else raw


def classify(name):
    m = re.match(r"^[a-z]+", name)
    return m.group(0) if m else "other"


def parse_relations(data, schema_classes):
    edges = data if isinstance(data, list) else data.get("edges", [])
    class_methods = defaultdict(list)
    session_methods = []
    dropped = defaultdict(int)

    seen_class = set()
    seen_session = set()

    for e in edges:
        if not all(k in e for k in ("from", "method", "to")):
            continue
        src, to = e["from"], e["to"]
        name = clean_method_name(e["method"])
        verb = classify(name)

        if src in schema_classes or src in KEEP_EXTRA:
            key = (src, name, to)
            if key in seen_class:
                continue
            seen_class.add(key)
            class_methods[src].append({"name": name, "verb": verb, "returns": to})
        elif src == "SchedulerSession":
            key = (name, to)
            if key in seen_session:
                continue
            seen_session.add(key)
            session_methods.append({"name": name, "verb": verb, "relates_to": to})
        else:
            dropped[src] += 1

    for methods in class_methods.values():
        methods.sort(key=lambda m: m["name"])
    session_methods.sort(key=lambda m: m["name"])

    return dict(class_methods), session_methods, dropped


def walk_tree(nodes, parent, out):
    for node in nodes or []:
        name = node.get("name")
        if name:
            if parent:
                out[name].add(parent)
            for ae in node.get("alsoExtends") or []:
                if ae.get("name"):
                    out[name].add(ae["name"])
        walk_tree(node.get("children"), name, out)


def parse_tree(data):
    out = defaultdict(set)
    walk_tree(data.get("classHierarchy"), None, out)
    walk_tree(data.get("interfaceHierarchy"), None, out)
    return {k: sorted(v) for k, v in out.items()}


def load(path):
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        print(f"warning: could not read {path}: {exc}", file=sys.stderr)
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--relations", required=True)
    ap.add_argument("--tree")
    ap.add_argument("--out", default="model.json")
    args = ap.parse_args()

    schema_text = load(args.schema)
    rel_text = load(args.relations)
    tree_text = load(args.tree) if args.tree else None

    if not schema_text or not rel_text:
        sys.exit("error: --schema and --relations are both required and must be readable")

    fields = parse_schema_md(schema_text)
    schema_classes = set(fields)
    class_methods, session_methods, dropped = parse_relations(
        json.loads(rel_text), schema_classes
    )
    extends = parse_tree(json.loads(tree_text)) if tree_text else {}

    names = schema_classes | set(class_methods) | set(extends)

    classes = {}
    for name in sorted(names):
        flds = [{**f, "ref": f["type"] in schema_classes} for f in fields.get(name, [])]
        classes[name] = {
            "fields": flds,
            "methods": class_methods.get(name, []),
            "extends": extends.get(name, []),
        }

    reverse = defaultdict(list)
    for name, info in classes.items():
        for f in info["fields"]:
            if f["ref"]:
                reverse[f["type"]].append({"from": name, "field": f["name"]})
        for m in info["methods"]:
            if m["returns"] in classes:
                reverse[m["returns"]].append({"from": name, "field": m["name"] + "()"})
    for v in reverse.values():
        v.sort(key=lambda r: (r["from"], r["field"]))

    model = {
        "classes": classes,
        "reverse": dict(reverse),
        "session": session_methods,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(model, fh, separators=(",", ":"), sort_keys=True)

    fielded = sum(1 for c in classes.values() if c["fields"])
    methoded = sum(1 for c in classes.values() if c["methods"])
    top_dropped = sorted(dropped.items(), key=lambda x: -x[1])[:5]
    print(
        f"wrote {args.out}: {len(classes)} classes "
        f"({fielded} with fields, {methoded} with methods), "
        f"{len(session_methods)} SchedulerSession methods"
    )
    if top_dropped:
        print(f"dropped internal/helper sources (top 5): {top_dropped}")


if __name__ == "__main__":
    main()
