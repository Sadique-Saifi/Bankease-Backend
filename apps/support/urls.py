from django.urls import path
from apps.support.views import (
    SupportTicketListCreateView,
    SupportTicketDetailView,
    SupportMessageCreateView,
)

urlpatterns = [
    path("tickets/", SupportTicketListCreateView.as_view(), name="support-ticket-list-create"),
    path("tickets/<int:pk>/", SupportTicketDetailView.as_view(), name="support-ticket-detail"),
    path("tickets/<int:pk>/messages/", SupportMessageCreateView.as_view(), name="support-message-create"),
]
