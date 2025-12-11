<h1 align="center">CognitiveTrail Navigator Source</h1>

# 1. Table of Contents
- [Purpose](#2-purpose)
- [File Guide](#3-file-guide)
- [Design Notes](#4-design-notes)
- [Usage Notes](#5-usage-notes)
- [Extending](#6-extending)

# 2. Purpose
This directory contains the Python source for the CognitiveTrail Navigator CLI pipeline, including consent handling, ingestion agents, storage utilities, and command-line entrypoints.

# 3. File Guide
- `agents.py`: Pipeline orchestration (consent → ingest → store → UI) and time-window resolution.
- `audit.py`: Reserved for future audit helpers; current logging utilities live in `storage.py`.
- `browser_history.py`: Read-only browser history ingestion for Chrome, Edge, and Firefox using temp copies.
- `cli.py`: Argparse entrypoint (`fetch-history`) that prompts for data limits and runs the pipeline.
- `consent.py`: Explicit consent prompts, logged to the audit log.
- `storage.py`: Local SQLite/CSV persistence plus audit logging utilities.
- `__init__.py`: Package marker.

# 4. Design Notes
- Pipeline steps are small functions that accept and return an `AgentContext`, keeping logic composable and testable.
- All artifacts (SQLite, CSV, audit log) are written under the project-level `data/` directory.
- Browser databases are copied to temp files before reading to keep source DBs untouched.

# 5. Usage Notes
- Run `python -m src.cli fetch-history` to launch consent-first browser history ingestion.
- The CLI always asks for a data limit (`today`, `last week`, `last month`, `1 year`) and logs your choice.
- Outputs (SQLite, CSV, HTML snapshot, audit log) live under `data/`.

# 6. Extending
- Add new agents (e.g., Gmail OAuth, filesystem metadata) as additional pipeline steps in `build_pipeline()`.
- When the graph grows, replace the list-based pipeline in `agents.py` with a full LangGraph graph.
- Keep any new artifacts within `data/` or `tokens/` and update ignore rules if needed.
