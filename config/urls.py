"""
URL configuration for BankEase project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # API v1 routes
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.banking.urls")),
    path("api/v1/", include("apps.transactions.urls")),
    path("api/v1/", include("apps.bill_payments.urls")),
    path("api/v1/loans/", include("apps.loans.urls")),
    path("api/v1/investments/", include("apps.investments.urls")),
    path("api/v1/support/", include("apps.support.urls")),
    path("api/v1/", include("apps.notifications.urls")),
]
