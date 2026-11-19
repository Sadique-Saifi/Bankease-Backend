from django.urls import path
from apps.banking.views import (
    BankAccountListCreateView,
    BankAccountDetailView,
    BeneficiaryListCreateView,
    BeneficiaryDetailView,
)

urlpatterns = [
    path("accounts/", BankAccountListCreateView.as_view(), name="bank-account-list"),
    path("accounts/<int:pk>/", BankAccountDetailView.as_view(), name="bank-account-detail"),
    path("beneficiaries/", BeneficiaryListCreateView.as_view(), name="beneficiary-list"),
    path("beneficiaries/<int:pk>/", BeneficiaryDetailView.as_view(), name="beneficiary-detail"),
]
