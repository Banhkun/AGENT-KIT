# Colab Integration & Execution Policy

## Core Principle
1. **User Owns Colab Notebook Code**:
   - The user writes and maintains their own Google Colab notebook code and models.
   - Do NOT dump unsolicited Colab setup code, notebook cells, or lectures into chat unless explicitly requested.

2. **Agent Works with Colab Directly**:
   - The agent is **expected to interact directly with the running Colab server** via its active API tunnel (e.g. `/list`, `/cutout-drive`, `/montage-drive`, etc.).
   - Call endpoints, query folders, process images, and retrieve generated assets autonomously without requiring the user to do the manual API plumbing.
