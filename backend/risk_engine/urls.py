from django.urls import path
from . import views

urlpatterns = [
    path('score/', views.RiskScoreView.as_view(), name='risk_score'),
    path('clause/', views.ClauseRiskView.as_view(), name='clause_risk'),
    path('batch/', views.BatchClauseRiskView.as_view(), name='batch_clause_risk'),
]
