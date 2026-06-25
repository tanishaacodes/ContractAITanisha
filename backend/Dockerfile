# ContractAI Django Backend Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=contractai.settings

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install PyTorch CPU-only first (prevents CUDA version being pulled in)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies (torch already cached, won't reinstall)
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy English model (~12MB)
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/uploads /app/chroma_db /app/staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Create non-root user
RUN useradd -m -u 1000 contractai && \
    chown -R contractai:contractai /app

USER contractai

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8003/health/ || exit 1

# Default command (overridden by docker-compose)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8003", "contractai.asgi:application"]
