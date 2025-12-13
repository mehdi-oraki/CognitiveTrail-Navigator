# Architecture Documentation

## System Overview

CognitiveTrail Navigator follows a pipeline-based architecture with explicit agent orchestration. The system is designed for privacy, transparency, and extensibility.

## Pipeline Flow

```
User Input (CLI)
    ↓
Consent Agent
    ├── Gmail Access
    ├── Filesystem Access
    ├── Browser History Access
    └── AI Analysis Consent
    ↓
Ingest Agent
    ├── Chrome History
    ├── Firefox History
    └── Edge History
    ↓
Store Agent
    ├── SQLite Database
    ├── CSV Export
    ├── HTML Reports
    └── Graph Data (JSON)
    ↓
UI Agent
    └── User Notifications
    ↓
Analysis Agent (Optional)
    ├── Query Data Extraction
    ├── Graph Data Processing
    └── LLM Analysis (LlamaIndex)
    ↓
Results
    ├── llm_analysis.txt
    └── Enhanced Reports
```

## Components

### Agents

- **Consent Agent**: Manages user permissions for each data source
- **Ingest Agent**: Reads browser history from supported browsers
- **Store Agent**: Persists data in multiple formats
- **UI Agent**: Provides user feedback and notifications
- **Analysis Agent**: Performs AI-powered behavioral analysis

### Data Flow

1. **Input**: Browser history databases (read-only)
2. **Processing**: Temporary file copying, querying, aggregation
3. **Storage**: SQLite, CSV, HTML, JSON formats
4. **Analysis**: LLM-based insights generation
5. **Output**: Reports and visualizations

## Technology Stack

- **Language**: Python 3.10+
- **Framework**: LlamaIndex (for AI analysis)
- **Storage**: SQLite, CSV
- **Containerization**: Docker
- **LLM Backend**: Ollama (local) or HuggingFace (cloud)

## Security Model

- Read-only access to source data
- Temporary file isolation
- Explicit consent requirements
- Complete audit logging
- Local-only processing

