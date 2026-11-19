from django.contrib import admin
from apps.notifications.models import Notification, AuditLog

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "notification_type", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = ["title", "user__username"]

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "actor", "entity_type", "entity_id", "ip_address", "created_at"]
    list_filter = ["action", "entity_type", "created_at"]
    search_fields = ["action", "actor__username", "entity_type"]
