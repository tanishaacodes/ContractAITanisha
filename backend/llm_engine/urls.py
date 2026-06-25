from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.LLMGenerateView.as_view(), name='llm_generate'),
    path('health/', views.LLMHealthView.as_view(), name='llm_health'),
    path('summarize/', views.LLMSummarizeView.as_view(), name='llm_summarize'),
]
