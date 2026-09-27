# AGENT-KIT

A curated, layered collection of agent skills, rules, and developer customizations for Google Antigravity.

## Repository Architecture

AGENT-KIT organizes customizations into Antigravity's two standard tiers in a single layered monorepo:

```
AGENT-KIT/
├── global/                         # Global scope (~/.gemini/config)
│   ├── rules/                      # environment-safety.md, etc.
│   ├── scripts/                    # safety-gate.ps1
│   └── hooks.json                  # Pre/post tool execution hooks
│
├── skills/                         # Workspace scope (.agents/skills)
│   ├── code-architect/
│   ├── colab-gpu-controller/
│   └── ...
│
├── rules/                          # Workspace scope (.agents/rules)
│   ├── jupyter-notebook-workflow.md
│   ├── powershell-execution.md
│   └── ...
│
└── sync.ps1                        # PowerShell deployment & sync script
```

---

## Quick Sync (`sync.ps1`)

Use `sync.ps1` to deploy or synchronize customizations between AGENT-KIT and your local machine:

```powershell
# Sync everything (Global to ~/.gemini/config, Workspace to C:\Users\Xabin\apps\.agents)
.\sync.ps1

# Sync only Global configurations
.\sync.ps1 -Scope Global

# Sync Workspace to a custom directory
.\sync.ps1 -Scope Workspace -WorkspaceRoot "C:\path\to\your\workspace"

# Link via directory junctions for live two-way editing
.\sync.ps1 -Mode Junction
```

---

## Global Customizations (`global/`)

Customizations intended for machine-wide application in `~/.gemini/config/`:

| Component | Description |
| :--- | :--- |
| [`environment-safety.md`](global/rules/environment-safety.md) | Universal environment safety rules and protected path boundaries. |
| [`safety-gate.ps1`](global/scripts/safety-gate.ps1) | Automated pre-execution hook script that denies destructive commands and gates force actions. |
| [`hooks.json`](global/hooks.json) | Antigravity IDE hook definitions binding `safety-gate.ps1` to tool calls. |

---

## Workspace Rules (`rules/`)

Universal project workflow rules and technical invariants placed in `<workspace>/.agents/rules/`:

| Rule | Description |
| :--- | :--- |
| [`jupyter-notebook-workflow.md`](rules/jupyter-notebook-workflow.md) | Standard Jupytext pairing (`ipynb,py:percent`) workflow for safe agent notebook editing. |
| [`powershell-execution.md`](rules/powershell-execution.md) | PowerShell execution rules, UTF-8 BOM encoding invariants, and sandbox isolation boundaries. |
| [`python-windows-encoding.md`](rules/python-windows-encoding.md) | Python UTF-8 streams, PEP 540 `-X utf8` flag, and Windows character encoding standards. |
| [`git-automation.md`](rules/git-automation.md) | Conventional commits, automatic staging, secret scanning, and branch workflows. |
| [`command-purpose.md`](rules/command-purpose.md) | Terminal execution safety, command clarity, and operational invariants. |
| [`colab-gpu-workflow.md`](rules/colab-gpu-workflow.md) | Remote Colab GPU orchestration, FastAPI controller lifecycle, and asset pipelines. |
| [`colab-execution-policy.md`](rules/colab-execution-policy.md) | Security policy for remote Colab code execution endpoints. |

---

## Skills Directory (`skills/`)

Reusable agent skills placed in `<workspace>/.agents/skills/`:

| Skill | Description |
| :--- | :--- |
| [`code-architect`](skills/code-architect) | Designs feature architectures by analyzing codebase patterns, conventions, component designs, and build blueprints. |
| [`code-explorer`](skills/code-explorer) | Traces execution paths, architecture layers, design patterns, and dependency maps across codebases. |
| [`code-reviewer`](skills/code-reviewer) | High-precision code review for bugs, logic errors, security vulnerabilities, and project conventions. |
| [`code-simplifier`](skills/code-simplifier) | Refines and simplifies code for clarity, elegance, and maintainability while preserving exact functionality. |
| [`colab-gpu-controller`](skills/colab-gpu-controller) | Remote Google Colab GPU orchestration (T4/A100) via Cloudflare tunnels for heavy ML, vision, and batch tasks. |
| [`color-system`](skills/color-system) | Product color system generation: tonal scales, semantic roles, and contrast compliance. |
| [`commit-commands`](skills/commit-commands) | Git workflow automation: smart commits, secrets screening, branch-commit-push-PR pipelines, and stale `[gone]` branch cleanup. |
| [`critique-composition`](skills/critique-composition) | Critiques layout balance, whitespace, visual rhythm, and gestalt grouping. |
| [`critique-typography`](skills/critique-typography) | Critiques typographic scale usage, readability, line height, and token compliance. |
| [`critique-visual-hierarchy`](skills/critique-visual-hierarchy) | Critiques screen entry point, eye flow, visual weight distribution, and emphasis. |
| [`feature-dev`](skills/feature-dev) | Structured 7-phase feature development lifecycle from discovery and architecture to implementation and review. |
| [`law-of-closure`](skills/law-of-closure) | Applies the Law of Closure to reduce visual weight using implied boundaries. |
| [`law-of-common-region`](skills/law-of-common-region) | Groups elements with shared containers, cards, and borders. |
| [`law-of-continuity`](skills/law-of-continuity) | Guides the eye through unbroken lines, timelines, and sequential layouts. |
| [`law-of-figure-ground`](skills/law-of-figure-ground) | Establishes depth, actionable foregrounds, and unobtrusive backgrounds. |
| [`law-of-proximity`](skills/law-of-proximity) | Groups elements through intentional spatial proximity and token spacing. |
| [`law-of-similarity`](skills/law-of-similarity) | Signals relationships across distances with shared color, shape, or styling. |
| [`layout-grid`](skills/layout-grid) | Establishes responsive grids, columns, gutters, margins, and breakpoints. |
| [`readable-measure`](skills/readable-measure) | Sets comfortable character line length and reading measure across breakpoints. |
| [`rel-generator`](skills/rel-generator) | Generates, validates, and troubleshoots Redwood Expression Language (REL) expressions. |
| [`repo-skill-importer`](skills/repo-skill-importer) | Discovers, compares, and installs agent skills from remote GitHub repositories. |
| [`runmyjobs-redwood-query`](skills/runmyjobs-redwood-query) | Explores RunMyJobs (Redwood) Data Model and builds ANSI SQL'92 Object Queries for scheduler entities. |
| [`runmyjobs-redwood-script`](skills/runmyjobs-redwood-script) | Guidance and recipes for Java (RedwoodScript) interactions with RunMyJobs objects, sessions, and UC4 `ObjectTag` mappings. |
| [`skill-creator`](skills/skill-creator) | Tools and evaluation pipelines to create, benchmark, and optimize agent skills. |
| [`skill-drive-upload`](skills/skill-drive-upload) | Packages and uploads skill bundles directly to Google Drive (`My Drive/.agent/skills`). |
| [`typography-scale`](skills/typography-scale) | Modular typographic scales, line heights, and hierarchy weights. |
| [`uc4-standalone-python`](skills/uc4-standalone-python) | Standalone Python automation, REST interaction, and job control for Automic/UC4. |
| [`visual-hierarchy`](skills/visual-hierarchy) | Establishes visual entry points and importance ordering through scale, weight, and contrast. |

---

## License & Attribution

This project is licensed under the **Apache License, Version 2.0** - see the [`LICENSE`](LICENSE) file for details.

### Third-Party Notices & Attribution
Several skills in this repository (`code-architect`, `code-explorer`, `code-reviewer`, `code-simplifier`, `commit-commands`, `feature-dev`, `skill-creator`) are derived from or inspired by prompt engineering artifacts and plugins originally developed by **Anthropic, PBC** (licensed under Apache-2.0). See [`NOTICE`](NOTICE) for comprehensive attribution details.

### Disclaimer
- This project is an independent community resource. It is **not** affiliated with, endorsed by, sponsored by, or associated with Anthropic, Redwood Software, Broadcom, Google, or any employer.
- All product names, logos, and brands (such as "Claude", "RunMyJobs", "Redwood", "UC4", "Automic") are property of their respective owners.
- **AS-IS Disclaimer**: This software and prompt repository is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability.
