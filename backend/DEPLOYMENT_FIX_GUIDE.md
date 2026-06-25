# 🚀 SSH Server Deployment Fix Guide

## Critical Issues Identified

Your deployment has several issues causing slow performance and failures:

### 🔴 Critical Problems:
1. **Using Development Server** - `backend.sh` runs `manage.py runserver` (NOT production-ready)
2. **No Async Task Queue** - Heavy ML operations blocking requests
3. **Models Loading on Every Request** - No caching for ML models
4. **Missing External Services** - Ollama, Qdrant, Neo4j may not be running
5. **No Production Server** - Should use Gunicorn/uWSGI
6. **Wrong Timeout Settings** - Gunicorn timeout too short (120s) for AI operations
7. **Missing CORS & Static Files** - Frontend can't connect properly
8. **No Environment Variables** - Using .env.example instead of actual .env

---

## 📋 Quick Diagnosis Commands

Run these on your SSH server to diagnose issues:

```bash
# Check what's running
ps aux | grep python
ps aux | grep gunicorn

# Check services
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:6333/health     # Qdrant
curl http://localhost:7687            # Neo4j

# Check logs
tail -f backend/server.log
tail -f /var/log/nginx/error.log

# Check environment
cd /path/to/contractbuild/backend
cat .env | head -20
```

---

## 🔧 Step-by-Step Fixes

### Step 1: Create Production .env File

```bash
cd /path/to/contractbuild/backend

# Copy example and edit
cp .env.example .env
nano .env
```

**Critical settings to update:**

```env
# Production settings
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-server-ip,localhost

# Database (use production DB, not SQLite)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=contractai_production
DB_USER=contractai_user
DB_PASSWORD=strong_password_here

# Ollama (ensure it's running on server)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b

# Qdrant (ensure it's running)
QDRANT_URL=http://localhost:6333

# Neo4j (if you're using it)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=production_password

# Security
SECRET_KEY=generate-new-secret-key-here
JWT_SECRET=generate-new-jwt-secret-here

# PayPal/Stripe (use production keys)
PAYPAL_MODE=live
```

**Generate secure keys:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

### Step 2: Install & Configure External Services

#### Install Ollama (for AI/LLM)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull qwen2.5:0.5b

# Verify it's running
ollama list
```

#### Install Qdrant (for Vector Search)

```bash
# Using Docker (recommended)
docker run -d -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  --name qdrant \
  qdrant/qdrant

# Or download binary
wget https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz
tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz
./qdrant &
```

#### Install Redis (for Celery task queue)

```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl enable redis
sudo systemctl start redis
```

---

### Step 3: Setup Celery for Async Tasks

**Create celery.py in backend directory:**

```bash
nano backend/celery.py
```

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

app = Celery('contractai')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configure Celery
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
)
```

**Update settings.py:**

```python
# Add to settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

**Start Celery workers:**

```bash
# In separate terminal/screen sessions
celery -A backend worker -l info --concurrency=2

# For slow AI tasks
celery -A backend worker -l info --concurrency=1 -Q slow_tasks
```

---

### Step 4: Create Production Deployment Scripts

#### Create production startup script:

**backend/start_production.sh:**

```bash
#!/bin/bash
set -e

echo "🚀 Starting ContractAI Production Server..."

# Activate virtual environment
source venv/bin/activate

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create cache tables
python manage.py createcachetable

# Download ML models (one-time)
echo "Verifying ML models..."
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" || echo "Model download needed"

# Start Gunicorn with proper settings
echo "Starting Gunicorn..."
gunicorn settings.wsgi:application \
  --bind 0.0.0.0:8002 \
  --workers 4 \
  --threads 2 \
  --timeout 600 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info \
  --preload \
  --worker-class sync \
  --worker-tmp-dir /dev/shm
```

Make it executable:
```bash
chmod +x backend/start_production.sh
```

---

### Step 5: Optimize ML Model Loading

**Create model cache (backend/api/model_cache.py):**

```python
"""
Singleton pattern for ML model caching
"""
from sentence_transformers import SentenceTransformer
from threading import Lock
import logging

logger = logging.getLogger(__name__)

class ModelCache:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._models = {}
        self._initialized = True
        logger.info("ModelCache initialized")

    def get_embedding_model(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        if model_name not in self._models:
            with self._lock:
                if model_name not in self._models:
                    logger.info(f"Loading model: {model_name}")
                    self._models[model_name] = SentenceTransformer(model_name)
                    logger.info(f"Model loaded: {model_name}")
        return self._models[model_name]

# Global instance
model_cache = ModelCache()
```

**Update your views to use cached models:**

```python
from api.model_cache import model_cache

# In your views, replace:
# model = SentenceTransformer('...')
# With:
model = model_cache.get_embedding_model()
```

---

### Step 6: Add Database Connection Pooling

**Update settings.py:**

```python
# Add to settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}

# Add caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'contractai',
        'TIMEOUT': 300,
    }
}
```

---

### Step 7: Setup Systemd Services

**Create /etc/systemd/system/contractai-backend.service:**

```ini
[Unit]
Description=ContractAI Backend (Gunicorn)
After=network.target mysql.service redis.service

[Service]
Type=notify
User=your-username
Group=www-data
WorkingDirectory=/path/to/contractbuild/backend
Environment="PATH=/path/to/contractbuild/backend/venv/bin"

ExecStart=/path/to/contractbuild/backend/venv/bin/gunicorn \
  settings.wsgi:application \
  --bind 0.0.0.0:8002 \
  --workers 4 \
  --timeout 600 \
  --max-requests 1000 \
  --log-file=/path/to/contractbuild/backend/logs/gunicorn.log \
  --access-logfile=/path/to/contractbuild/backend/logs/access.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Create /etc/systemd/system/contractai-celery.service:**

```ini
[Unit]
Description=ContractAI Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=your-username
Group=www-data
WorkingDirectory=/path/to/contractbuild/backend
Environment="PATH=/path/to/contractbuild/backend/venv/bin"

ExecStart=/path/to/contractbuild/backend/venv/bin/celery \
  -A backend worker \
  -l info \
  --concurrency=2 \
  --logfile=/path/to/contractbuild/backend/logs/celery.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start services:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable contractai-backend
sudo systemctl enable contractai-celery
sudo systemctl start contractai-backend
sudo systemctl start contractai-celery

# Check status
sudo systemctl status contractai-backend
sudo systemctl status contractai-celery
```

---

### Step 8: Setup Nginx Reverse Proxy

**Create /etc/nginx/sites-available/contractai:**

```nginx
upstream backend {
    server 127.0.0.1:8002 fail_timeout=0;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    # Frontend
    location / {
        root /path/to/contractbuild/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for slow AI operations
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # Static files
    location /static/ {
        alias /path/to/contractbuild/backend/staticfiles/;
    }

    # Uploaded files
    location /uploads/ {
        alias /path/to/contractbuild/backend/uploads/;
    }
}
```

**Enable and restart Nginx:**

```bash
sudo ln -s /etc/nginx/sites-available/contractai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🐛 Common Issues & Fixes

### Issue 1: "Some functions taking too long"

**Likely causes:**
- ML models loading on every request
- No Celery for async tasks
- Slow database queries
- Ollama not running

**Fixes:**
```bash
# 1. Implement model caching (see Step 5)
# 2. Start Celery workers
celery -A backend worker -l info

# 3. Add database indexes
python manage.py dbshell
# Then run:
CREATE INDEX idx_contract_user ON api_contract(user_id);
CREATE INDEX idx_clause_contract ON api_clause(contract_id);

# 4. Ensure Ollama is running
ollama serve
```

---

### Issue 2: "Some functions not working"

**Likely causes:**
- Missing environment variables
- External services down (Ollama, Qdrant, Neo4j)
- CORS errors
- File permission issues

**Diagnostic commands:**

```bash
# Check logs
tail -f backend/logs/error.log

# Check services
systemctl status ollama
systemctl status qdrant
curl http://localhost:11434/api/tags

# Check permissions
ls -la backend/uploads/
ls -la backend/chroma_db/

# Fix permissions
sudo chown -R your-user:www-data backend/uploads/
sudo chown -R your-user:www-data backend/chroma_db/
chmod 775 backend/uploads/
chmod 775 backend/chroma_db/
```

---

### Issue 3: "CORS errors from frontend"

**Add to settings.py:**

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://your-domain.com",
    "https://your-domain.com",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
```

---

### Issue 4: "Out of memory errors"

**Optimize Gunicorn workers:**

```bash
# Reduce workers if low RAM
# Formula: (2 x CPU cores) + 1
# For 2 CPU cores = 5 workers max

gunicorn settings.wsgi:application \
  --workers 2 \
  --threads 1 \
  --worker-class sync \
  --max-requests 500
```

---

### Issue 5: "PDF generation/OCR too slow"

**Move to Celery task:**

```python
# In api/tasks.py
from celery import shared_task

@shared_task(bind=True, time_limit=3600)
def process_contract_async(self, contract_id):
    """Process contract in background"""
    from api.models import Contract
    contract = Contract.objects.get(id=contract_id)
    # Do heavy processing...
    return {'status': 'completed'}

# In views.py
from api.tasks import process_contract_async

@api_view(['POST'])
def upload_contract(request):
    # Save contract
    contract = Contract.objects.create(...)

    # Queue for async processing
    task = process_contract_async.delay(contract.id)

    return Response({
        'contract_id': contract.id,
        'task_id': task.id,
        'status': 'processing'
    })
```

---

## 📊 Performance Monitoring

**Install monitoring tools:**

```bash
pip install django-debug-toolbar django-silk

# Add to settings.py for development
INSTALLED_APPS += ['debug_toolbar', 'silk']

# View slow queries
python manage.py showmigrations
```

**Check system resources:**

```bash
# CPU usage
top -u your-username

# Memory usage
free -h

# Disk usage
df -h

# Network
netstat -tuln | grep :8002
```

---

## ✅ Post-Deployment Checklist

```bash
# 1. Environment variables set
cat backend/.env | grep SECRET_KEY

# 2. Database migrated
python manage.py migrate --check

# 3. Static files collected
ls backend/staticfiles/

# 4. Services running
systemctl status contractai-backend
systemctl status contractai-celery
systemctl status redis
ollama list

# 5. Qdrant running
curl http://localhost:6333/health

# 6. Can access API
curl http://localhost:8002/api/health

# 7. Frontend built
ls frontend/dist/

# 8. Nginx configured
sudo nginx -t

# 9. Logs accessible
tail backend/logs/error.log

# 10. Firewall configured
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## 🚀 Quick Start Commands

**Start everything:**

```bash
# 1. Start external services
sudo systemctl start redis
docker start qdrant  # if using Docker
ollama serve &

# 2. Start Django backend
sudo systemctl start contractai-backend
sudo systemctl start contractai-celery

# 3. Start Nginx
sudo systemctl start nginx

# 4. Check status
sudo systemctl status contractai-backend
curl http://localhost:8002/api/health
```

**Stop everything:**

```bash
sudo systemctl stop contractai-backend
sudo systemctl stop contractai-celery
sudo systemctl stop nginx
```

**View logs:**

```bash
# Real-time logs
sudo journalctl -u contractai-backend -f

# Celery logs
tail -f backend/logs/celery.log

# Nginx logs
tail -f /var/log/nginx/error.log
```

---

## 📞 Need Help?

1. **Check logs first:** `tail -f backend/logs/error.log`
2. **Verify services:** `systemctl status contractai-backend`
3. **Test API directly:** `curl http://localhost:8002/api/health`
4. **Check external services:** Ollama, Qdrant, Redis, MySQL

---

## 🎯 Expected Performance After Fixes

- **Contract upload:** < 5 seconds
- **Clause extraction:** 10-30 seconds (async)
- **RAG queries:** 1-3 seconds
- **Dashboard load:** < 2 seconds
- **API response:** < 500ms (cached)

Good luck with your deployment! 🚀
