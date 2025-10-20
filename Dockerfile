# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PATH="/root/.local/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV (it installs to /root/.local/bin by default)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify UV installation
RUN uv --version

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies with UV
RUN uv pip install --system .

# Copy application
COPY . .

# Create directories
RUN mkdir -p data/chroma_db logs

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]