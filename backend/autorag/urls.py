from django.urls import path
from .views import AskView, AskEntityView, RiskClausesView, FlagClausesView, GraphDataView

urlpatterns = [
    path("ask/",          AskView.as_view(),         name="autorag-ask"),
    path("ask/entity/",   AskEntityView.as_view(),   name="autorag-ask-entity"),
    path("clauses/risk/", RiskClausesView.as_view(), name="autorag-risk-clauses"),
    path("clauses/flags/",FlagClausesView.as_view(), name="autorag-flag-clauses"),
    path("graph/",        GraphDataView.as_view(),   name="autorag-graph"),
]
