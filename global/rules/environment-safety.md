# Environment Safety & System Protection Guidelines

## 1. Workspace Isolation & Confinement
- **Strict Working Boundaries**: Confine all file modifications, creations, and deletions strictly within the user's active workspace (e.g., `c:\Users\Xabin\apps`).
- **Never Modify Outside Workspace**:
  - Do NOT create, edit, or delete files in system directories (`C:\Windows`, `C:\Program Files`, `C:\Program Files (x86)`).
  - Do NOT touch personal user directories (`C:\Users\Xabin\Desktop`, `Documents`, `Downloads`, `Pictures`, `Videos`) unless explicitly directed by the user.
  - Do NOT touch or expose security stores: `.ssh`, `.aws`, `.gnupg`, credential vaults, or system keychain files.
  - Do NOT modify global environment variables, system PATH, or Windows Registry settings.

## 2. Prohibition of Destructive Commands
- **Disk & System Level Commands**: Strictly forbidden:
  - `format`, `diskpart`, `bcdedit`, `chkdsk /f`
  - `reg delete`, `reg add`, `reg restore`
  - `vssadmin delete shadows`
- **Recursive File Destruction**:
  - Never execute recursive deletions targeting root drives (`C:\`, `D:\`), user profile root (`$env:USERPROFILE`, `~`), or critical system subfolders.
  - Commands such as `rmdir /s /q C:\`, `del /f /s /q C:\`, `rm -rf /`, `rm -rf ~`, or `Remove-Item -Recurse -Force $HOME` are strictly prohibited.
- **Process & System Integrity**:
  - Do not terminate system processes, OS services, or background tasks not spawned by this agent.
  - Dev servers and child processes spawned by tasks may be stopped when needed.

## 3. Git Safety & History Preservation
- **No Force Pushing**: Never run `git push --force`, `git push -f`, or `git push --delete` on remote branches without explicit, unambiguous user confirmation.
- **Preserve Uncommitted Work**: Never run `git reset --hard`, `git checkout -- .`, or `git clean -fd` if there are unstaged or uncommitted user changes, unless the user explicitly commands discarding them.
- **Safe Branching**: Perform experiments and substantial changes on dedicated branches or with clean commits so work can always be reverted.

## 4. Stability & Clean Housekeeping
- Clean up all temporary directories, scratch files, and intermediate build artifacts when operations complete.
- Verify actions non-destructively before modifying existing working setups.
