from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List

from . import consent
from .browser_history import fetch_browser_history
from .storage import AuditLogger, BrowserEntry, LocalStore


@dataclass
class AgentContext:
    limit: int
    browsers: Iterable[str]
    audit: AuditLogger
    store: LocalStore
    consents: Dict[str, bool] = field(default_factory=dict)
    history: List[BrowserEntry] = field(default_factory=list)
    entries_saved: int = 0


def consent_agent(ctx: AgentContext) -> AgentContext:
    ctx.consents = consent.collect_consents(ctx.audit)
    return ctx


def ingest_agent(ctx: AgentContext) -> AgentContext:
    if ctx.consents.get("browser_history"):
        ctx.audit.log("ingest_start", "browser_history")
        ctx.history = fetch_browser_history(ctx.browsers, ctx.limit)
        ctx.audit.log("ingest_end", f"browser_history_count={len(ctx.history)}")
    return ctx


def store_agent(ctx: AgentContext) -> AgentContext:
    if ctx.history:
        ctx.audit.log("store_start", f"rows={len(ctx.history)}")
        ctx.entries_saved = ctx.store.save_browser_history(ctx.history)
        ctx.audit.log("store_end", f"rows_saved={ctx.entries_saved}")
    return ctx


def ui_agent(ctx: AgentContext) -> AgentContext:
    message = f"Data fetch complete — {ctx.entries_saved} entries saved."
    print(message)
    ctx.audit.log("ui_notify", message)
    return ctx


PipelineStep = Callable[[AgentContext], AgentContext]


def build_pipeline() -> List[PipelineStep]:
    return [consent_agent, ingest_agent, store_agent, ui_agent]


def run_pipeline(pipeline: List[PipelineStep], ctx: AgentContext) -> AgentContext:
    for step in pipeline:
        ctx = step(ctx)
    return ctx

