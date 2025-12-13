# API Reference

## CLI Commands

### fetch-history

Ingest and analyze browser history data.

**Usage:**
```bash
python -m src.cli fetch-history [OPTIONS]
```

**Options:**

- `--browsers [chrome|firefox|edge]`: Specify browsers to include (default: all)
- `--time-window [today|last week|last month|1 year]`: Set default time window

**Examples:**

```bash
# Basic usage
python -m src.cli fetch-history

# Specific browsers
python -m src.cli fetch-history --browsers chrome firefox

# With time window
python -m src.cli fetch-history --time-window "last month"
```

## Python API

### Core Classes

#### `AgentContext`

Context object passed through the pipeline.

**Attributes:**
- `time_window: str` - Selected time window
- `since: datetime` - Calculated start time
- `browsers: Iterable[str]` - Browser list
- `consents: Dict[str, bool]` - Consent decisions
- `history: List[BrowserEntry]` - Ingested entries
- `analyze_with_llamaindex: bool` - Analysis flag
- `llm_analysis_result: Optional[str]` - Analysis output

#### `BrowserEntry`

Represents a single browser history entry.

**Attributes:**
- `source: str` - Browser name
- `url: str` - Visited URL
- `title: Optional[str]` - Page title
- `visit_time: datetime` - Visit timestamp
- `query: Optional[str]` - Search query (if any)
- `ip: Optional[str]` - Local IP address

#### `LocalStore`

Manages data persistence.

**Methods:**
- `save_browser_history(entries: Iterable[BrowserEntry]) -> int`: Save entries and return count

#### `AuditLogger`

Manages audit logging.

**Methods:**
- `log(event: str, detail: Optional[str])`: Log an event

## Pipeline Functions

### `build_pipeline() -> List[PipelineStep]`

Constructs the agent pipeline.

**Returns:** List of pipeline step functions

### `run_pipeline(pipeline: List[PipelineStep], ctx: AgentContext) -> AgentContext`

Executes the pipeline.

**Parameters:**
- `pipeline`: List of step functions
- `ctx`: Initial context

**Returns:** Updated context

