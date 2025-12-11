<h1 align="center">CognitiveTrail Navigator</h1>

# 1. Overview
CognitiveTrail Navigator is a local-first assistant scaffolded to run as a LangGraph-style agent pipeline. It focuses on explicit user consent, read-only data access, and storing everything locally (SQLite/CSV). No data leaves your machine unless you explicitly extend it to do so.

# 2. Repository Contents
- `README.md`: Project overview, setup, and usage notes.
- `.gitignore`: Keeps data, tokens, and other sensitive artifacts out of version control.
- `.gitignore_global.txt`: Optional global ignore list; configure Git to use it for extra safety.
- `src/`: Python source for the consent, ingestion, storage, and CLI pipeline.

# 3. Setup
- Recommended: Python 3.10+ with a virtual environment (`python -m venv .venv && source .venv/bin/activate`).
- Install dependencies: `pip install -r requirements.txt` (stdlib-only for now, file included for future additions).
- Ensure Git respects the global ignore file: `git config core.excludesFile .gitignore_global.txt`.

# 4. Usage (MVP CLI)
- Run the pipeline: `python -m src.cli fetch-history --browsers chrome firefox edge`. The CLI will always prompt you to enter a data limit (`today`, `last week`, `last month`, or `1 year`); passing `--time-window` simply sets the default option shown in the prompt.
- The CLI will prompt for explicit consent before accessing each data source (Gmail, filesystem, browser history). If you decline, the step is skipped.
- On success, you will see a summary like `Data fetch complete — N entries saved.`.

# 5. Consent and Safety
- Every access is gated by explicit per-source consent.
- Data access uses read-only copies of browser history databases; originals remain untouched.
- All artifacts (SQLite DB, CSV exports, audit log, OAuth tokens) are written under `data/` and `tokens/`, which are gitignored.
- No network uploads are performed by default.

# 6. Data Storage
- SQLite file: `data/ctn.sqlite` with `browser_history` and `audit_log` tables.
- CSV export: `data/browser_history.csv` (append-only).
- Audit log: `data/audit.log` captures consents and major actions.

# 7. Incremental Development Plan
- Current state: Browser history ingestion scaffold with consent, storage, and audit logging. Gmail OAuth and filesystem enrichment are placeholders.
- Next steps: Add Gmail read-only OAuth agent (restricted scopes), enrich entries with IP/geo hints if locally available, add tests, and extend LangGraph structure.

# 8. Troubleshooting
- If history files are locked, the CLI copies them to a temp file before reading.
- Ensure your browser is closed for best results.
- For WSL/Windows, history paths may differ; adjust `KNOWN_HISTORY_PATHS` in `src/browser_history.py` as needed.

