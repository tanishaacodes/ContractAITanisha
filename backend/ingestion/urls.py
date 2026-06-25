from django.urls import path
from .views import ContractIngestionView, SchemaSetupView, IngestionStatusView

urlpatterns = [
    path("upload/",  ContractIngestionView.as_view(), name="ingestion-upload"),
    path("schema/",  SchemaSetupView.as_view(),        name="ingestion-schema"),
    path("status/",  IngestionStatusView.as_view(),    name="ingestion-status"),
]
