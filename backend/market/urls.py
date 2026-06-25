from django.urls import path
from . import views

urlpatterns = [
    path('signals/', views.MarketSignalsView.as_view(), name='market_signals'),
    path('history/', views.MarketSignalHistoryView.as_view(), name='market_signal_history'),
]
