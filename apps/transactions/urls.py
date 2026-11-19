from django.urls import path
from apps.transactions.views import (
    TransactionListView,
    TransactionDetailView,
    FundTransferCreateView,
)

urlpatterns = [
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path("transactions/<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
    path("transfers/", FundTransferCreateView.as_view(), name="fund-transfer-create"),
]
