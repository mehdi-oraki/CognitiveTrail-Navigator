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

