# Deployment Guide

## Docker Deployment

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

### Quick Start

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f app

# Execute commands
docker-compose exec app python -m src.cli fetch-history
```

### Production Deployment

1. **Configure Environment Variables**

```bash
# .env file
HF_TOKEN=your_token_here
OLLAMA_HOST=ollama:11434
```

2. **Build Production Image**

```bash
docker build -t cognitive-trail:latest .
```

3. **Run Container**

```bash
docker run -d \
  --name cognitive-trail \
  -v $(pwd)/data:/app/data \
  -e HF_TOKEN=${HF_TOKEN} \
  cognitive-trail:latest
```

## Local Deployment

### System Requirements

- Python 3.10 or higher
- 2GB RAM minimum
- 500MB disk space

### Installation Steps

1. **Clone Repository**

```bash
git clone <repository-url>
cd CognitiveTrail-Navigator
```

2. **Create Virtual Environment**

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure (Optional)**

- Set `HF_TOKEN` for HuggingFace API
- Install Ollama for local AI analysis
- Adjust browser paths in `src/browser_history.py`

5. **Run Application**

```bash
python -m src.cli fetch-history
```

## WSL Deployment

### Setup on Windows WSL

1. **Install Python**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

2. **Install Application**

```bash
cd /path/to/CognitiveTrail-Navigator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Install Ollama (Optional)**

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
```

4. **Run**

```bash
python -m src.cli fetch-history
```

## Monitoring

### Logs

- Application logs: `data/audit.log`
- Docker logs: `docker-compose logs`
- System logs: Check container/system logs

### Health Checks

```bash
# Check application
docker-compose exec app python -c "from src.llm_analysis import check_llamaindex_available; print(check_llamaindex_available())"

# Check Ollama
curl http://localhost:11434/api/tags
```

## Backup

### Data Backup

```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Restore
tar -xzf backup-YYYYMMDD.tar.gz
```

### Database Backup

```bash
sqlite3 data/ctn.sqlite ".backup backup.sqlite"
```

