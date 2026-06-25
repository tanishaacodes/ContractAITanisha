# ContractAI

An enterprise AI platform for intelligent contract analysis, risk assessment, and negotiation management.

## Overview

ContractAI helps organizations:
- Analyze contracts using advanced NLP and ML
- Identify risks and deviations from standard terms
- Track obligations and compliance requirements
- Negotiate more effectively with AI recommendations
- Manage contract portfolios with real-time analytics

**Tech Stack**: 55.7% Python (Django backend) | 44% JavaScript (Vue/React frontend)

## Quick Start

### Backend (Python)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

## Getting Started

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## Docker Setup

Run the complete application using Docker:

```bash
docker-compose up -d
```

---

# Project Structure

```
backend/                  # Django REST API, ML models, data processing
frontend/                 # Vue/React UI, dashboards, visualizations
docker-compose.yml        # Docker configuration
```

---

# Key Features

- 📄 Contract upload and analysis
- 🔍 Automated clause extraction
- ⚠️ Risk scoring and compliance tracking
- 🧠 Semantic search using RAG (Retrieval-Augmented Generation)
- 🤝 Negotiation history tracking and recommendations
- 📊 Portfolio analytics and reporting dashboards

---

# API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/contracts/` | List all contracts |
| POST | `/api/contracts/` | Upload a contract |
| GET | `/api/contracts/{id}/analysis/` | Retrieve contract analysis |
| GET | `/api/contracts/{id}/risks/` | Get identified risks |
| POST | `/api/search/semantic/` | Perform semantic contract search |

---

# Configuration

Create a `.env` file inside the backend directory:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost/contractai
OLLAMA_API_URL=http://localhost:11434
```

---

# Documentation

Additional documentation:

```
backend/
├── DJANGO_SETUP_GUIDE.md       # Backend setup instructions
├── DEPLOYMENT_FIX_GUIDE.md     # Deployment guide
└── QUICK_COMMANDS.md           # Common commands

frontend/
└── README.md                   # Frontend documentation
```

---

# Production Deployment

Before deploying, run:

```bash
python manage.py check --deploy
```

Configure production settings:

- Set `DEBUG=False`
- Configure secure environment variables
- Enable proper database configuration
- Configure security settings

---

## Tech Stack

### Backend
- Django REST Framework
- Machine Learning Models
- Data Processing Pipeline
- PostgreSQL

### Frontend
- Vue / React
- Dashboards
- Data Visualizations

### AI Layer
- RAG-based semantic search
- Ollama API integration

