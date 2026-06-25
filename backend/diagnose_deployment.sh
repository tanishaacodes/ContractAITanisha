#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     ContractAI Deployment Diagnostic Tool                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check function
check_service() {
    local name=$1
    local command=$2

    echo -n "Checking $name... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

check_port() {
    local name=$1
    local port=$2

    echo -n "Checking $name (port $port)... "

    if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
        echo -e "${GREEN}✓ Listening${NC}"
        return 0
    else
        echo -e "${RED}✗ Not listening${NC}"
        return 1
    fi
}

echo "═══════════════════════════════════════════════════════════════"
echo "1. CHECKING ENVIRONMENT"
echo "═══════════════════════════════════════════════════════════════"

# Check .env file
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"

    # Check critical env vars
    if grep -q "SECRET_KEY=django-insecure" .env 2>/dev/null; then
        echo -e "${YELLOW}⚠${NC}  WARNING: Using default SECRET_KEY (insecure!)"
    fi

    if grep -q "DEBUG=True" .env 2>/dev/null; then
        echo -e "${YELLOW}⚠${NC}  WARNING: DEBUG=True (not recommended for production)"
    fi
else
    echo -e "${RED}✗${NC} .env file NOT found"
    echo "   → Run: cp .env.example .env"
fi

# Check virtual environment
if [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment exists"
else
    echo -e "${RED}✗${NC} Virtual environment NOT found"
    echo "   → Run: python -m venv venv"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "2. CHECKING REQUIRED SERVICES"
echo "═══════════════════════════════════════════════════════════════"

# Check Python
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python installed: $python_version"
else
    echo -e "${RED}✗${NC} Python3 not found"
fi

# Check MySQL/MariaDB
check_service "MySQL/MariaDB" "mysql --version"

# Check Redis
check_service "Redis" "redis-cli ping"

# Check Ollama
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ollama installed"

    # Check if Ollama is serving
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Ollama is running"

        # Check for required model
        if ollama list 2>/dev/null | grep -q "qwen2.5:0.5b"; then
            echo -e "${GREEN}✓${NC} Qwen model installed"
        else
            echo -e "${YELLOW}⚠${NC}  Qwen model NOT found"
            echo "   → Run: ollama pull qwen2.5:0.5b"
        fi
    else
        echo -e "${RED}✗${NC} Ollama not responding"
        echo "   → Run: ollama serve"
    fi
else
    echo -e "${RED}✗${NC} Ollama not installed"
    echo "   → Install from: https://ollama.com"
fi

# Check Qdrant
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Qdrant is running"
else
    echo -e "${RED}✗${NC} Qdrant not running"
    echo "   → Run: docker run -d -p 6333:6333 qdrant/qdrant"
fi

# Check Nginx
if command -v nginx &> /dev/null; then
    echo -e "${GREEN}✓${NC} Nginx installed"

    if systemctl is-active --quiet nginx 2>/dev/null || pgrep nginx > /dev/null; then
        echo -e "${GREEN}✓${NC} Nginx is running"
    else
        echo -e "${YELLOW}⚠${NC}  Nginx not running"
    fi
else
    echo -e "${YELLOW}⚠${NC}  Nginx not installed (optional)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "3. CHECKING RUNNING PROCESSES"
echo "═══════════════════════════════════════════════════════════════"

# Check Django/Gunicorn
if pgrep -f "gunicorn.*settings.wsgi" > /dev/null; then
    echo -e "${GREEN}✓${NC} Gunicorn is running (production)"
    pgrep -f "gunicorn" | head -5
elif pgrep -f "manage.py runserver" > /dev/null; then
    echo -e "${YELLOW}⚠${NC}  Django dev server is running (not for production!)"
    echo "   → Use: gunicorn settings.wsgi:application"
else
    echo -e "${RED}✗${NC} No Django server running"
fi

# Check Celery
if pgrep -f "celery.*worker" > /dev/null; then
    echo -e "${GREEN}✓${NC} Celery worker is running"
else
    echo -e "${RED}✗${NC} Celery worker not running"
    echo "   → Run: celery -A celery_app worker -l info"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "4. CHECKING NETWORK PORTS"
echo "═══════════════════════════════════════════════════════════════"

check_port "Django/Gunicorn" "8002"
check_port "Redis" "6379"
check_port "Qdrant" "6333"
check_port "Ollama" "11434"
check_port "MySQL" "3306"
check_port "Nginx" "80"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "5. CHECKING FILE PERMISSIONS"
echo "═══════════════════════════════════════════════════════════════"

# Check critical directories
for dir in "uploads" "chroma_db" "staticfiles" "logs"; do
    if [ -d "$dir" ]; then
        perms=$(stat -c "%a" "$dir" 2>/dev/null || stat -f "%A" "$dir" 2>/dev/null)
        echo -e "${GREEN}✓${NC} $dir/ exists (permissions: $perms)"

        if [ ! -w "$dir" ]; then
            echo -e "${YELLOW}⚠${NC}  WARNING: $dir/ not writable"
        fi
    else
        echo -e "${RED}✗${NC} $dir/ does NOT exist"
        echo "   → Run: mkdir -p $dir"
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "6. CHECKING DATABASE CONNECTION"
echo "═══════════════════════════════════════════════════════════════"

if [ -f ".env" ] && [ -d "venv" ]; then
    source venv/bin/activate 2>/dev/null

    if python manage.py check --database default 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Database connection successful"
    else
        echo -e "${RED}✗${NC} Database connection failed"
        echo "   → Check database credentials in .env"
    fi

    # Check migrations
    pending_migrations=$(python manage.py showmigrations 2>/dev/null | grep "\[ \]" | wc -l)
    if [ "$pending_migrations" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} All migrations applied"
    else
        echo -e "${YELLOW}⚠${NC}  $pending_migrations pending migrations"
        echo "   → Run: python manage.py migrate"
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "7. CHECKING SYSTEM RESOURCES"
echo "═══════════════════════════════════════════════════════════════"

# Check disk space
echo "Disk usage:"
df -h . | tail -1 | awk '{print "  Used: "$3" / "$2" ("$5")"}'

# Check memory
echo "Memory usage:"
free -h 2>/dev/null | grep "Mem:" | awk '{print "  Used: "$3" / "$2}' || vm_stat | head -1

# Check CPU
echo "CPU load:"
uptime | awk -F'load average:' '{print "  "$2}'

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "8. TESTING API ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════"

# Test health endpoint
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/api/health 2>/dev/null | grep -q "200"; then
    echo -e "${GREEN}✓${NC} API health check passed"
else
    echo -e "${RED}✗${NC} API health check failed"
    echo "   → Check if Django is running: systemctl status contractai-backend"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "9. RECENT LOGS (Last 10 lines)"
echo "═══════════════════════════════════════════════════════════════"

if [ -f "logs/error.log" ]; then
    echo "Error log:"
    tail -10 logs/error.log | sed 's/^/  /'
else
    echo -e "${YELLOW}⚠${NC}  No error log found"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "SUMMARY & RECOMMENDATIONS"
echo "═══════════════════════════════════════════════════════════════"

# Count issues
issues=0

[ ! -f ".env" ] && ((issues++)) && echo "• Create .env file"
[ ! -d "venv" ] && ((issues++)) && echo "• Create virtual environment"
! pgrep -f "gunicorn" > /dev/null && ((issues++)) && echo "• Start Gunicorn server"
! pgrep -f "celery.*worker" > /dev/null && ((issues++)) && echo "• Start Celery worker"
! curl -s http://localhost:11434/api/tags > /dev/null 2>&1 && ((issues++)) && echo "• Start Ollama service"
! curl -s http://localhost:6333/health > /dev/null 2>&1 && ((issues++)) && echo "• Start Qdrant service"
! redis-cli ping > /dev/null 2>&1 && ((issues++)) && echo "• Start Redis service"

if [ $issues -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! System looks healthy.${NC}"
else
    echo -e "${YELLOW}Found $issues issue(s). Please address them.${NC}"
    echo ""
    echo "Quick start commands:"
    echo "  1. ./start_production.sh          # Start Django"
    echo "  2. celery -A celery_app worker   # Start Celery"
    echo "  3. ollama serve                   # Start Ollama"
fi

echo ""
echo "For detailed fixes, see: DEPLOYMENT_FIX_GUIDE.md"
echo "═══════════════════════════════════════════════════════════════"
