# 🚀 Quick Start Guide (UV + Docker)

## Prerequisites

- Docker & Docker Compose
- UV package manager (optional for local dev)

## Option 1: Docker (Recommended)

### 1. Setup
```bash
# Clone repository
git clone <repository>
cd job-fair-navigator

# Copy environment file
cp .env.example .env

# Edit .env with your Azure OpenAI credentials
nano .env
```

### 2. Run Setup Script
```bash
chmod +x docker-setup.sh
./docker-setup.sh
```

### 3. Start Application
```bash
docker-compose up -d
```

### 4. Access
Open browser: http://localhost:8501

### 5. View Logs
```bash
docker-compose logs -f
```

### 6. Stop
```bash
docker-compose down
```

## Option 2: Local Development with UV

### 1. Install UV
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Setup Project
```bash
# Clone repository
git clone <repository>
cd job-fair-navigator

# Create virtual environment
uv venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
uv pip install -e .

# For development
uv pip install -e ".[dev]"
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 4. Scrape Data
```bash
python scripts/scrape_jobs.py
python scripts/build_vectorstore.py
```

### 5. Run Application
```bash
streamlit run app.py
```

## Using Makefile (Easier)

### Local Development
```bash
make install      # Install dependencies
make scrape       # Scrape jobs
make vectorstore  # Build vector store
make run          # Run app
```

### Docker
```bash
make docker-build  # Build image
make docker-up     # Start containers
make docker-logs   # View logs
make docker-down   # Stop containers
```

### Maintenance
```bash
make check-db     # Check database health
make test         # Run tests
make lint         # Run linters
make format       # Format code
make clean        # Clean cache
```

## Common Commands

### Update Dependencies
```bash
# With UV (local)
uv pip install --upgrade -e .

# With Docker
docker-compose build --no-cache
```

### Re-scrape Jobs
```bash
# Local
make scrape
make vectorstore

# Docker
docker-compose run --rm app python scripts/scrape_jobs.py
docker-compose run --rm app python scripts/build_vectorstore.py
```

### Backup Data
```bash
# Backup
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Restore
tar -xzf backup-20250120.tar.gz
```

## Troubleshooting

### UV Installation Issues
```bash
# Verify installation
uv --version

# Reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Docker Issues
```bash
# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Database Issues
```bash
# Reset database
rm -rf data/jobs.db data/chroma_db/
make scrape
make vectorstore
```

## Performance Tips

### UV is Fast! 🚀
- 10-100x faster than pip
- Better dependency resolution
- Automatic virtual environment management

### Docker Optimization
```bash
# Use BuildKit for faster builds
export DOCKER_BUILDKIT=1
docker-compose build
```

---

**Need help?** Check the full documentation in `docs/` or open an issue.