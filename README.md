# CognitiveTrail Navigator

<div align="center">

**A Privacy-First Browser History Analysis Tool with AI-Powered Insights**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## Overview

CognitiveTrail Navigator is an enterprise-grade, privacy-first application designed to analyze browser history data locally with AI-powered insights. Built on a pipeline architecture, it emphasizes explicit user consent, read-only data access, and complete data privacy—all processing occurs on your local machine.

### Key Highlights

- 🔒 **100% Local Processing** - No data leaves your machine
- ✅ **Consent-First Architecture** - Explicit approval required for every data source
- 🤖 **AI-Powered Analysis** - Leverages LlamaIndex for intelligent behavioral insights
- 📊 **Rich Visualizations** - Interactive charts and HTML reports
- 🔍 **Multi-Browser Support** - Chrome, Firefox, and Edge
- 📝 **Complete Audit Trail** - Full logging of all operations

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CognitiveTrail Navigator                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   CLI Entry     │
                    │   (src/cli.py)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Consent Agent   │
                    │ (src/consent.py)│
                    │  • Gmail        │
                    │  • Filesystem   │
                    │  • Browser Hist │
                    │  • LLM Analysis │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Ingest Agent   │
                    │(browser_history)│
                    │  • Chrome       │
                    │  • Firefox      │
                    │  • Edge         │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Store Agent    │
                    │  (storage.py)   │
                    │  • SQLite DB    │
                    │  • CSV Export   │
                    │  • HTML Report  │
                    │  • Graph JSON   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   UI Agent      │
                    │  (notifications)│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Analysis Agent  │
                    │ (llm_analysis)  │
                    │  • LlamaIndex   │
                    │  • Query Data   │
                    │  • Graph Data   │
                    │  • AI Insights  │
                    └────────┬────────┘
                             │
                             ▼
              ┌──────────────┴──────────────┐
              │                             │
    ┌─────────▼─────────┐      ┌──────────▼──────────┐
    │  Analysis Report  │      │  HTML Visualizations│
    │  (llm_analysis.txt│      │  (analyze.html)     │
    └───────────────────┘      └─────────────────────┘
```

---

## Features

### Core Capabilities

- **Browser History Ingestion**
  - Read-only access to Chrome, Firefox, and Edge history databases
  - Automatic profile detection and scanning
  - Temporary file copying to preserve original databases
  - Time-window filtering (today, last week, last month, 1 year)

- **Data Storage & Export**
  - SQLite database for structured queries
  - CSV export for spreadsheet analysis
  - HTML reports with clickable URLs
  - Interactive charts and visualizations

- **AI-Powered Analysis**
  - Learning direction assessment
  - Working pattern identification
  - Mental model evolution tracking
  - Research interest spike detection
  - Professional personality profiling

- **Privacy & Security**
  - Explicit consent for each data source
  - Read-only database access
  - Local-only processing
  - Complete audit logging
  - No network uploads by default

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Docker (optional, for containerized deployment)
- Browser history access (close browsers before running)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd CognitiveTrail-Navigator

# Build and run with Docker Compose
docker-compose up --build
```

#### Option 2: Local Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.cli fetch-history
```

### Optional: Ollama Setup (for AI Analysis)

If you want to use local AI analysis:

```bash
# Install Ollama (https://ollama.ai/)
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended model
ollama pull llama3.2
```

---

## Usage

### Basic Command

```bash
python -m src.cli fetch-history
```

### Advanced Options

```bash
# Specify browsers and time window
python -m src.cli fetch-history \
  --browsers chrome firefox edge \
  --time-window "last month"

# Using Docker
docker-compose run app fetch-history --browsers chrome firefox
```

### Interactive Flow

1. **Time Window Selection**: Choose data range (today, last week, last month, 1 year)
2. **Consent Prompts**: Approve or decline access to:
   - Gmail (OAuth)
   - Local filesystem
   - Browser history
   - AI analysis
3. **Processing**: Application ingests and analyzes data
4. **Results**: View outputs in `data/` directory

---

## Output Files

All outputs are saved in the `data/` directory:

| File | Description |
|------|-------------|
| `browser_history.csv` | Raw data export (CSV format) |
| `browser_history.html` | Interactive HTML table with clickable URLs |
| `analyze.html` | Interactive charts and visualizations |
| `graph_data.json` | Graph data for AI analysis |
| `llm_analysis.txt` | AI-generated behavioral insights |
| `ctn.sqlite` | SQLite database for queries |
| `audit.log` | Complete audit trail |

---

## Project Structure

```
CognitiveTrail-Navigator/
├── src/                    # Source code
│   ├── agents.py          # Pipeline orchestration
│   ├── browser_history.py # Browser data ingestion
│   ├── cli.py             # Command-line interface
│   ├── consent.py         # Consent management
│   ├── llm_analysis.py    # AI analysis with LlamaIndex
│   └── storage.py         # Data persistence
├── data/                   # Output directory (gitignored)
├── docs/                   # Documentation
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

---

## Docker Deployment

### Using Docker Compose

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Run commands
docker-compose exec app python -m src.cli fetch-history

# Stop services
docker-compose down
```

### Using Dockerfile Directly

```bash
# Build image
docker build -t cognitive-trail .

# Run container
docker run -v $(pwd)/data:/app/data cognitive-trail fetch-history
```

---

## Configuration

### Environment Variables

- `HF_TOKEN`: HuggingFace API token (optional, for cloud-based AI)
- `OLLAMA_HOST`: Ollama server host (default: localhost:11434)

### Browser Paths

The application automatically detects browser history locations. For custom paths, edit `KNOWN_HISTORY_PATHS` in `src/browser_history.py`.

---

## Security & Privacy

- **Local-Only Processing**: All data processing occurs on your machine
- **Read-Only Access**: Browser databases are copied to temp files, originals remain untouched
- **Explicit Consent**: Every data source requires user approval
- **Audit Logging**: Complete trail of all operations
- **No Telemetry**: Zero external data transmission

---

## Troubleshooting

### Browser History Not Found

- Ensure browsers are closed before running
- Check browser profile paths in `src/browser_history.py`
- Verify file permissions

### AI Analysis Fails

- Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
- Pull model: `ollama pull llama3.2`
- Check Ollama service: `ollama list`

### Docker Issues

- Ensure Docker is running: `docker ps`
- Check logs: `docker-compose logs`
- Rebuild images: `docker-compose build --no-cache`

---

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Support

For issues, questions, or contributions, please open an issue on the repository.

---

<div align="center">

**CognitiveTrail Navigator** - Privacy-First Browser Analytics

Made with ❤️ for privacy-conscious users

</div>
