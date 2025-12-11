from __future__ import annotations

import argparse

from .agents import (
    AgentContext,
    TIME_WINDOWS,
    build_pipeline,
    resolve_window_start,
    run_pipeline,
)
from .storage import AuditLogger, LocalStore


def _prompt_time_window(default: str = "last week") -> str:
    """Prompt the user to select a data limit/time window."""
    options_display = ", ".join(TIME_WINDOWS)
    while True:
        choice = (
            input(f"Enter data limit ({options_display}) [{default}]: ")
            .strip()
            .lower()
        )
        if not choice:
            return default
        if choice in TIME_WINDOWS:
            return choice
        print(f"Please enter one of: {options_display}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CognitiveTrail Navigator — local, consent-first data fetcher."
    )
    parser.add_argument(
        "command",
        choices=["fetch-history"],
        help="Action to perform (currently only browser history ingestion).",
    )
    parser.add_argument(
        "--time-window",
        choices=TIME_WINDOWS,
        help="Restrict ingestion to a relative time window.",
    )
    parser.add_argument(
        "--browsers",
        nargs="+",
        default=["chrome", "firefox", "edge"],
        help="Browsers to include (chrome, firefox, edge).",
    )
    args = parser.parse_args()

    if args.command == "fetch-history":
        window = _prompt_time_window(args.time_window or "last week")
        pipeline = build_pipeline()
        ctx = AgentContext(
            time_window=window,
            since=resolve_window_start(window),
            browsers=args.browsers,
            audit=AuditLogger(),
            store=LocalStore(),
        )
        run_pipeline(pipeline, ctx)


if __name__ == "__main__":
    main()

