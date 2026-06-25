from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.EmbeddingGenerateView.as_view(), name='embedding_generate'),
    path('batch/', views.EmbeddingBatchView.as_view(), name='embedding_batch'),
    path('similarity/', views.EmbeddingSimilarityView.as_view(), name='embedding_similarity'),
    path('health/', views.EmbeddingHealthView.as_view(), name='embedding_health'),
]
