# Command Purpose & Operational Transparency

## Explicit Purpose Requirement
- Whenever proposing or executing a command (e.g. terminal execution, script run, network request), the agent **MUST** explicitly state:
  1. **The Purpose**: What the command accomplishes and why it is necessary for the current task.
  2. **The Target / Outcome**: What file, directory, or service is being modified or queried.
- Never run opaque commands without explaining the rationale to the user in the accompanying message or summary.
