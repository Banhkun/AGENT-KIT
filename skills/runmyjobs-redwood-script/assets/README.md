# assets/

`model.json` (~600 KB) is the Redwood Data Model dump used by `scripts/lookup.py`.

It is intentionally not committed via the automated PR path because of size limits in the push tool.

**To add it:**
1. Download or generate `model.json` from the local skill (`/home/workdir/.grok/skills/runmyjobs-redwood-script/assets/model.json`).
2. Upload it via the GitHub UI into `skills/runmyjobs-redwood-script/assets/` on this branch, or
3. Use `git` locally with a normal push.

The skill works without it for documentation purposes; the lookup script requires it for live queries.
