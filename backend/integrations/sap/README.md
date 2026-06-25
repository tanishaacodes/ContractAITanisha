# SAP S/4HANA Integration for PrimeContractAI

## 📘 Overview

This module provides bi-directional integration between **PrimeContractAI** and **SAP S/4HANA** for intelligent contract risk assessment and automated decision-making.

### What It Does

- **Reads contracts** from SAP S/4HANA via OData APIs
- **Analyzes risk** using AI-powered risk scoring engine
- **Detects intent** and liability patterns automatically
- **Blocks high-risk contracts** in SAP before execution
- **Generates clause suggestions** for contract improvement
- **Updates SAP** with AI-generated risk scores and recommendations

### Architecture

```
SAP S/4HANA ↔ OAuth2 ↔ PrimeContractAI ↔ Risk Engine
     │                                      │
     └──────── OData APIs ─────────────────┘
```

---

## 🚀 Quick Start

### 1. Configure SAP Credentials

Edit `backend/.env`:

```bash
# SAP System Configuration
SAP_BASE_URL=https://your-sap-system.com/sap/opu/odata/sap
SAP_TOKEN_URL=https://your-sap-system.com/sap/bc/sec/oauth2/token
SAP_CLIENT_ID=your_client_id
SAP_CLIENT_SECRET=your_client_secret
SAP_SYSTEM_ID=S4H_PRD_100
```

### 2. Register SAP URLs

Add to `backend/contractai/urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns
    path('api/sap/', include('integrations.sap.urls', namespace='sap')),
]
```

### 3. Test Connection

```bash
curl -X GET http://localhost:8000/api/sap/health/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🎯 5 Integration Scenarios

### Scenario 1: Process New Contract

**Flow:** SAP → Read → Risk Analysis → Update SAP

```bash
POST /api/sap/contracts/{contract_id}/process/
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/sap/contracts/4600002345/process/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "scenario": 1,
  "contract_id": "4600002345",
  "risk_score": 65,
  "risk_category": "MEDIUM",
  "intent": "HIGH_LIABILITY",
  "status": "REVIEW_REQUIRED",
  "exposure": 5000000,
  "message": "Contract processed with REVIEW_REQUIRED status"
}
```

---

### Scenario 2: Block High-Risk Contract

**Flow:** Read → Risk Analysis → Block in SAP if risk > 80

```bash
POST /api/sap/contracts/{contract_id}/block-if-high-risk/
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/sap/contracts/4600002345/block-if-high-risk/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "scenario": 2,
  "contract_id": "4600002345",
  "blocked": true,
  "risk_score": 85,
  "message": "Contract blocked due to critical risk (score: 85)"
}
```

---

### Scenario 3: Process Amendment

**Flow:** Read Amended Contract → Re-calculate Risk → Update SAP

```bash
POST /api/sap/contracts/{contract_id}/amendment/
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/sap/contracts/4600002345/amendment/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "scenario": 3,
  "contract_id": "4600002345",
  "previous_risk": 45,
  "new_risk_score": 72,
  "risk_delta": 27,
  "risk_increased": true,
  "status": "REVIEW_REQUIRED",
  "message": "Amendment re-evaluation complete"
}
```

---

### Scenario 4: Manual Override

**Flow:** Check Override Flag → Mark as Manually Approved → Log Action

```bash
POST /api/sap/contracts/{contract_id}/override/
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/sap/contracts/4600002345/override/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "scenario": 4,
  "contract_id": "4600002345",
  "override_applied": true,
  "override_user": "JDOE",
  "message": "Manual override processed successfully"
}
```

---

### Scenario 5: AI Clause Suggestions

**Flow:** Analyze Contract → Generate Suggestions → Add as SAP Note

```bash
POST /api/sap/contracts/{contract_id}/suggestions/
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/sap/contracts/4600002345/suggestions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "scenario": 5,
  "contract_id": "4600002345",
  "suggestions_count": 5,
  "suggestions": [
    "⚠️ Add liability cap: Limit indemnity to the contract value",
    "💡 Insert liability limitation clause",
    "⚖️ Add arbitration clause for dispute resolution"
  ],
  "risk_score": 68,
  "message": "Clause suggestions added successfully"
}
```

---

## 🔧 SAP Custom Fields (Z-Fields)

The integration updates these custom fields in SAP:

| Field Name | Type | Description |
|------------|------|-------------|
| `Z_AI_RISK_SCORE` | Integer | Risk score (0-100) |
| `Z_AI_RISK_CATEGORY` | String | LOW / MEDIUM / HIGH / CRITICAL |
| `Z_AI_STATUS` | String | APPROVED / REVIEW_REQUIRED / BLOCKED |
| `Z_AI_INTENT` | String | Contract intent classification |
| `Z_AI_EXPOSURE` | Decimal | Financial exposure amount |
| `Z_AI_VALIDATED_DATE` | Date | Last AI validation timestamp |
| `Z_AI_COMPLIANCE` | String | Compliance status |

### How to Create Z-Fields in SAP

1. Transaction: **SE11** (ABAP Dictionary)
2. Navigate to: **EKKO** (Purchase Contract Header)
3. Add custom fields with prefix `Z_AI_*`
4. Extend OData service to expose these fields

---

## 🧠 Risk Scoring Engine

### Risk Components

| Component | Weight | Description |
|-----------|--------|-------------|
| Contract Value | 25% | Higher value = higher risk |
| Payment Terms | 20% | Extended terms = higher risk |
| Liability Clauses | 20% | Unlimited liability = critical |
| Vendor Credit | 15% | Lower rating = higher risk |
| Duration | 10% | Longer contracts = higher risk |
| Currency | 10% | Foreign currency = FX risk |

### Risk Categories

- **LOW (0-29):** Auto-approve
- **MEDIUM (30-59):** Review required
- **HIGH (60-79):** Escalate to legal
- **CRITICAL (80-100):** Auto-block

---

## 🔐 Security & Authentication

### OAuth2 Flow

1. Client requests token from SAP
2. SAP validates client credentials
3. Token valid for 1 hour (configurable)
4. Auto-refresh before expiration

### CSRF Token

- Required for write operations (PATCH, POST, DELETE)
- Automatically fetched via HEAD request
- Cached for session duration

### ETag Support

- Enables optimistic locking
- Prevents concurrent update conflicts
- Configurable via `SAP_ENABLE_ETAG`

---

## 📊 Monitoring & Logging

### Health Check

```bash
GET /api/sap/health/
```

Returns:
```json
{
  "status": "healthy",
  "sap_system": "S4H_PRD_100",
  "authenticated": true
}
```

### Logs

All operations are logged at:
- **INFO:** Successful operations
- **WARNING:** High-risk actions (blocks, overrides)
- **ERROR:** API failures, authentication issues

---

## 🔄 Batch Processing

Process multiple contracts in one request:

```bash
POST /api/sap/contracts/batch-process/
Content-Type: application/json

{
  "contract_ids": ["4600001", "4600002", "4600003"],
  "scenario": "process"
}
```

Supported scenarios:
- `process` - Scenario 1
- `block` - Scenario 2
- `amendment` - Scenario 3
- `suggestions` - Scenario 5

---

## 🧪 Testing

### Unit Tests

```bash
cd backend
python manage.py test integrations.sap
```

### Integration Tests with SAP Sandbox

```bash
# Set sandbox credentials
export SAP_BASE_URL=https://sandbox.sap.com/sap/opu/odata/sap
export SAP_CLIENT_ID=test_client
export SAP_CLIENT_SECRET=test_secret

# Run integration tests
python test_sap_integration.py
```

---

## 🚨 Error Handling

| Error Code | Meaning | Action |
|------------|---------|--------|
| 401 | Authentication failed | Check credentials |
| 404 | Contract not found | Verify contract ID |
| 502 | SAP API error | Check SAP system status |
| 503 | Service unavailable | Retry with backoff |

---

## 📈 Performance

- **Latency:** < 2 seconds per contract
- **Throughput:** 1000+ contracts/hour
- **Connection pooling:** Enabled
- **Retry strategy:** Exponential backoff (3 attempts)

---

## 🛠️ Troubleshooting

### "Authentication failed"
- Verify `SAP_CLIENT_ID` and `SAP_CLIENT_SECRET`
- Check token URL is correct
- Ensure OAuth client is activated in SAP

### "Contract not found"
- Verify contract ID format (e.g., '4600002345')
- Check user has authorization for contract
- Ensure OData service is active

### "CSRF token missing"
- Set `SAP_ENABLE_CSRF=True` in .env
- Check SAP system allows CSRF token fetch

---

## 📚 Additional Resources

- [SAP OData API Documentation](https://api.sap.com/)
- [SAP BTP Integration Suite](https://help.sap.com/btp)
- [OAuth2 Client Credentials Flow](https://oauth.net/2/grant-types/client-credentials/)

---

## 🤝 Support

For issues or questions:
- **Email:** support@primecontractai.com
- **Documentation:** [Full Integration Guide](../../../COMPLETE_IMPLEMENTATION_REPORT.md)
- **GitHub:** Create an issue in the repository

---

## 📝 License

© 2026 PrimeContractAI. All rights reserved.
