from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional

from . import consent
from .browser_history import fetch_browser_history
from .storage import AuditLogger, BrowserEntry, DATA_DIR, LocalStore
from .llm_analysis import analyze_with_llamaindex

TIME_WINDOWS = ["today", "last week", "last month", "1 year"]


def resolve_window_start(window: str) -> dt.datetime:
    now = dt.datetime.utcnow()
    if window == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if window == "last week":
        return now - dt.timedelta(days=7)
    if window == "last month":
        return now - dt.timedelta(days=30)
    if window == "1 year":
        return now - dt.timedelta(days=365)
    return now


@dataclass
class AgentContext:
    time_window: str
    since: dt.datetime
    browsers: Iterable[str]
    audit: AuditLogger
    store: LocalStore
    consents: Dict[str, bool] = field(default_factory=dict)
    history: List[BrowserEntry] = field(default_factory=list)
    entries_saved: int = 0
    analyze_with_llamaindex: bool = False
    llm_analysis_result: Optional[str] = None


def consent_agent(ctx: AgentContext) -> AgentContext:
    ctx.consents = consent.collect_consents(ctx.audit)
    # Ask for LlamaIndex analysis consent after browser history consent
    if ctx.consents.get("browser_history"):
        ctx.analyze_with_llamaindex = consent.prompt_llamaindex_analysis()
        ctx.audit.log("consent", f"llamaindex_analysis={'granted' if ctx.analyze_with_llamaindex else 'declined'}")
    return ctx


def ingest_agent(ctx: AgentContext) -> AgentContext:
    if ctx.consents.get("browser_history"):
        ctx.audit.log("ingest_start", "browser_history")
        ctx.history = fetch_browser_history(ctx.browsers, since=ctx.since)
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


def analysis_agent(ctx: AgentContext) -> AgentContext:
    """Analyze browser history using LlamaIndex if requested."""
    if not ctx.analyze_with_llamaindex:
        return ctx
    
    ctx.audit.log("analysis_start", "llamaindex")
    print("\nStarting LlamaIndex analysis...")
    
    csv_path = ctx.store.csv_path
    graph_json_path = DATA_DIR / "graph_data.json"
    
    result = analyze_with_llamaindex(csv_path, graph_json_path)
    
    if result:
        ctx.llm_analysis_result = result
        ctx.audit.log("analysis_end", "llamaindex_success")
        
        # Save analysis result to file
        analysis_path = DATA_DIR / "llm_analysis.txt"
        with analysis_path.open("w", encoding="utf-8") as handle:
            handle.write(result)
        
        print("\n" + "=" * 70)
        print("LLM ANALYSIS RESULTS")
        print("=" * 70)
        print(result)
        print("=" * 70)
        print(f"\nAnalysis saved to: {analysis_path}")
    else:
        ctx.audit.log("analysis_end", "llamaindex_failed")
        print("Analysis failed. Check if LlamaIndex is installed.")
        print("Install with: pip install llama-index")
    
    return ctx


PipelineStep = Callable[[AgentContext], AgentContext]


def build_pipeline() -> List[PipelineStep]:
    return [consent_agent, ingest_agent, store_agent, ui_agent, analysis_agent]


def run_pipeline(pipeline: List[PipelineStep], ctx: AgentContext) -> AgentContext:
    for step in pipeline:
        ctx = step(ctx)
    return ctx

