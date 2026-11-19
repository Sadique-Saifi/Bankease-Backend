from django.urls import path
from apps.bill_payments.views import BillerListView, BillPaymentListCreateView

urlpatterns = [
    path("billers/", BillerListView.as_view(), name="biller-list"),
    path("bill-payments/", BillPaymentListCreateView.as_view(), name="bill-payment-list-create"),
]
