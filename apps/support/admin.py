from django.contrib import admin
from apps.support.models import SupportTicket, SupportMessage

class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 1

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ["id", "subject", "customer", "priority", "ticket_status", "assigned_officer", "created_at"]
    list_filter = ["priority", "ticket_status", "created_at"]
    search_fields = ["subject", "customer__full_name"]
    inlines = [SupportMessageInline]

@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ["ticket", "sender", "created_at"]
