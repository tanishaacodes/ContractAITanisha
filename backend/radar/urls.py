from django.urls import path
from .views import StrategicRadarView, StrategicAlertHistoryView

urlpatterns = [
    path('<str:contract_id>/', StrategicRadarView.as_view(), name='strategic_radar'),
    path('alerts/', StrategicAlertHistoryView.as_view(), name='strategic_alerts'),
]
