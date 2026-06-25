from django.urls import path
from .views import ContractTwinView

urlpatterns = [
    path('<str:contract_id>/', ContractTwinView.as_view(), name='contract_twin'),
]
