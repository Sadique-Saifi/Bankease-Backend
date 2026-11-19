from rest_framework import serializers
from apps.support.models import SupportTicket, SupportMessage


class SupportMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.username", read_only=True)
    sender_role = serializers.CharField(source="sender.role", read_only=True)

    class Meta:
        model = SupportMessage
        fields = [
            "id",
            "ticket",
            "sender",
            "sender_name",
            "sender_role",
            "message",
            "created_at",
        ]
        read_only_fields = ["id", "ticket", "sender", "created_at"]


class SupportTicketSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    customer_number = serializers.CharField(source="customer.customer_number", read_only=True)
    assigned_officer_name = serializers.CharField(source="assigned_officer.username", read_only=True, default=None)
    messages = SupportMessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "customer",
            "customer_name",
            "customer_number",
            "assigned_officer",
            "assigned_officer_name",
            "subject",
            "description",
            "priority",
            "ticket_status",
            "created_at",
            "messages",
        ]
        read_only_fields = ["id", "customer", "assigned_officer", "created_at", "messages"]


class SupportTicketCreateSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=200, required=True)
    description = serializers.CharField(required=True)
    priority = serializers.ChoiceField(
        choices=SupportTicket.Priority.choices,
        default=SupportTicket.Priority.MEDIUM,
    )


class SupportMessageCreateSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)


class SupportTicketUpdateSerializer(serializers.Serializer):
    ticket_status = serializers.ChoiceField(choices=SupportTicket.TicketStatus.choices, required=False)
    assigned_officer_id = serializers.IntegerField(required=False, allow_null=True)
