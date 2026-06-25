# 🚀 Quick Command Reference

## SSH into Server

```bash
ssh username@your-server-ip
cd /path/to/contractbuild/backend
```

---

## Check What's Running

```bash
# Run diagnostic script
chmod +x diagnose_deployment.sh
./diagnose_deployment.sh

# Check processes
ps aux | grep gunicorn
ps aux | grep celery
ps aux | grep ollama

# Check services
systemctl status contractai-backend
systemctl status contractai-celery
systemctl status nginx
systemctl status redis
```

---

## Start Services

```bash
# Quick start (development)
chmod +x start_production.sh
./start_production.sh

# Production with systemd
sudo systemctl start contractai-backend
sudo systemctl start contractai-celery

# Start Ollama
ollama serve &

# Start Qdrant (Docker)
docker start qdrant
# OR
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
```

---

## Stop Services

```bash
# Stop systemd services
sudo systemctl stop contractai-backend
sudo systemctl stop contractai-celery

# Stop Gunicorn manually
pkill -f gunicorn

# Stop Celery manually
pkill -f celery
```

---

## View Logs

```bash
# Real-time Django logs
tail -f logs/error.log
tail -f logs/access.log

# Systemd logs
sudo journalctl -u contractai-backend -f
sudo journalctl -u contractai-celery -f

# Nginx logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Last 100 lines
tail -100 logs/error.log
```

---

## Database Commands

```bash
# Activate venv first
source venv/bin/activate

# Run migrations
python manage.py migrate

# Check database
python manage.py check --database default

# Database shell
python manage.py dbshell

# Create superuser
python manage.py createsuperuser

# Show migrations status
python manage.py showmigrations
```

---

## Fix Slow Performance

```bash
# 1. Enable model caching (already created)
# Just restart server to use api/model_cache.py

# 2. Start Celery for async tasks
celery -A celery_app worker -l info --concurrency=2

# 3. Check if Ollama is running
ollama list
ollama serve &

# 4. Increase Gunicorn timeout
# Edit: gunicorn ... --timeout 600

# 5. Add database indexes
python manage.py dbshell
# Then:
CREATE INDEX idx_contract_user ON api_contract(user_id);
CREATE INDEX idx_clause_contract ON api_clause(contract_id);
```

---

## Fix Non-Working Functions

```bash
# 1. Check .env exists
ls -la .env

# 2. Check services
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:6333/health     # Qdrant
redis-cli ping                        # Redis

# 3. Check permissions
ls -la uploads/
ls -la chroma_db/

# Fix permissions
sudo chown -R $USER:www-data uploads/
sudo chown -R $USER:www-data chroma_db/
chmod 775 uploads/ chroma_db/

# 4. Check CORS settings in settings.py
grep CORS_ALLOWED settings.py
```

---

## Update Code from Git

```bash
# Pull latest code
git pull origin main

# Restart services
sudo systemctl restart contractai-backend
sudo systemctl restart contractai-celery

# OR if using manual start
pkill -f gunicorn
./start_production.sh
```

---

## Install Dependencies

```bash
# Activate venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install Ollama model
ollama pull qwen2.5:0.5b

# Download ML models
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

---

## Test API Endpoints

```bash
# Health check
curl http://localhost:8002/api/health

# Test with auth (replace TOKEN)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8002/api/contracts

# Test Ollama directly
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:0.5b",
  "prompt": "Hello"
}'

# Test Qdrant
curl http://localhost:6333/collections
```

---

## Performance Monitoring

```bash
# Check CPU usage
top -u your-username

# Check memory
free -h

# Check disk
df -h

# Check network
netstat -tuln | grep :8002

# Check slow queries (if django-silk installed)
# Visit: http://your-server:8002/silk/

# Profile a specific endpoint
time curl http://localhost:8002/api/contracts
```

---

## Emergency Commands

```bash
# Kill all related processes
pkill -9 -f gunicorn
pkill -9 -f celery
pkill -9 -f manage.py

# Restart everything
sudo systemctl daemon-reload
sudo systemctl restart contractai-backend
sudo systemctl restart contractai-celery
sudo systemctl restart nginx
sudo systemctl restart redis

# Clear all caches
redis-cli FLUSHALL
rm -rf chroma_db/*

# Reset database (DANGER!)
python manage.py flush
python manage.py migrate
```

---

## Useful Aliases (add to ~/.bashrc)

```bash
# Add these to ~/.bashrc
alias cdcontract="cd /path/to/contractbuild/backend"
alias venvactivate="source /path/to/contractbuild/backend/venv/bin/activate"
alias djangologs="tail -f /path/to/contractbuild/backend/logs/error.log"
alias djangostatus="systemctl status contractai-backend"
alias djangorestart="sudo systemctl restart contractai-backend"

# Then run: source ~/.bashrc
```

---

## Common Issues & Quick Fixes

### Issue: "502 Bad Gateway"
```bash
# Check if Django is running
systemctl status contractai-backend
# Restart if needed
sudo systemctl restart contractai-backend
```

### Issue: "Connection refused to Ollama"
```bash
# Start Ollama
ollama serve &
# Check it's running
curl http://localhost:11434/api/tags
```

### Issue: "Permission denied" on uploads
```bash
sudo chown -R $USER:www-data uploads/
chmod 775 uploads/
```

### Issue: "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Database connection failed"
```bash
# Check MySQL is running
sudo systemctl status mysql
# Test connection
mysql -u root -p -e "SHOW DATABASES;"
```

### Issue: "Celery tasks not processing"
```bash
# Check Celery is running
ps aux | grep celery
# Start if not running
celery -A celery_app worker -l info
```

---

## Production Checklist

```bash
# Before going live:
□ Change DEBUG=False in .env
□ Set strong SECRET_KEY and JWT_SECRET
□ Configure ALLOWED_HOSTS
□ Setup HTTPS with SSL certificate
□ Enable firewall (ufw)
□ Setup regular backups
□ Configure log rotation
□ Setup monitoring (e.g., Sentry)
□ Use production payment keys
□ Test all critical endpoints
```

---

## Get Help

```bash
# Run diagnostic
./diagnose_deployment.sh

# View full guide
cat DEPLOYMENT_FIX_GUIDE.md

# Check Django errors
python manage.py check

# Test settings
python manage.py diffsettings
```

---

**Pro tip:** Keep this file open in a terminal while debugging:
```bash
watch -n 5 './diagnose_deployment.sh'
```

This will auto-refresh the diagnostic every 5 seconds!
