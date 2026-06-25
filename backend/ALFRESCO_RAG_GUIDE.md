# Alfresco Integration & RAG System Guide

## Overview

This system integrates Alfresco CMS with a powerful RAG (Retrieval-Augmented Generation) engine for intelligent contract extraction, analysis, and search.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────┐
│   Alfresco CMS  │────▶│  Django Backend  │────▶│  ChromaDB     │
│  (Document Mgmt)│     │  (Extraction)    │     │ (Vector Store)│
└─────────────────┘     └──────────────────┘     └───────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  LLM (Qwen/GPT)  │
                        │ (Clause Extract) │
                        └──────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  MySQL Database  │
                        │  (Intelligence)  │
                        └──────────────────┘
```

## Features

### 1. **Alfresco Document Extraction**
- Connects to Alfresco CMS via REST API or python-alfresco-api
- Fetches documents from specific folders
- Supports PDF, DOCX, and other document formats
- Extracts document metadata and properties
- Handles document versioning

### 2. **RAG-Based Intelligence Extraction**
- Chunks documents into semantic segments (1000 chars, 100 overlap)
- Generates embeddings using Contracts-BERT or sentence-transformers
- Stores embeddings in ChromaDB vector database
- Performs semantic search across all contracts
- Extracts legal clauses using LLM (Qwen or GPT-4)

### 3. **Extracted Legal Intelligence**
- **Parties**: All entities entering the agreement
- **Termination Clauses**: How and when contract can be ended
- **Liability Limitations**: Caps on damages and responsibility
- **Governing Law**: Jurisdiction and applicable laws
- **Confidentiality**: Duration and scope of confidential information
- **Payment Terms**: Payment schedules and conditions
- **Arbitration**: Dispute resolution mechanisms
- **Indemnification**: Indemnification obligations
- **Force Majeure**: Force majeure provisions

## Installation

### 1. Install Dependencies

```bash
cd django_backend
pip install -r requirements.txt
```

Required packages:
- `langchain==0.3.14`
- `langchain-community==0.3.14`
- `langchain-openai==0.3.0`
- `chromadb==0.5.23`
- `python-alfresco-api==0.1.3`
- `sentence-transformers==3.3.1`

### 2. Configure Environment Variables

Create `.env` file in `django_backend/`:

```env
# Alfresco Configuration
ALFRESCO_URL=http://localhost:8080/alfresco
ALFRESCO_USER=admin
ALFRESCO_PASSWORD=admin

# ChromaDB Path (optional, defaults to ./chroma_db)
CHROMADB_PATH=./chroma_db

# Contracts-BERT Model (optional)
CONTRACTS_BERT_MODEL=sentence-transformers/all-MiniLM-L6-v2
# For legal-specific: nlpaueb/legal-bert-base-uncased

# OpenAI API Key (optional, for GPT-4 extraction)
OPENAI_API_KEY=sk-your-api-key

# Ollama Configuration (for local Qwen extraction)
OLLAMA_MODEL=qwen2.5:0.5b
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Setup Alfresco (if not already running)

**Using Docker:**
```bash
docker run -d -p 8080:8080 alfresco/alfresco-content-repository-community:latest
```

**Access Alfresco:**
- URL: http://localhost:8080/alfresco
- Default credentials: admin/admin

### 4. Setup Ollama (for local LLM)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull Qwen model
ollama pull qwen2.5:0.5b

# Verify
ollama list
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Start Django Server

```bash
python manage.py runserver
```

## API Endpoints

### 1. Health Check

**GET** `/api/alfresco/health`

Check Alfresco connection status.

**Response:**
```json
{
  "status": "success",
  "alfresco": {
    "status": "healthy",
    "method": "python-alfresco-api",
    "message": "Successfully connected to Alfresco"
  }
}
```

### 2. Sync Contracts from Alfresco

**POST** `/api/alfresco/sync`

Fetch documents from Alfresco, ingest into vector DB, and extract intelligence.

**Request Body:**
```json
{
  "folder_id": "-root-",           // Alfresco folder ID (optional)
  "extract_intelligence": true,     // Extract legal intelligence (default: true)
  "use_openai": false              // Use OpenAI GPT-4 (default: false, uses Ollama)
}
```

**Response:**
```json
{
  "status": "completed",
  "message": "Sync completed. 5 successful, 0 failed",
  "synced_count": 5,
  "failed_count": 0,
  "total_count": 5,
  "results": [
    {
      "name": "contract_001.pdf",
      "contract_id": "uuid-here",
      "alfresco_id": "alfresco-node-id",
      "status": "success",
      "chunks_created": 15,
      "intelligence_extracted": true,
      "intelligence": {
        "parties": "Acme Corp, Widget Inc",
        "jurisdiction": "State of Delaware",
        "termination": "30 days written notice"
      }
    }
  ]
}
```

### 3. RAG-Based Contract Query

**GET** `/api/alfresco/query?q=<query>&use_openai=false&k=5`

Perform semantic search and Q&A across all contracts.

**Query Parameters:**
- `q`: Natural language query (required)
- `use_openai`: Use OpenAI GPT-4 (default: false)
- `k`: Number of results (default: 5)

**Example:**
```
GET /api/alfresco/query?q=What are the termination clauses in my contracts?
```

**Response:**
```json
{
  "status": "success",
  "query": "What are the termination clauses in my contracts?",
  "answer": "Based on the contracts in your portfolio, termination clauses vary: Contract A allows termination with 30 days notice, Contract B requires 60 days notice, and Contract C permits immediate termination for cause.",
  "relevant_chunks": [
    {
      "text": "Either party may terminate this agreement by providing thirty (30) days written notice...",
      "contract_id": "uuid-1",
      "chunk_index": 5,
      "relevance_score": 0.92
    }
  ],
  "total_results": 3
}
```

### 4. Get Contract Intelligence

**GET** `/api/alfresco/contracts/{contract_id}/intelligence`

Retrieve extracted legal intelligence for a specific contract.

**Response:**
```json
{
  "status": "success",
  "contract_id": "uuid-here",
  "contract_name": "contract_001.pdf",
  "intelligence": {
    "parties": "Acme Corp, Widget Inc",
    "termination_summary": "Either party may terminate with 30 days written notice",
    "termination_notice_period": "30 days",
    "liability_summary": "Liability capped at total fees paid in preceding 12 months",
    "jurisdiction": "State of Delaware, USA",
    "confidentiality_duration": "5 years from contract termination",
    "extraction_confidence": 0.85,
    "extracted_at": "2025-01-15T10:30:00Z",
    "raw_data": { /* Full JSON extraction */ }
  }
}
```

### 5. Extract Contract Intelligence

**POST** `/api/alfresco/contracts/{contract_id}/extract`

Manually trigger intelligence extraction for a specific contract.

**Request Body:**
```json
{
  "use_openai": false  // Optional, default: false
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Intelligence extracted successfully",
  "contract_id": "uuid-here",
  "intelligence": {
    "parties": "Acme Corp, Widget Inc",
    "termination_summary": "30 days written notice",
    "jurisdiction": "Delaware",
    "liability_summary": "Capped at 12 months fees"
  }
}
```

## Usage Examples

### Example 1: Sync All Contracts from Alfresco

```bash
curl -X POST http://localhost:8000/api/alfresco/sync \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_id": "-root-",
    "extract_intelligence": true,
    "use_openai": false
  }'
```

### Example 2: Search Contracts

```bash
curl -X GET "http://localhost:8000/api/alfresco/query?q=What+are+the+payment+terms&k=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Example 3: Get Intelligence for Contract

```bash
curl -X GET http://localhost:8000/api/alfresco/contracts/{contract_id}/intelligence \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Database Models

### 1. AlfrescoDocument
Stores metadata for documents synced from Alfresco.

**Fields:**
- `alfresco_node_id`: Unique Alfresco node ID
- `alfresco_folder_id`: Parent folder ID
- `alfresco_name`: Original filename
- `alfresco_content_type`: MIME type
- `alfresco_properties`: JSON metadata
- `contract`: Link to Contract model
- `sync_status`: SYNCED, FAILED, PENDING
- `last_synced_at`: Last sync timestamp

### 2. ContractIntelligence
Stores AI-extracted legal intelligence.

**Fields:**
- `contract`: OneToOne link to Contract
- `parties`: Contracting parties
- `termination_summary`: Termination clause summary
- `termination_notice_period`: Notice period
- `liability_summary`: Liability limitations
- `jurisdiction`: Governing law
- `confidentiality_duration`: Confidentiality term
- `extraction_confidence`: Extraction quality (0-1)
- `vector_db_chunks`: Number of chunks in vector DB
- `raw_extraction_data`: Full JSON extraction

### 3. VectorEmbedding
Tracks document chunks in ChromaDB.

**Fields:**
- `contract`: ForeignKey to Contract
- `embedding_id`: ChromaDB ID
- `chunk_index`: Chunk order
- `chunk_text`: Original text
- `chunk_start_char`: Start position
- `chunk_end_char`: End position
- `embedding_model`: Model used

## Advanced Configuration

### Using Legal-Specific Embeddings

For higher accuracy on legal documents:

```env
CONTRACTS_BERT_MODEL=nlpaueb/legal-bert-base-uncased
```

This model is trained specifically on legal texts but is slower.

### Using OpenAI GPT-4

For best extraction quality (requires API key):

```env
OPENAI_API_KEY=sk-your-api-key
```

Then set `use_openai=true` in API calls.

### Custom Extraction Prompts

Edit `api/legal_extraction_prompt.py` to customize:
- `get_extraction_prompt()` - Main extraction
- `get_risk_assessment_prompt()` - Risk analysis
- `get_compliance_check_prompt()` - Compliance checking
- `get_obligation_extraction_prompt()` - Obligation extraction

## Troubleshooting

### Issue: Alfresco connection fails

**Solution:**
- Verify Alfresco is running: `curl http://localhost:8080/alfresco`
- Check credentials in `.env`
- Ensure firewall allows connection

### Issue: ChromaDB errors

**Solution:**
- Ensure `chroma_db/` directory has write permissions
- Delete and recreate: `rm -rf chroma_db/`

### Issue: LLM extraction fails

**Solution:**
- For Ollama: Verify running with `ollama list`
- For OpenAI: Check API key validity
- Check logs: `tail -f server.log`

### Issue: Out of memory

**Solution:**
- Reduce chunk size in `rag_engine.py`:
  ```python
  chunk_size=500,  # Instead of 1000
  chunk_overlap=50  # Instead of 100
  ```

## Performance Optimization

### 1. Batch Processing
Process multiple contracts in parallel:
```python
# In alfresco_rag_views.py
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(process_contract, contracts)
```

### 2. Caching
Cache LLM responses to avoid redundant calls:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def extract_clauses_cached(contract_text):
    return rag.extract_clauses(contract_text)
```

### 3. Incremental Sync
Only sync changed documents:
```python
# Check last_synced_at before re-processing
if alfresco_doc.last_synced_at < alfresco_modified_date:
    # Re-sync
```

## Security Considerations

1. **API Authentication**: All endpoints require JWT authentication
2. **Alfresco Credentials**: Store in environment variables, never in code
3. **OpenAI API Key**: Use environment variables with restricted permissions
4. **Database Access**: Use read-only MySQL user for RAG queries
5. **File Uploads**: Validate file types and scan for malware

## Next Steps

1. **Frontend Integration**: Build Next.js UI to display intelligence
2. **Compliance Checking**: Integrate with ComplianceFramework models
3. **Real-time Sync**: Implement Alfresco webhooks for automatic sync
4. **Multi-tenancy**: Add tenant isolation for SaaS deployment
5. **Analytics Dashboard**: Visualize extracted intelligence trends

## Support

For issues or questions:
- Check logs: `tail -f django_backend/server.log`
- Review Django admin: http://localhost:8000/admin
- Test API: http://localhost:8000/api/alfresco/health

## License

Proprietary - Contract AI MVP System
