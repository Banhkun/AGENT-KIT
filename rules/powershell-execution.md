# PowerShell Execution & Windows Terminal Invariants

## Core Principles

1. **Prefer Script Files (`.ps1`) Over Inlined Complex Commands**:
   - For any command that involves variables (`$var`), loops, quotes, or more than a single straightforward pipeline, **DO NOT** use inlined `powershell -Command "..."`.
   - **Instead**: Write the script to a clean `.ps1` file (e.g. in `scripts/` or `scratch/`) and execute it with:
     ```powershell
     powershell -NoProfile -ExecutionPolicy Bypass -File path/to/script.ps1
     ```
   - This completely eliminates premature variable expansion, quote escaping corruption, and statement splitting.
   - **UTF-8 BOM Invariant**: Windows PowerShell 5.1 defaults to ANSI (`Windows-1252`) when parsing `.ps1` files unless they have a UTF-8 BOM. Any `.ps1` script containing emojis, regex patterns with unicode, or non-ASCII characters MUST be saved with a UTF-8 BOM (`[System.Text.Encoding]::UTF8`), otherwise characters are corrupted silently (e.g. `👉` becomes `ðŸ‘‰`).

2. **Single Quotes for Simple Inlined Commands**:
   - If an inlined command is truly trivial, wrap the command in **single quotes** (`'...'`) so the outer shell does not expand `$` signs:
     ```powershell
     powershell -NoProfile -Command '$p = [Environment]::GetEnvironmentVariable("PATH"); Write-Host $p'
     ```
   - Never use double quotes `powershell -Command "..."` when the payload contains `$` variables.

3. **Check Before Assuming Tool Availability**:
   - Never assume binaries like `python`, `git`, or `winget` are in the active process PATH.
   - Test existence via `Get-Command <tool> -ErrorAction SilentlyContinue` or inspect registry/paths before invoking.
   - **Stale Process PATH**: If the user recently changed environment variables in the Windows Registry, the current shell process may still hold stale values. Verify against `[Environment]::GetEnvironmentVariable('Path', 'User')` if a recently installed tool is reported missing.

4. **Sandbox vs System Modification**:
   - Commands that modify persistent user registry, environment variables, or execute binaries located outside the workspace (such as Python in `AppData\Local\Programs\...`) require `BypassSandbox: true`. Do not attempt them in the default sandboxed environment.
