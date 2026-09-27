# Python UTF-8 & Windows Encoding Invariants

## Core Principles

1. **Top-of-File Stream Reconfiguration**:
   Every Python script that prints paths, logs, or external data on Windows MUST include this block at the very top:
   ```python
   import sys
   if sys.platform == "win32":
       sys.stdout.reconfigure(encoding="utf-8", errors="replace")
       sys.stderr.reconfigure(encoding="utf-8", errors="replace")
   ```
   Using `errors="replace"` ensures that even malformed byte streams or unmapped characters never crash the process with `UnicodeEncodeError`.

2. **Invoke Python with `-X utf8`**:
   When launching Python scripts from terminal or tool calls, always pass `-X utf8` (and `-u` for real-time unbuffered progress):
   ```bash
   python -u -X utf8 scripts/my_script.py
   ```
   This activates Python's PEP 540 UTF-8 mode on Windows, enforcing UTF-8 as the default encoding for standard streams and OS interfaces.

3. **Explicit File I/O Encodings**:
   Never rely on Windows system locale for file reading or writing. Always declare UTF-8 explicitly:
   ```python
   with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
   with open(file_path, "w", encoding="utf-8") as f:
   ```
