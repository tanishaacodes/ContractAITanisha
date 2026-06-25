#!/bin/bash
set -e

echo "🚀 Starting ContractAI Production Server..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Error: Virtual environment not found!"
    echo "Please create it first: python -m venv venv"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Load environment variables
echo "Loading environment variables..."
export $(cat .env | grep -v '^#' | xargs)

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs uploads staticfiles chroma_db

# Check database connection
echo "Checking database connection..."
python manage.py check --database default || {
    echo "❌ Error: Cannot connect to database!"
    echo "Please check your database settings in .env"
    exit 1
}

# Database migrations
echo "Running migrations..."
python manage.py migrate --noinput || {
    echo "❌ Error: Migration failed!"
    exit 1
}

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️  Warning: Static files collection failed (may be okay)"

# Create cache tables
echo "Creating cache tables..."
python manage.py createcachetable || echo "⚠️  Cache table creation skipped"

# Download ML models (one-time)
echo "Verifying ML models..."
python -c "from sentence_transformers import SentenceTransformer; print('Loading model...'); SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); print('✅ Model loaded successfully')" || {
    echo "⚠️  Warning: ML model download failed - will try on first request"
}

# Check if Ollama is running
echo "Checking Ollama service..."
curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama is running" || echo "⚠️  Warning: Ollama not running - some AI features may not work"

# Check if Qdrant is running
echo "Checking Qdrant service..."
curl -s http://localhost:6333/health > /dev/null && echo "✅ Qdrant is running" || echo "⚠️  Warning: Qdrant not running - RAG features may not work"

# Check if Redis is running
echo "Checking Redis service..."
redis-cli ping > /dev/null 2>&1 && echo "✅ Redis is running" || echo "⚠️  Warning: Redis not running - caching disabled"

# Set number of workers based on CPU cores
NUM_WORKERS=$(python -c "import multiprocessing; print(min(4, multiprocessing.cpu_count()))")
echo "Using $NUM_WORKERS Gunicorn workers"

# Start Gunicorn with proper settings
echo "Starting Gunicorn server on 0.0.0.0:8002..."
echo "=========================================="
echo "Access API at: http://your-server-ip:8002"
echo "Press Ctrl+C to stop"
echo "=========================================="

exec gunicorn settings.wsgi:application \
  --bind 0.0.0.0:8002 \
  --workers $NUM_WORKERS \
  --threads 2 \
  --timeout 600 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info \
  --worker-class sync \
  --worker-tmp-dir /dev/shm \
  --preload
