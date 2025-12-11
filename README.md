<h1 align="center">CognitiveTrail Navigator</h1>

# 1. Table of Contents
- [Overview](#2-overview)
- [Key Features](#3-key-features)
- [Architecture](#4-architecture)
- [Setup](#5-setup)
- [Usage](#6-usage)
- [Consent & Safety](#7-consent--safety)
- [Data & Storage Layout](#8-data--storage-layout)
- [Development & Testing](#9-development--testing)
- [Troubleshooting](#10-troubleshooting)
- [Roadmap](#11-roadmap)

# 2. Overview
CognitiveTrail Navigator is a local-first assistant scaffolded as a LangGraph-style pipeline. It emphasizes explicit user consent, read-only data access, and local storage (SQLite/CSV). No data leaves your machine unless you extend it to do so.

# 3. Key Features
- Local-only ingestion of browser history with optional per-browser selection.
- Consent-first flow; each data source requires explicit approval.
- Read-only access to browser databases via temp copies to keep originals untouched.
- Dual persistence targets: SQLite (`data/ctn.sqlite`) and CSV (`data/browser_history.csv`).
- Audit logging for major actions and consents (`data/audit.log`).

# 4. Architecture
- Pipeline agents in `src/agents.py` orchestrate consent → ingest → store → UI notify.
- Browser history readers in `src/browser_history.py` support Chrome, Edge, and Firefox.
- Storage and audit utilities live in `src/storage.py`.
- CLI entrypoint in `src/cli.py` wires argparse into the agent pipeline.

# 5. Setup
- Use Python 3.10+ with a virtual environment: `python -m venv .venv && source .venv/bin/activate`.
- Install dependencies: `pip install -r requirements.txt` (currently stdlib-only scaffold).
- Optional: respect the provided global ignore list: `git config core.excludesFile .gitignore_global.txt`.

# 6. Usage
- Run: `python -m src.cli fetch-history --browsers chrome firefox edge`.
- The CLI always prompts for a data limit (`today`, `last week`, `last month`, or `1 year`). Supplying `--time-window` only sets the default shown in the prompt.
- Grant consent when asked; declining skips that data source.
- On completion, you will see `Data fetch complete — N entries saved.` with rows persisted to SQLite, CSV, and an HTML snapshot under `data/browser_history.html`.
- IP column in the HTML/CSV is filled with a best-effort local interface IP (no external calls).

# 7. Consent & Safety
- Explicit per-source consent is required before any data read.
- History DBs are copied to temp files before querying; source files remain untouched.
- All artifacts (SQLite, CSV, audit log, future tokens) stay under `data/` (gitignored).
- No network uploads occur by default.

# 8. Data & Storage Layout
- SQLite: `data/ctn.sqlite` with `browser_history` and `audit_log` tables.
- CSV: `data/browser_history.csv` (append-only export of ingested rows).
- HTML: `data/browser_history.html` (auto-generated view with clickable URLs after each run; fixed column widths with ellipsis for long URLs).
- Analysis: `data/analyze.html` (charts of top subdomains, TLDs, and day-of-week usage by subdomain from the CSV).
- Audit: `data/audit.log` records timestamps, events, and details.
- See `data/README.md` for folder-specific notes.

# 9. Development & Testing
- Current focus: CLI-driven manual runs. Add `pytest`-style tests under `tests/` as you extend functionality.
- For new agents, keep steps small and composable; update `build_pipeline()` in `src/agents.py`.
- Follow semantic commits (feat:, fix:, docs:) and keep changes scoped.

# 10. Troubleshooting
- If history files are locked, ensure the browser is closed; the CLI already copies to temp files.
- WSL/Windows paths may vary; Chrome/Edge profiles are auto-scanned but you can add paths in `KNOWN_HISTORY_PATHS` in `src/browser_history.py` if no results are returned.
- Missing data often means consent was declined; re-run and approve.

# 11. Roadmap
- Add Gmail read-only OAuth agent with restricted scopes.
- Enrich history entries with optional IP/geo hints if locally available.
- Replace the linear list pipeline with a full LangGraph graph and add automated tests.
