from __future__ import annotations

import datetime as dt
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.parse import urlparse, parse_qs
import socket

from .storage import BrowserEntry


def _win_localappdata() -> Path | None:
    raw = os.environ.get("LOCALAPPDATA")
    return Path(raw) if raw else None


def _win_appdata() -> Path | None:
    raw = os.environ.get("APPDATA")
    return Path(raw) if raw else None


# Known history database locations (read-only). Adjust as needed per host OS.
KNOWN_HISTORY_PATHS: Dict[str, Tuple[Path, ...]] = {
    "chrome": tuple(
        path
        for path in (
            Path.home() / ".config" / "google-chrome" / "Default" / "History",
            Path.home() / ".config" / "chromium" / "Default" / "History",
            (_win_localappdata() / "Google/Chrome/User Data/Default/History") if _win_localappdata() else None,
            Path("/mnt/c/Users/Lenovo/AppData/Local/Google/Chrome/User Data/Default/History"),
            Path("/mnt/c/Users/Lenovo/AppData/Local/Google/Chrome/User Data/Profile 1/History"),
        )
        if path
    ),
    "edge": tuple(
        path
        for path in (
            Path.home() / ".config" / "microsoft-edge" / "Default" / "History",
            (_win_localappdata() / "Microsoft/Edge/User Data/Default/History") if _win_localappdata() else None,
            Path("/mnt/c/Users/Lenovo/AppData/Local/Microsoft/Edge/User Data/Default/History"),
            Path("/mnt/c/Users/Lenovo/AppData/Local/Microsoft/Edge/User Data/Profile 1/History"),
        )
        if path
    ),
    "firefox": (),  # handled separately via profiles.ini
}


def _resolve_local_ip() -> str | None:
    """Best-effort local IP detection without external calls."""
    try:
        # Uses system routing table to pick the primary interface.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        pass
    return None


def fetch_browser_history(
    browsers: Iterable[str], since: dt.datetime | None = None, max_rows: int = 10000
) -> List[BrowserEntry]:
    entries: List[BrowserEntry] = []
    normalized = {b.lower() for b in browsers}
    if "chrome" in normalized:
        entries.extend(_read_chromium_like("chrome", since, max_rows))
    if "edge" in normalized:
        entries.extend(_read_chromium_like("edge", since, max_rows))
    if "firefox" in normalized:
        entries.extend(_read_firefox(since, max_rows))
    entries.sort(key=lambda entry: entry.visit_time, reverse=True)
    return entries[:max_rows] if max_rows else entries


def _chromium_profile_candidates(source: str) -> Tuple[Path, ...]:
    """Return possible History DB locations for Chromium-based browsers."""
    if source == "chrome":
        bases = [
            Path.home() / ".config" / "google-chrome",
            Path.home() / ".config" / "chromium",
            (_win_localappdata() / "Google/Chrome/User Data") if _win_localappdata() else None,
            Path("/mnt/c/Users/Lenovo/AppData/Local/Google/Chrome/User Data"),
        ]
    elif source == "edge":
        bases = [
            Path.home() / ".config" / "microsoft-edge",
            (_win_localappdata() / "Microsoft/Edge/User Data") if _win_localappdata() else None,
            Path("/mnt/c/Users/Lenovo/AppData/Local/Microsoft/Edge/User Data"),
        ]
    else:
        return ()

    profile_names = ("Default", "Profile 1", "Profile 2", "Profile 3")
    candidates: List[Path] = []
    for base in bases:
        if not base or not base.exists():
            continue
        for name in profile_names:
            candidate = base / name / "History"
            if candidate.exists():
                candidates.append(candidate)
        # Also scan any other profile directories that contain a History file.
        for subdir in base.iterdir():
            if not subdir.is_dir():
                continue
            history_file = subdir / "History"
            if history_file.exists() and history_file not in candidates:
                candidates.append(history_file)
    return tuple(candidates)


def _read_chromium_like(
    source: str, since: dt.datetime | None, max_rows: int
) -> List[BrowserEntry]:
    paths = KNOWN_HISTORY_PATHS.get(source, ())
    for db_path in paths:
        if db_path.exists():
            return _read_chromium_db(source, db_path, since, max_rows)

    # Fallback: scan common profile directories to find non-default profiles.
    dynamic_paths = _chromium_profile_candidates(source)
    for db_path in dynamic_paths:
        if db_path.exists():
            return _read_chromium_db(source, db_path, since, max_rows)

    return []


def _read_chromium_db(
    source: str, db_path: Path, since: dt.datetime | None, max_rows: int
) -> List[BrowserEntry]:
    temp_path = Path(tempfile.mkstemp(suffix=".db")[1])
    ip = _resolve_local_ip()
    try:
        shutil.copy2(db_path, temp_path)
        where_clause = ""
        params: Tuple[object, ...]
        if since:
            where_clause = "WHERE visits.visit_time >= ?"
            params = (_chromium_dt_to_ts(since), max_rows)
        else:
            params = (max_rows,)
        query = f"""
            SELECT urls.url, urls.title, visits.visit_time
            FROM urls
            JOIN visits ON urls.id = visits.url
            {where_clause}
            ORDER BY visits.visit_time DESC
            LIMIT ?
        """
        with sqlite3.connect(f"file:{temp_path}?mode=ro", uri=True) as conn:
            cur = conn.cursor()
            rows = cur.execute(query, params).fetchall()
            return [
                BrowserEntry(
                    source=source,
                    url=row[0],
                    title=row[1],
                    visit_time=_chromium_ts_to_dt(row[2]),
                    query=_extract_query(row[0]),
                    ip=ip,
                )
                for row in rows
            ]
    except sqlite3.Error:
        return []
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def _read_firefox(
    since: dt.datetime | None, max_rows: int
) -> List[BrowserEntry]:
    profiles_ini = Path.home() / ".mozilla" / "firefox" / "profiles.ini"
    if not profiles_ini.exists():
        win_profiles = (_win_appdata() / "Mozilla/Firefox/profiles.ini") if _win_appdata() else None
        if win_profiles and win_profiles.exists():
            profiles_ini = win_profiles
        else:
            return []

    profile_dirs = [
        line.split("=", 1)[1].strip()
        for line in profiles_ini.read_text().splitlines()
        if line.lower().startswith("path=")
    ]

    ip = _resolve_local_ip()

    for profile in profile_dirs:
        # Prefer Linux-style path; fall back to Windows profile location.
        db_path = Path.home() / ".mozilla" / "firefox" / profile / "places.sqlite"
        if not db_path.exists() and _win_appdata():
            db_path = _win_appdata() / "Mozilla/Firefox" / profile / "places.sqlite"
        if not db_path.exists():
            win_base = Path("/mnt/c/Users/Lenovo/AppData/Roaming/Mozilla/Firefox/Profiles")
            alt = win_base / profile / "places.sqlite"
            if alt.exists():
                db_path = alt
            else:
                continue
        temp_path = Path(tempfile.mkstemp(suffix=".db")[1])
        try:
            shutil.copy2(db_path, temp_path)
            where_clause = ""
            params: Tuple[object, ...]
            if since:
                where_clause = "WHERE moz_historyvisits.visit_date >= ?"
                params = (_firefox_dt_to_ts(since), max_rows)
            else:
                params = (max_rows,)
            query = f"""
                SELECT moz_places.url, moz_places.title, moz_historyvisits.visit_date
                FROM moz_places
                JOIN moz_historyvisits ON moz_places.id = moz_historyvisits.place_id
                {where_clause}
                ORDER BY moz_historyvisits.visit_date DESC
                LIMIT ?
            """
            with sqlite3.connect(f"file:{temp_path}?mode=ro", uri=True) as conn:
                cur = conn.cursor()
                rows = cur.execute(query, params).fetchall()
                return [
                    BrowserEntry(
                        source="firefox",
                        url=row[0],
                        title=row[1],
                        visit_time=_firefox_ts_to_dt(row[2]),
                        query=_extract_query(row[0]),
                        ip=ip,
                    )
                    for row in rows
                ]
        except sqlite3.Error:
            return []
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
    return []


def _chromium_ts_to_dt(value: int) -> dt.datetime:
    # Chromium stores microseconds since 1601-01-01
    epoch_start = dt.datetime(1601, 1, 1)
    return epoch_start + dt.timedelta(microseconds=value)


def _chromium_dt_to_ts(value: dt.datetime) -> int:
    epoch_start = dt.datetime(1601, 1, 1)
    delta = value - epoch_start
    return int(delta.total_seconds() * 1_000_000)


def _firefox_ts_to_dt(value: int) -> dt.datetime:
    # Firefox uses microseconds since Unix epoch
    return dt.datetime.utcfromtimestamp(value / 1_000_000)


def _firefox_dt_to_ts(value: dt.datetime) -> int:
    return int(value.timestamp() * 1_000_000)


def _extract_query(url: str) -> str | None:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    for key in ("q", "query", "text"):
        if key in qs:
            return qs[key][0]
    return None

