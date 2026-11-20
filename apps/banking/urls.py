from django.urls import path
from apps.banking.views import (
    BankAccountListCreateView,
    BankAccountDetailView,
    BeneficiaryListCreateView,
    BeneficiaryDetailView,
    AccountOpeningRequestListView,
    AccountOpeningReviewView,
)

urlpatterns = [
    path("accounts/", BankAccountListCreateView.as_view(), name="bank-account-list"),
    path("accounts/<int:pk>/", BankAccountDetailView.as_view(), name="bank-account-detail"),
    path("beneficiaries/", BeneficiaryListCreateView.as_view(), name="beneficiary-list"),
    path("beneficiaries/<int:pk>/", BeneficiaryDetailView.as_view(), name="beneficiary-detail"),
    path("account-requests/", AccountOpeningRequestListView.as_view(), name="account-request-list"),
    path("account-requests/<int:pk>/review/", AccountOpeningReviewView.as_view(), name="account-request-review"),
]
