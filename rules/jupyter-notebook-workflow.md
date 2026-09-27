# Jupyter Notebook (.ipynb) Workflow & Invariants

> [!IMPORTANT]
> **HARNESS RESTRICTION ON .IPYNB**
> The agent's file editing tools (`replace_file_content`, `multi_replace_file_content`) explicitly forbid editing `.ipynb` files. Never attempt ad-hoc JSON parsing, regex splicing, or raw text replacement on `.ipynb` files.

## Core Rules

1. **Jupytext Pairing (`ipynb,py:percent`)**:
   - Always pair `.ipynb` files with a companion Python script using Jupytext's `percent` format:
     ```powershell
     jupytext --set-formats ipynb,py:percent <notebook>.ipynb
     ```
   - This produces `<notebook>.py` with `# %%` cell markers.
   - Edit the `.py` companion file directly using standard tools (`replace_file_content`, `multi_replace_file_content`).

2. **Synchronize After Edits**:
   - After completing modifications to `<notebook>.py`, sync the changes back into the `.ipynb` notebook:
     ```powershell
     jupytext --sync <notebook>.ipynb
     ```
   - Jupytext round-trips cell structure, metadata, and outputs cleanly adhering to `nbformat` standards (`splitlines(keepends=True)`).

3. **Git Hygiene**:
   - Both the `.ipynb` and `.py` file should remain in sync in version control.
   - Code reviews and PR diffs should prioritize reviewing the `.py` file to avoid execution-count and binary output noise.
