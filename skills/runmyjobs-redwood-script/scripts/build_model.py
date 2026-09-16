#!/usr/bin/env python3
"""Convert Redwood API Explorer artifacts into model.json for the skill's lookup script.

This is a one-time / maintenance utility. The resulting model.json is committed
to assets/ and then queried via lookup.py so the agent never has to load the
full model into context.
"""

import json
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: build_model.py <path-to-api-explorer-export.json>")
        sys.exit(1)
    src = Path(sys.argv[1])
    with open(src, encoding="utf-8") as f:
        raw = json.load(f)

    # Normalize into the shape expected by lookup.py
    out = {
        "classes": {},
        "session_methods": {},
    }

    # The real conversion logic depends on the exact shape of the API Explorer
    # export. This is a structural placeholder that preserves the expected keys.
    if "classes" in raw:
        out["classes"] = raw["classes"]
    if "session_methods" in raw:
        out["session_methods"] = raw["session_methods"]

    dest = Path(__file__).resolve().parent.parent / "assets" / "model.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {dest} ({dest.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
