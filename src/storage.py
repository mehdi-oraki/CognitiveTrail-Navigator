from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Iterable, List, Optional
import csv
import datetime as dt
import html as html_lib

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

    def __init__(
        self,
        db_path: Path | None = None,
        csv_path: Path | None = None,
        html_path: Path | None = None,
    ) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or DATA_DIR / "ctn.sqlite"
        self.csv_path = csv_path or DATA_DIR / "browser_history.csv"
        self.html_path = html_path or DATA_DIR / "browser_history.html"
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
        self._write_html()
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

    def _write_html(self) -> None:
        """Render a simple HTML table from the CSV export for easy viewing."""
        if not self.csv_path.exists():
            return

        with self.csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            rows = list(reader)

        if not rows:
            return

        header, *body = rows
        header_lower = [col.strip().lower() for col in header]

        desired_order = ["source", "url", "title", "visit_time", "query", "ip"]
        ordered_indices = [header_lower.index(col) for col in desired_order if col in header_lower]
        display_header = [header[i] for i in ordered_indices] if ordered_indices else header

        def cell(col_name: str, val: str) -> str:
            """Render table cell; make URL fields clickable."""
            safe_val = html_lib.escape(val or "")
            if col_name == "url" and val:
                safe_href = html_lib.escape(val, quote=True)
                return f'<a href="{safe_href}" target="_blank" rel="noopener noreferrer">{safe_val}</a>'
            return safe_val

        def ordered_row(row: List[str]) -> List[str]:
            if not ordered_indices:
                return row
            return [row[i] if i < len(row) else "" for i in ordered_indices]

        html_rows = "\n".join(
            "<tr>"
            + "".join(
                f"<td>{cell(col_name, col_val)}</td>"
                for col_name, col_val in zip(
                    (col.lower() for col in display_header), ordered_row(row)
                )
            )
            + "</tr>"
            for row in body
        )
        html_header = "".join(f"<th>{html_lib.escape(col)}</th>" for col in display_header)

        colgroup = """
    <col style="width: 12%" />
    <col style="width: 34%" />
    <col style="width: 20%" />
    <col style="width: 14%" />
    <col style="width: 12%" />
    <col style="width: 8%" />
"""

        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Browser History Export</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 24px;
      color: #111;
      background: #f7f7f7;
    }}
    h1 {{
      text-align: center;
      margin-bottom: 16px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: #fff;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
      table-layout: fixed;
    }}
    th, td {{
      padding: 10px 12px;
      border: 1px solid #e0e0e0;
      text-align: left;
      vertical-align: top;
      font-size: 14px;
      word-wrap: break-word;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    th {{
      background: #fafafa;
      font-weight: 600;
    }}
    tr:nth-child(even) {{
      background: #fcfcfc;
    }}
  </style>
</head>
<body>
  <h1>Browser History Export</h1>
  <table>
    <colgroup>
      {colgroup}
    </colgroup>
    <thead><tr>{html_header}</tr></thead>
    <tbody>
      {html_rows}
    </tbody>
  </table>
</body>
</html>
"""

        with self.html_path.open("w", encoding="utf-8") as handle:
            handle.write(html_doc)


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

