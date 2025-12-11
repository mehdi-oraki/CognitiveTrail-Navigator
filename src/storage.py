from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Iterable, List, Optional
import csv
import datetime as dt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


@dataclass
class BrowserEntry:
    source: str
    url: str
    title: Optional[str]
    visit_time: dt.datetime
    query: Optional[str] = None
    ip: Optional[str] = None


class LocalStore:
    """Local SQLite + CSV storage."""

    def __init__(self, db_path: Path | None = None, csv_path: Path | None = None) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or DATA_DIR / "ctn.sqlite"
        self.csv_path = csv_path or DATA_DIR / "browser_history.csv"
        self._ensure_db()

    def _ensure_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS browser_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    visit_time TEXT NOT NULL,
                    query TEXT,
                    ip TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event TEXT NOT NULL,
                    detail TEXT
                )
                """
            )
            conn.commit()

    def save_browser_history(self, entries: Iterable[BrowserEntry]) -> int:
        rows: List[BrowserEntry] = list(entries)
        if not rows:
            return 0

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.executemany(
                """
                INSERT INTO browser_history (source, url, title, visit_time, query, ip)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row.source,
                        row.url,
                        row.title,
                        row.visit_time.isoformat(),
                        row.query,
                        row.ip,
                    )
                    for row in rows
                ],
            )
            conn.commit()

        self._append_csv(rows)
        return len(rows)

    def _append_csv(self, rows: List[BrowserEntry]) -> None:
        is_new = not self.csv_path.exists()
        with self.csv_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            if is_new:
                writer.writerow(["source", "url", "title", "visit_time", "query", "ip"])
            for row in rows:
                writer.writerow(
                    [
                        row.source,
                        row.url,
                        row.title or "",
                        row.visit_time.isoformat(),
                        row.query or "",
                        row.ip or "",
                    ]
                )


class AuditLogger:
    """Append-only audit log stored locally."""

    def __init__(self, log_path: Path | None = None) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.log_path = log_path or DATA_DIR / "audit.log"

    def log(self, event: str, detail: str | None = None) -> None:
        timestamp = dt.datetime.utcnow().isoformat()
        line = f"{timestamp}\t{event}"
        if detail:
            line = f"{line}\t{detail}"
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

