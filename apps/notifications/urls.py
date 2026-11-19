from django.urls import path
from apps.notifications.views import (
    NotificationListView,
    NotificationMarkReadView,
    AuditLogListView,
    CustomerDashboardView,
    OfficerDashboardView,
)

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/read/", NotificationMarkReadView.as_view(), name="notification-mark-all-read"),
    path("notifications/<int:pk>/read/", NotificationMarkReadView.as_view(), name="notification-mark-read"),
    path("audit-logs/", AuditLogListView.as_view(), name="audit-log-list"),
    path("dashboard/customer/", CustomerDashboardView.as_view(), name="dashboard-customer"),
    path("dashboard/officer/", OfficerDashboardView.as_view(), name="dashboard-officer"),
]
