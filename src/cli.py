from __future__ import annotations

import argparse

from .agents import AgentContext, build_pipeline, run_pipeline
from .storage import AuditLogger, LocalStore


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
        "--limit",
        type=int,
        default=100,
        help="Max number of entries to ingest.",
    )
    parser.add_argument(
        "--browsers",
        nargs="+",
        default=["chrome", "firefox", "edge"],
        help="Browsers to include (chrome, firefox, edge).",
    )
    args = parser.parse_args()

    if args.command == "fetch-history":
        pipeline = build_pipeline()
        ctx = AgentContext(
            limit=args.limit,
            browsers=args.browsers,
            audit=AuditLogger(),
            store=LocalStore(),
        )
        run_pipeline(pipeline, ctx)


if __name__ == "__main__":
    main()

