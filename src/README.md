<h1 align="center">CognitiveTrail Navigator Source</h1>

# 1. Purpose
This directory contains the Python source for the CognitiveTrail Navigator CLI pipeline, including consent handling, ingestion agents, storage utilities, and command-line entrypoints.

# 2. File Guide
- `cli.py`: CLI entrypoint; prompts for data limit and runs the ingestion pipeline.
- `agents.py`: Agent context, pipeline assembly, and time-window resolution helpers.
- `browser_history.py`: Read-only browser history extractors for Chromium-based browsers and Firefox.
- `storage.py`: Local SQLite/CSV persistence and audit logging primitives.
- `consent.py`: User consent collection utilities (prompt-driven).
- `audit.py`: Placeholder hook for future audit enhancements.
- `__init__.py`: Package marker.

# 3. Usage Notes
- Run `python -m src.cli fetch-history` to launch the consent-first browser history ingest. The CLI will ask you to select a data limit (`today`, `last week`, `last month`, `1 year`) before collecting entries.
- All outputs (SQLite DB, CSV, logs) are written under the top-level `data/` directory.
<h1 align="center">Source Modules</h1>

# 1. Contents
- `__init__.py`: Package marker.
- `agents.py`: Lightweight LangGraph-style pipeline orchestrating consent, ingest, storage, and UI steps.
- `audit.py`: (Reserved) audit helpers; current logging lives in `storage.py`.
- `browser_history.py`: Read-only browser history ingestion for Chrome, Firefox, and Edge.
- `cli.py`: Minimal argparse CLI entry point (`fetch-history`).
- `consent.py`: Explicit consent prompts logged to the audit file.
- `storage.py`: Local SQLite/CSV storage plus audit logging utilities.

# 2. Design Notes
- Pipeline agents are small, testable functions returning an updated context.
- All data and audit artifacts are written under `data/` (gitignored).
- History databases are copied to temp files before reading to keep source files untouched.

# 3. Extending
- Add Gmail OAuth and filesystem agents as new pipeline steps.
- Replace the pipeline list in `agents.py` with a real LangGraph graph when ready.
- Keep any new data artifacts within `data/` or `tokens/` and update ignore rules if needed.

