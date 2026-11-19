from django.urls import path
from apps.loans.views import (
    LoanProductListView,
    LoanApplicationListCreateView,
    LoanApplicationDetailView,
    LoanReviewView,
    LoanRepaymentPayView,
)

urlpatterns = [
    path("products/", LoanProductListView.as_view(), name="loan-product-list"),
    path("applications/", LoanApplicationListCreateView.as_view(), name="loan-application-list-create"),
    path("applications/<int:pk>/", LoanApplicationDetailView.as_view(), name="loan-application-detail"),
    path("applications/<int:pk>/review/", LoanReviewView.as_view(), name="loan-review"),
    path("repayments/<int:pk>/pay/", LoanRepaymentPayView.as_view(), name="loan-repayment-pay"),
]
