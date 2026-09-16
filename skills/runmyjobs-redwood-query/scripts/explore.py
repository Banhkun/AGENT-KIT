#!/usr/bin/env python3
"""RunMyJobs (Redwood) Data Model Explorer & SQL Query Generator.

Allows exploring the Redwood Data Model (462 entities) and automatically generating
optimized ANSI SQL'92 queries for the Redwood Object Query engine.

Usage:
  python explore.py inspect <Entity>            # Fields, types, reference columns, joins
  python explore.py path <Start> <End>          # Shortest relationship path between entities
  python explore.py join <Start> <End>          # Auto-generate ANSI SQL JOIN clause
  python explore.py find <pattern>              # Find entities or fields by pattern
  python explore.py field <fieldName>           # Find entities containing a specific field
  python explore.py check "<SQL>"               # Lint SQL for common Redwood gotchas
"""

import argparse
import fnmatch
import json
import os
import re
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
            f"model.json not found at {path}\n"
            "Ensure assets/model.json is present in the skill directory."
        )


def resolve_entity(model, name):
    classes = model["classes"]
    if name in classes:
        return name
    lowered = {k.lower(): k for k in classes}
    if name.lower() in lowered:
        return lowered[name.lower()]
    near = [k for k in classes if name.lower() in k.lower()][:10]
    sys.exit(
        f"Unknown entity {name!r}"
        + (f" — did you mean: {', '.join(near)}" if near else "")
    )


def make_alias(entity_name, used_aliases):
    # Derive acronym or lowercase name
    base = "".join(c for c in entity_name if c.isupper()).lower()
    if not base or len(base) == 1:
        base = entity_name[:3].lower()
    alias = base
    idx = 1
    while alias in used_aliases:
        alias = f"{base}{idx}"
        idx += 1
    used_aliases.add(alias)
    return alias


def cmd_inspect(model, args):
    entity = resolve_entity(model, args.name)
    info = model["classes"][entity]

    print(f"# Entity: {entity}")
    if info.get("extends"):
        print(f"Extends/Implements: {', '.join(info['extends'])}")

    fields = info.get("fields", [])
    ref_fields = [f for f in fields if f.get("ref")]
    scalar_fields = [f for f in fields if not f.get("ref")]

    if ref_fields:
        print("\n## Reference Columns (Store UniqueId -> Require JOIN or ID bind)")
        for f in ref_fields:
            print(f"  {entity}.{f['name']} -> {f['type']}.UniqueId")

    if scalar_fields:
        print("\n## Scalar Columns (Directly filterable)")
        for f in scalar_fields:
            print(f"  {entity}.{f['name']}: {f['type']}")

    rev = model.get("reverse", {}).get(entity, [])
    if rev:
        print("\n## Referenced By (Other entities pointing here)")
        # Group by referring entity
        by_entity = {}
        for r in rev:
            by_entity.setdefault(r["from"], []).append(r["field"])
        for source, flds in sorted(by_entity.items()):
            print(f"  {source} via {', '.join(flds)}")


def get_edges(model, name):
    """Returns list of (target_entity, field_name, direction: 'forward' | 'reverse')."""
    info = model["classes"].get(name, {})
    edges = []
    # Forward: this entity has a field pointing to target entity
    for f in info.get("fields", []):
        if f.get("ref") and f.get("type") in model["classes"]:
            edges.append((f["type"], f["name"], "forward"))
    # Reverse: another entity has a field pointing to this entity
    for r in model.get("reverse", {}).get(name, []):
        if r["from"] in model["classes"]:
            edges.append((r["from"], r["field"], "reverse"))
    return edges


def find_paths(model, start, end, max_hops=5, limit=5):
    if start == end:
        return []
    queue = deque([(start, [])])
    seen = {start}
    found = []

    while queue:
        node, trail = queue.popleft()
        if len(trail) >= max_hops:
            continue
        for nxt, field, direction in get_edges(model, node):
            step = (nxt, field, direction)
            if nxt == end:
                found.append(trail + [step])
                if len(found) >= limit:
                    return found
                continue
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, trail + [step]))
    return found


def cmd_path(model, args):
    start = resolve_entity(model, args.start)
    end = resolve_entity(model, args.end)

    paths = find_paths(model, start, end, max_hops=args.max_hops, limit=args.limit)
    if not paths:
        print(f"No path found between {start} and {end} within {args.max_hops} hops.")
        return

    print(f"# Relationship paths from {start} to {end}:")
    for i, path in enumerate(paths, 1):
        steps_desc = []
        curr = start
        for nxt, field, direction in path:
            if direction == "forward":
                steps_desc.append(f"--[{curr}.{field} = {nxt}.UniqueId]--> {nxt}")
            else:
                steps_desc.append(f"--[{nxt}.{field} = {curr}.UniqueId]--> {nxt}")
            curr = nxt
        print(f"{i}. {start} " + " ".join(steps_desc))


def cmd_join(model, args):
    start = resolve_entity(model, args.start)
    end = resolve_entity(model, args.end)

    paths = find_paths(model, start, end, max_hops=args.max_hops, limit=1)
    if not paths:
        print(f"No path found between {start} and {end} within {args.max_hops} hops.")
        return

    path = paths[0]
    used_aliases = set()
    aliases = {}

    curr_alias = make_alias(start, used_aliases)
    aliases[start] = curr_alias

    join_clauses = []
    where_clauses = []
    from_tables = [f"{start} {curr_alias}"]

    curr_entity = start
    for nxt_entity, field, direction in path:
        nxt_alias = make_alias(nxt_entity, used_aliases)
        aliases[nxt_entity] = nxt_alias
        from_tables.append(f"{nxt_entity} {nxt_alias}")

        if direction == "forward":
            # curr.field = nxt.UniqueId
            join_clauses.append(
                f"JOIN {nxt_entity} {nxt_alias}\n     ON {curr_alias}.{field} = {nxt_alias}.UniqueId"
            )
            where_clauses.append(f"{curr_alias}.{field} = {nxt_alias}.UniqueId")
        else:
            # nxt.field = curr.UniqueId
            join_clauses.append(
                f"JOIN {nxt_entity} {nxt_alias}\n     ON {nxt_alias}.{field} = {curr_alias}.UniqueId"
            )
            where_clauses.append(f"{nxt_alias}.{field} = {curr_alias}.UniqueId")

        curr_entity = nxt_entity
        curr_alias = nxt_alias

    print(f"-- Generated SQL Join for: {start} -> {end}")
    print("\n-- 1. ANSI JOIN Syntax:")
    print(f"SELECT {aliases[start]}.*\nFROM {start} {aliases[start]}")
    print("\n".join(join_clauses))

    # Add common version filters if relevant
    notes = []
    for ent in [start] + [p[0] for p in path]:
        info = model["classes"].get(ent, {})
        fnames = [f["name"] for f in info.get("fields", [])]
        if "BranchedLLPVersion" in fnames:
            notes.append(f"{aliases[ent]}.BranchedLLPVersion = -1")

    if notes:
        print(f"WHERE " + "\n  AND ".join(notes))

    print("\n-- 2. Equivalent Comma-FROM / WHERE Syntax:")
    print(f"SELECT {aliases[start]}.*\nFROM " + ", ".join(from_tables))
    all_where = where_clauses + notes
    print("WHERE " + "\n  AND ".join(all_where))


def cmd_find(model, args):
    pattern = args.pattern.lower()
    matching_entities = []
    for name in sorted(model["classes"].keys()):
        if fnmatch.fnmatch(name.lower(), f"*{pattern}*"):
            matching_entities.append(name)

    print(f"# Entities matching '*{args.pattern}*':")
    if matching_entities:
        for m in matching_entities:
            print(f"  {m}")
    else:
        print("  (no entity matched)")

    matching_fields = []
    for name, info in sorted(model["classes"].items()):
        for f in info.get("fields", []):
            if fnmatch.fnmatch(f["name"].lower(), f"*{pattern}*"):
                ref_str = f" -> {f['type']}" if f.get("ref") else ""
                matching_fields.append(f"  {name}.{f['name']}: {f['type']}{ref_str}")

    if matching_fields:
        print(f"\n# Fields matching '*{args.pattern}*' (showing up to 25):")
        for mf in matching_fields[:25]:
            print(mf)
        if len(matching_fields) > 25:
            print(f"  ... and {len(matching_fields) - 25} more")


def cmd_field(model, args):
    field_name = args.name.lower()
    matches = []
    for name, info in sorted(model["classes"].items()):
        for f in info.get("fields", []):
            if f["name"].lower() == field_name:
                ref_str = f" -> {f['type']} (Reference column - stores UniqueId)" if f.get("ref") else ""
                matches.append(f"  {name}.{f['name']}: {f['type']}{ref_str}")

    if matches:
        print(f"# Entities carrying field '{args.name}':")
        for m in matches:
            print(m)
    else:
        print(f"No entity carries field '{args.name}'.")


def cmd_check(model, args):
    sql = args.sql
    print(f"# Checking SQL Query for RunMyJobs Pitfalls:\n")
    warnings = []

    # 1. Check bare SELECT *
    if re.search(r"\bSELECT\s+\*\s+FROM\b", sql, re.IGNORECASE):
        warnings.append(
            "[ERROR] Bare 'SELECT *' is rejected by Redwood. Use alias-qualified wildcard: 'SELECT j.* FROM Job j' or select specific columns."
        )

    # 2. Check reference column string comparison
    ref_columns = {
        "Partition": "Partition",
        "ParentApplication": "Application",
        "JobDefinitionType": "JobDefinitionType",
        "LastModifierSubject": "Subject",
        "DefaultQueue": "Queue",
        "ActionSubject": "Subject",
        "CreatedBySubject": "Subject",
        "OwnerSubject": "Subject",
    }
    for col, target_ent in ref_columns.items():
        # Match pattern: alias.Column = '...' or alias.Column LIKE '...'
        pattern = rf"\b\w+\.{col}\s*(=|LIKE)\s*['\"][^'\"]+['\"]"
        match = re.search(pattern, sql, re.IGNORECASE)
        if match:
            warnings.append(
                f"[CRITICAL] Direct string comparison on reference column '{match.group(0)}':\n"
                f"  '{col}' stores the target {target_ent}'s UniqueId (number), not its Name (string).\n"
                f"  This query will silently return 0 rows!\n"
                f"  Fix: JOIN {target_ent} and filter on its Name: e.g. JOIN {target_ent} x ON jd.{col} = x.UniqueId WHERE x.Name = '...'"
            )

    # 3. Check BranchedLLPVersion for JobDefinition / JobChain
    if "JobDefinition" in sql and "BranchedLLPVersion" not in sql:
        warnings.append(
            "[WARNING] JobDefinition queried without 'BranchedLLPVersion = -1'.\n"
            "  This may include uncommitted draft branches. Add 'jd.BranchedLLPVersion = -1' to select current master definitions."
        )

    # 4. Check MasterJobDefinition for tag/sibling queries
    if "ObjectTag" in sql and "JobDefinition" in sql and "MasterJobDefinition" not in sql:
        warnings.append(
            "[NOTE] When querying ObjectTags on JobDefinition, consider adding 'jd.UniqueId = jd.MasterJobDefinition' to avoid duplicate tags on branched/split objects."
        )

    # 5. Check join equality on UniqueId
    # Scan for joins where neither side is UniqueId
    join_matches = re.findall(r"(\b\w+\.\w+)\s*=\s*(\b\w+\.\w+)", sql)
    for left, right in join_matches:
        if left.endswith("UniqueId") or right.endswith("UniqueId"):
            continue
        # If neither side is UniqueId and not literal
        if not left.isdigit() and not right.isdigit() and "'" not in left and "'" not in right:
            warnings.append(
                f"[CAUTION] Join condition '{left} = {right}' does not join on 'UniqueId'.\n"
                f"  In Redwood Object Model, entities almost always join on UniqueId (e.g. jcc.JobDefinition = jd.UniqueId)."
            )

    # 6. Check ORDER BY with table-qualified columns when aliases are defined (prevents ORA-00918)
    order_by_match = re.search(r"\bORDER\s+BY\s+(.+)$", sql, re.IGNORECASE)
    select_match = re.search(r"\bSELECT\s+(.+?)\s+FROM\b", sql, re.IGNORECASE | re.DOTALL)
    if order_by_match and select_match:
        select_part = select_match.group(1)
        order_by_part = order_by_match.group(1)
        # Check if query projects aliases (e.g., "col AS Alias")
        aliases = re.findall(r"\bAS\s+(\w+)", select_part, re.IGNORECASE)
        if aliases and ("." in order_by_part or re.search(r"\b\w+\.\w+", order_by_part)):
            warnings.append(
                "[CRITICAL] 'ORDER BY' uses table-qualified column names or bare table columns when projection aliases are defined:\n"
                f"  Found in ORDER BY: '{order_by_part.strip()}'.\n"
                "  When multiple joined tables share column names (e.g. Name), ordering by table-qualified names\n"
                "  triggers Redwood/Oracle ambiguity error: 'ORA-00918: column ambiguously defined'.\n"
                f"  Fix: ORDER BY the output column alias directly: e.g. ORDER BY {', '.join(aliases[:2])}"
            )

    if not warnings:
        print("✓ No common Redwood SQL anti-patterns detected. Query looks well-formed!")
    else:
        for w in warnings:
            print(f"- {w}\n")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Path to model.json")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    p_inspect = subparsers.add_parser("inspect", help="Inspect entity fields and reference columns")
    p_inspect.add_argument("name", help="Entity name (e.g. JobDefinition)")
    p_inspect.set_defaults(fn=cmd_inspect)

    p_path = subparsers.add_parser("path", help="Find path between two entities")
    p_path.add_argument("start", help="Start entity name")
    p_path.add_argument("end", help="End entity name")
    p_path.add_argument("--max-hops", type=int, default=5, help="Max search hops (default: 5)")
    p_path.add_argument("--limit", type=int, default=3, help="Max paths to return (default: 3)")
    p_path.set_defaults(fn=cmd_path)

    p_join = subparsers.add_parser("join", help="Generate SQL JOIN between two entities")
    p_join.add_argument("start", help="Start entity name")
    p_join.add_argument("end", help="End entity name")
    p_join.add_argument("--max-hops", type=int, default=5, help="Max search hops")
    p_join.set_defaults(fn=cmd_join)

    p_find = subparsers.add_parser("find", help="Find entities or fields matching pattern")
    p_find.add_argument("pattern", help="Search pattern or wildcard (e.g. chain, param, tag)")
    p_find.set_defaults(fn=cmd_find)

    p_field = subparsers.add_parser("field", help="Find which entities carry a given field")
    p_field.add_argument("name", help="Field name (e.g. KeepAmount, Partition)")
    p_field.set_defaults(fn=cmd_field)

    p_check = subparsers.add_parser("check", help="Lint SQL query against Redwood gotchas")
    p_check.add_argument("sql", help="SQL query string to analyze")
    p_check.set_defaults(fn=cmd_check)

    args = parser.parse_args()
    model = load_model(args.model)
    args.fn(model, args)


if __name__ == "__main__":
    main()
