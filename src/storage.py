from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Iterable, List, Optional
import csv
import datetime as dt
import html as html_lib
import json
from collections import Counter
from urllib.parse import urlparse

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
        analysis_path: Path | None = None,
    ) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or DATA_DIR / "ctn.sqlite"
        self.csv_path = csv_path or DATA_DIR / "browser_history.csv"
        self.html_path = html_path or DATA_DIR / "browser_history.html"
        self.analysis_path = analysis_path or DATA_DIR / "analyze.html"
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
        self._write_analysis_html()
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

    def _aggregate_domains(self) -> tuple[Counter, Counter, dict[str, Counter], Counter]:
        """Return counters for subdomains (full host), TLDs, per-day-of-week usage, and total day-of-week counts."""
        if not self.csv_path.exists():
            return Counter(), Counter(), {}, Counter()

        with self.csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            subdomains: Counter = Counter()
            tlds: Counter = Counter()
            dow_by_subdomain: dict[str, Counter] = {}
            dow_total: Counter = Counter()
            for row in reader:
                url = row.get("url") or ""
                host = urlparse(url).hostname or ""
                if not host:
                    continue
                subdomains[host] += 1
                parts = host.split(".")
                if len(parts) >= 2:
                    tlds[parts[-1]] += 1
                elif parts:
                    tlds[parts[0]] += 1
                # Day-of-week aggregation
                visit_raw = row.get("visit_time") or ""
                try:
                    ts = dt.datetime.fromisoformat(visit_raw)
                    dow = ts.weekday()  # 0=Mon
                except (ValueError, TypeError):
                    continue
                if host not in dow_by_subdomain:
                    dow_by_subdomain[host] = Counter()
                dow_by_subdomain[host][dow] += 1
                dow_total[dow] += 1
        return subdomains, tlds, dow_by_subdomain, dow_total

    def _write_analysis_html(self) -> None:
        """Render a chart view summarizing frequent subdomains, TLDs, and day-of-week usage."""
        subdomains, tlds, dow_by_subdomain, dow_total = self._aggregate_domains()

        # Take top 20 for readability
        top_subdomains = subdomains.most_common(20)
        top_tlds = tlds.most_common(20)

        sub_labels = [label for label, _ in top_subdomains]
        sub_counts = [count for _, count in top_subdomains]
        tld_labels = [label for label, _ in top_tlds]
        tld_counts = [count for _, count in top_tlds]

        # Day-of-week dataset for top subdomains (limit to top 8 for readability)
        dow_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        dow_subdomains = sub_labels[:8]
        dow_datasets = []
        palette = [
            "#4F46E5",
            "#0EA5E9",
            "#10B981",
            "#F59E0B",
            "#EF4444",
            "#8B5CF6",
            "#EC4899",
            "#06B6D4",
        ]
        for idx, sub in enumerate(dow_subdomains):
            counts = [dow_by_subdomain.get(sub, Counter()).get(i, 0) for i in range(7)]
            dow_datasets.append(
                {
                    "label": sub,
                    "data": counts,
                    "backgroundColor": palette[idx % len(palette)],
                    "stack": "dow",
                }
            )
        other_counts = [
            sum(
                counts.get(i, 0)
                for host, counts in dow_by_subdomain.items()
                if host not in dow_subdomains
            )
            for i in range(7)
        ]
        if any(other_counts):
            dow_datasets.append(
                {
                    "label": "Other",
                    "data": other_counts,
                    "backgroundColor": "#9CA3AF",
                    "stack": "dow",
                }
            )

        total_dow_counts = [dow_total.get(i, 0) for i in range(7)]

        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Domain Usage Analysis</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 24px;
      background: #f7f7f7;
      color: #111;
    }}
    h1, h2 {{
      text-align: center;
    }}
    .chart-container {{
      width: 100%;
      max-width: 960px;
      margin: 24px auto;
      background: #fff;
      padding: 16px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }}
  </style>
</head>
<body>
  <h1>Browser History Analysis</h1>
  <div class="chart-container">
    <h2>Top Subdomains (Top 20)</h2>
    <canvas id="subdomainChart" height="220"></canvas>
  </div>
  <div class="chart-container">
    <h2>Top TLDs (Top 20)</h2>
    <canvas id="tldChart" height="220"></canvas>
  </div>
  <div class="chart-container">
    <h2>Top Subdomains by Day of Week (Top 8 + Other)</h2>
    <canvas id="dowChart" height="280"></canvas>
  </div>
  <div class="chart-container">
    <h2>All Visits by Day of Week</h2>
    <canvas id="dowTotalChart" height="220"></canvas>
  </div>

  <script>
    const subLabels = {json.dumps(sub_labels)};
    const subCounts = {json.dumps(sub_counts)};
    const tldLabels = {json.dumps(tld_labels)};
    const tldCounts = {json.dumps(tld_counts)};
    const dowLabels = {json.dumps(dow_labels)};
    const dowDatasets = {json.dumps(dow_datasets)};
    const dowTotals = {json.dumps(total_dow_counts)};

    const barOptions = {{
      indexAxis: 'y',
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{ enabled: true }},
      }},
      scales: {{
        x: {{ beginAtZero: true, title: {{ display: true, text: 'Visits' }} }},
        y: {{ title: {{ display: true, text: 'Host / TLD' }} }}
      }}
    }};

    new Chart(document.getElementById('subdomainChart'), {{
      type: 'bar',
      data: {{
        labels: subLabels,
        datasets: [{{
          label: 'Visits',
          data: subCounts,
          backgroundColor: '#4F46E5',
        }}],
      }},
      options: barOptions,
    }});

    new Chart(document.getElementById('tldChart'), {{
      type: 'bar',
      data: {{
        labels: tldLabels,
        datasets: [{{
          label: 'Visits',
          data: tldCounts,
          backgroundColor: '#0EA5E9',
        }}],
      }},
      options: barOptions,
    }});

    new Chart(document.getElementById('dowChart'), {{
      type: 'bar',
      data: {{
        labels: dowLabels,
        datasets: dowDatasets,
      }},
      options: {{
        responsive: true,
        plugins: {{
          legend: {{ position: 'bottom' }},
          tooltip: {{ mode: 'index', intersect: false }},
        }},
        scales: {{
          x: {{ stacked: true }},
          y: {{ stacked: true, beginAtZero: true, title: {{ display: true, text: 'Visits' }} }},
        }},
      }},
    }});

    new Chart(document.getElementById('dowTotalChart'), {{
      type: 'bar',
      data: {{
        labels: dowLabels,
        datasets: [{{
          label: 'Visits',
          data: dowTotals,
          backgroundColor: '#6366F1',
        }}],
      }},
      options: {{
        responsive: true,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{ mode: 'index', intersect: false }},
        }},
        scales: {{
          x: {{ beginAtZero: true }},
          y: {{ beginAtZero: true, title: {{ display: true, text: 'Visits' }} }},
        }},
      }},
    }});
  </script>
</body>
</html>
"""

        with self.analysis_path.open("w", encoding="utf-8") as handle:
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

