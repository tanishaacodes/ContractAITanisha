# Bid Actions Backend Setup Instructions

## Step 1: Update Django Settings

Add the new app to `INSTALLED_APPS` in your settings.py:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'apps.bid_actions',
]
```

## Step 2: Update Main URLs

In `backend/backend/urls.py`, add:

```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    path('api/bid-actions/', include('apps.bid_actions.urls')),
]
```

## Step 3: Run Migrations

```bash
cd backend
python manage.py makemigrations bid_actions
python manage.py migrate
```

## Step 4: Seed Departments

```bash
python manage.py seed_departments
```

## Step 5: Test API Endpoints

The following endpoints are now available:

### Departments
- `GET /api/bid-actions/departments/` - List departments
- `GET /api/bid-actions/departments/keywords/` - Get classification keywords

### Action Items
- `GET /api/bid-actions/actions/` - List all actions
- `POST /api/bid-actions/actions/` - Create action
- `GET /api/bid-actions/actions/{id}/` - Get action detail
- `PATCH /api/bid-actions/actions/{id}/update_status/` - Update status
- `POST /api/bid-actions/actions/bulk_update_status/` - Bulk status update
- `GET /api/bid-actions/actions/{id}/delay_prediction/` - Get delay prediction

### Tender Actions
- `GET /api/bid-actions/tenders/{tender_id}/actions/` - Get tender actions
- `POST /api/bid-actions/tenders/{tender_id}/generate-actions/` - Generate actions
- `POST /api/bid-actions/tenders/{tender_id}/regenerate-actions/` - Regenerate
- `GET /api/bid-actions/tenders/{tender_id}/dashboard/` - Dashboard data
- `GET /api/bid-actions/tenders/{tender_id}/risk-propagation/` - Risk propagation
- `GET /api/bid-actions/tenders/{tender_id}/dependency-graph/` - Graph data
- `GET /api/bid-actions/tenders/{tender_id}/critical-path/` - Critical path

### Portfolio
- `GET /api/bid-actions/portfolio/dashboard/` - Portfolio dashboard
- `GET /api/bid-actions/portfolio/department_heatmap/` - Department heatmap

## Step 6: Test with cURL

```bash
# Generate actions for a tender
curl -X POST http://localhost:8002/api/bid-actions/tenders/{TENDER_ID}/generate-actions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get dashboard data
curl http://localhost:8002/api/bid-actions/tenders/{TENDER_ID}/dashboard/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get dependency graph
curl http://localhost:8002/api/bid-actions/tenders/{TENDER_ID}/dependency-graph/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## API Response Examples

### Dashboard Response
```json
{
  "tender_id": "uuid",
  "tender_title": "Metro Project",
  "readiness": {
    "readiness_index": 45.5,
    "data_readiness": 60.0,
    "action_completion": 25.0,
    "readiness_steps": [...]
  },
  "department_summaries": [
    {
      "department_name": "Civil",
      "total_actions": 15,
      "completed_actions": 5,
      "avg_risk_score": 0.65
    }
  ],
  "total_actions": 50,
  "completed_actions": 12
}
```

### Dependency Graph Response
```json
{
  "nodes": [
    {
      "id": "uuid",
      "label": "BOQ: Foundation Work",
      "department": "Civil",
      "risk_score": 0.7,
      "status": "In Progress"
    }
  ],
  "edges": [
    {
      "from": "uuid1",
      "to": "uuid2",
      "type": "dependency"
    }
  ]
}
```

## Next Steps

1. Run migrations and seed departments
2. Test API endpoints
3. Integrate frontend components
4. Setup auto-generation on tender upload
