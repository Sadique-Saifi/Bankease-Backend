from django.urls import path
from apps.investments.views import (
    InvestmentProductListView,
    InvestmentOrderListCreateView,
    InvestmentHoldingListView,
)

urlpatterns = [
    path("products/", InvestmentProductListView.as_view(), name="investment-product-list"),
    path("orders/", InvestmentOrderListCreateView.as_view(), name="investment-order-list-create"),
    path("holdings/", InvestmentHoldingListView.as_view(), name="investment-holding-list"),
]
