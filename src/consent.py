from __future__ import annotations

from typing import Dict

from .storage import AuditLogger


def prompt_yes_no(question: str) -> bool:
    """Simple CLI consent prompt."""
    while True:
        answer = input(f"{question} [y/N]: ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"", "n", "no"}:
            return False
        print("Please answer with 'y' or 'n'.")


def prompt_llamaindex_analysis() -> bool:
    """Prompt user if they want to analyze browser history using LlamaIndex."""
    return prompt_yes_no("Do you want to analyze browser history more precisely using LlamaIndex?")


def collect_consents(audit: AuditLogger) -> Dict[str, bool]:
    """Ask for explicit consent per resource."""
    prompts = {
        "gmail": "Allow read-only Gmail access via OAuth?",
        "filesystem": "Allow read-only local filesystem scan (for config/paths)?",
        "browser_history": "Allow read-only browser history ingestion (Chrome/Firefox/Edge)?",
    }
    decisions: Dict[str, bool] = {}
    for key, question in prompts.items():
        allowed = prompt_yes_no(question)
        decisions[key] = allowed
        audit.log("consent", f"{key}={'granted' if allowed else 'declined'}")
    return decisions

