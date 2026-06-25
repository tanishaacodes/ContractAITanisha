# Enterprise Risk & Profitability Intelligence Platform

CFO-Grade Analytics for Contract Risk Management

## Features

- **Global Risk Dashboard**: Portfolio-level exposure metrics and VaR analysis
- **Contract Knowledge Graph**: Interactive graph visualization of contract entities and relationships
- **Supply Chain Risk Network**: Multi-tier supplier dependency analysis
- **Geo-Political Risk Map**: World heatmap with country-level risk scoring
- **Commodity Price Forecast**: Geometric Brownian Motion price simulation
- **Monte Carlo VaR Simulation**: 30,000+ iteration Value-at-Risk analysis
- **Margin Sensitivity Analysis**: Tornado chart sensitivity factors
- **Portfolio VaR Aggregation**: Portfolio-level risk metrics and concentration

## Installation

### 1. Run Database Migrations

```bash
cd backend
python manage.py makemigrations enterprise
python manage.py migrate enterprise
```

### 2. Seed Enterprise Data

```bash
python manage.py seed_enterprise_data
```

This will create:
- 6 Suppliers (Tata Steel, China Steel, Russian Metals, etc.)
- 5 Commodities (Steel, Copper, Oil, Aluminum, Gold)
- 6 Geopolitical Risk entries (India, China, Russia, Germany, USA, Brazil)

## API Endpoints

### Dashboard
- `GET /api/enterprise/dashboard/` - Global portfolio dashboard
- `GET /api/enterprise/dashboard/<contract_id>/` - Contract-specific dashboard

### Knowledge Graph
- `GET /api/enterprise/graph/<contract_id>/` - Contract knowledge graph data

### Supply Chain
- `GET /api/enterprise/supply-chain/` - All suppliers network
- `GET /api/enterprise/supply-chain/<contract_id>/` - Contract suppliers

### Geopolitical Risk
- `GET /api/enterprise/geo-risk/` - All countries risk map
- `GET /api/enterprise/geo-risk/<contract_id>/` - Contract geo-risks

### Commodity Forecast
- `GET /api/enterprise/commodity-forecast/?commodity=Steel` - GBM forecast
- `GET /api/enterprise/commodity-forecast/<contract_id>/?commodity=Copper`

### Monte Carlo
- `POST /api/enterprise/monte-carlo/<contract_id>/` - Run VaR simulation
  ```json
  { "iterations": 30000 }
  ```

### Margin Sensitivity
- `GET /api/enterprise/margin-sensitivity/<contract_id>/` - Tornado chart data

### Portfolio VaR
- `GET /api/enterprise/portfolio-var/` - Portfolio aggregation
- `GET /api/enterprise/portfolio/contracts/` - All contracts list

### Exposure Waterfall
- `GET /api/enterprise/exposure-waterfall/<contract_id>/` - Waterfall data

## Models

### Supplier
- Multi-tier classification (Tier 1, 2, 3)
- Risk scoring and classification
- Single-source dependency tracking
- Geopolitical attributes

### Commodity
- Current price and volatility parameters
- GBM drift and sigma for forecasting
- Total contract exposure tracking

### GeoPoliticalRisk
- Country-level risk scoring
- Sanction tracking
- Economic indicators (GDP growth, inflation)
- Geographic coordinates for mapping

### MonteCarloSimulation
- Stored simulation results
- VaR percentiles (90%, 95%, 99%)
- CVaR (Conditional VaR)
- Distribution and convergence data

## Services

### MonteCarloService
Implements Monte Carlo VaR simulation using NumPy:
- Geometric Brownian Motion
- Risk-neutral simulation
- Percentile-based VaR calculation
- Expected Shortfall (CVaR)

### CommodityForecastService
Generates commodity price forecasts:
- Geometric Brownian Motion paths
- Confidence bands
- Scenario analysis
- Risk impact calculation

### KnowledgeGraphService
Builds contract knowledge graphs:
- Suppliers, countries, commodities
- Liabilities and risks
- Sanctions and geopolitical factors
- Cytoscape.js compatible format

## Frontend Integration

Update frontend service calls to use real APIs:

```javascript
// enterpriseRiskService.js

async getDashboardData(contractId) {
  const response = await api.get(`/enterprise/dashboard/${contractId}`);
  return response.data;
}

async runMonteCarloSimulation(contractId, iterations = 30000) {
  const response = await api.post(`/enterprise/monte-carlo/${contractId}`, {
    iterations
  });
  return response.data;
}
```

## Next Steps

1. ✅ Backend API implementation complete
2. ⏳ Link contracts to suppliers (many-to-many relationships)
3. ⏳ Link contracts to commodities
4. ⏳ Run Monte Carlo simulations for existing contracts
5. ⏳ Frontend: Remove mock data, use real APIs
6. ⏳ Integrate with Neo4j for advanced graph queries (optional)

## Admin Interface

All models are registered in Django Admin:
- Navigate to `/admin/enterprise/`
- Manage suppliers, commodities, geopolitical risks
- View Monte Carlo simulation results

## Authentication

All endpoints require authentication. Include JWT token:

```
Authorization: Bearer <your_jwt_token>
```
