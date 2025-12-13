# Quick Start Guide

## Installation (Choose One Method)

### Method 1: Docker (Recommended for Production)

```bash
# Clone repository
git clone <repository-url>
cd CognitiveTrail-Navigator

# Build and run
docker-compose up --build
```

### Method 2: Local Python Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
python -m src.cli fetch-history
```

## First Run

1. **Close all browsers** before running
2. **Run the command:**
   ```bash
   python -m src.cli fetch-history
   ```
3. **Answer prompts:**
   - Time window: `last week` (or press Enter)
   - Gmail access: `n` (unless needed)
   - Filesystem access: `n` (unless needed)
   - Browser history: `y`
   - AI analysis: `y` (requires Ollama)
4. **View results:**
   - Open `data/browser_history.html` in your browser
   - Open `data/analyze.html` for charts
   - Read `data/llm_analysis.txt` for AI insights

## Optional: Setup Ollama for AI Analysis

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull llama3.2

# Verify
ollama list
```

## Troubleshooting

**Browser history not found?**
- Ensure browsers are completely closed
- Check file permissions
- Verify browser paths in `src/browser_history.py`

**AI analysis fails?**
- Install Ollama (see above)
- Check `ollama --version`
- Ensure model is pulled: `ollama pull llama3.2`

**Docker issues?**
- Ensure Docker is running: `docker ps`
- Check logs: `docker-compose logs`
- Rebuild: `docker-compose build --no-cache`

