"""
URL configuration for contractai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.health_views import health_check, readiness_check, liveness_check, startup_check

urlpatterns = [
    # Health check endpoints (no auth required)
    path('health/', health_check, name='health'),
    path('health/ready/', readiness_check, name='readiness'),
    path('health/live/', liveness_check, name='liveness'),
    path('health/startup/', startup_check, name='startup'),

    # Application endpoints
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/admin/', include('admin_app.urls')),
    path('api/superadmin/', include('superadmin_app.urls')),  # NEW: SuperAdmin user management
    path('api/integrations/', include('integrations.urls')),  # NEW: Fivetran & Kafka connectors
    path('api/counterfactual/', include('counterfactual.urls')),
    path('api/drift/', include('drift.urls')),
    path('api/risk/', include('risk.urls')),
    path('api/negotiation/', include('negotiation.urls')),  # NEW: Negotiation intelligence features
    path('api/sap/', include('integrations.sap.urls', namespace='sap')),  # SAP S/4HANA integration
    path('api/infor/', include('integrations.infor.urls', namespace='infor')),  # Infor ERP integration
    path('api/v1/', include('integrations.v1.urls', namespace='v1')),  # Unified multi-ERP API v1
    path('api/market/', include('market.urls')),                      # Market Feed Engine
    path('api/contract-twin/', include('contract_twin.urls')),        # Contract Twin Engine
    path('api/strategic-radar/', include('radar.urls')),              # Strategic Intelligence Radar
    path('api/llm/', include('llm_engine.urls')),                    # LLM Engine (Qwen2.5)
    path('api/embeddings/', include('embeddings.urls')),             # Embeddings Engine
    path('api/risk-engine/', include('risk_engine.urls')),           # Risk Scoring Engine
    path('api/ingestion/', include('ingestion.urls')),               # Contract Ingestion Pipeline
    path('api/autorag/', include('autorag.urls')),                   # AutoRAG Graph+Vector Q&A
    path('api/tenders/', include('tenders.urls')),                   # Tender Intelligence Engine
    path('api/enterprise/', include('enterprise.urls')),             # Enterprise Risk Intelligence (CFO Analytics)
    path('api/prime/', include('prime.urls')),                       # PrimeContractAI Executive Dashboard
    path('api/dispute-predictor/', include('dispute_predictor.urls')),  # Dispute Predictor & Simulator
    path('api/ai-chat/', include('ai_chat.urls')),                   # AI Chat Assistant (Qwen2.5 + RAG)
    path('api/force-majeure/', include('force_majeure.urls')),      # Force Majeure Intelligence Engine
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
