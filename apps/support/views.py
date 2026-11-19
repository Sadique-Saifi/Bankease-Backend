from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.support.models import SupportTicket, SupportMessage
from apps.support.serializers import (
    SupportTicketSerializer,
    SupportTicketCreateSerializer,
    SupportMessageSerializer,
    SupportMessageCreateSerializer,
    SupportTicketUpdateSerializer,
)
from apps.notifications.models import Notification, AuditLog
from apps.accounts.permissions import IsBankOfficer


class SupportTicketListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff:
            tickets = SupportTicket.objects.all().select_related("customer", "assigned_officer").prefetch_related("messages__sender")
            status_param = request.query_params.get("status")
            if status_param:
                tickets = tickets.filter(ticket_status=status_param.upper())
        else:
            if not hasattr(user, "customer_profile"):
                return Response({"status": "success", "data": []})
            tickets = SupportTicket.objects.filter(
                customer=user.customer_profile
            ).select_related("customer", "assigned_officer").prefetch_related("messages__sender")

        serializer = SupportTicketSerializer(tickets, many=True)
        return Response({"status": "success", "data": serializer.data})

    def post(self, request):
        if not hasattr(request.user, "customer_profile"):
            return Response(
                {"status": "error", "message": "Only registered customers can create support tickets."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SupportTicketCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        ticket = SupportTicket.objects.create(
            customer=request.user.customer_profile,
            subject=data["subject"],
            description=data["description"],
            priority=data["priority"],
            ticket_status=SupportTicket.TicketStatus.OPEN,
        )

        # Initial message
        SupportMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=data["description"],
        )

        AuditLog.objects.create(
            actor=request.user,
            action="SUPPORT_TICKET_CREATED",
            entity_type="SUPPORT_TICKET",
            entity_id=ticket.id,
        )

        return Response(
            {
                "status": "success",
                "message": "Support ticket created successfully.",
                "data": SupportTicketSerializer(ticket).data,
            },
            status=status.HTTP_201_CREATED,
        )


class SupportTicketDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        try:
            if getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff:
                ticket = SupportTicket.objects.select_related("customer", "assigned_officer").prefetch_related("messages__sender").get(pk=pk)
            else:
                ticket = SupportTicket.objects.select_related("customer", "assigned_officer").prefetch_related("messages__sender").get(
                    pk=pk, customer=user.customer_profile
                )
        except SupportTicket.DoesNotExist:
            return Response({"status": "error", "message": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SupportTicketSerializer(ticket)
        return Response({"status": "success", "data": serializer.data})

    def patch(self, request, pk):
        user = request.user
        if not (getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff):
            return Response({"status": "error", "message": "Only bank officers can update ticket status."}, status=status.HTTP_403_FORBIDDEN)

        try:
            ticket = SupportTicket.objects.get(pk=pk)
        except SupportTicket.DoesNotExist:
            return Response({"status": "error", "message": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SupportTicketUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        if "ticket_status" in data:
            ticket.ticket_status = data["ticket_status"]
        if "assigned_officer_id" in data:
            ticket.assigned_officer_id = data["assigned_officer_id"]
        ticket.save()

        # Notify customer of update
        Notification.objects.create(
            user=ticket.customer.user,
            title="Support Ticket Updated",
            message=f"Your ticket #{ticket.id} ('{ticket.subject}') status is now {ticket.get_ticket_status_display()}.",
            notification_type=Notification.NotificationType.SUPPORT,
        )

        return Response({"status": "success", "message": "Ticket updated.", "data": SupportTicketSerializer(ticket).data})


class SupportMessageCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        try:
            if getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff:
                ticket = SupportTicket.objects.get(pk=pk)
            else:
                ticket = SupportTicket.objects.get(pk=pk, customer=user.customer_profile)
        except SupportTicket.DoesNotExist:
            return Response({"status": "error", "message": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SupportMessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        msg = SupportMessage.objects.create(
            ticket=ticket,
            sender=user,
            message=serializer.validated_data["message"],
        )

        # Notify other party
        if user == ticket.customer.user and ticket.assigned_officer:
            Notification.objects.create(
                user=ticket.assigned_officer,
                title="New Customer Message",
                message=f"New response on Ticket #{ticket.id} from {ticket.customer.full_name}.",
                notification_type=Notification.NotificationType.SUPPORT,
            )
        elif user != ticket.customer.user:
            Notification.objects.create(
                user=ticket.customer.user,
                title="Support Response Received",
                message=f"An officer has replied to your Ticket #{ticket.id}.",
                notification_type=Notification.NotificationType.SUPPORT,
            )

        return Response(
            {"status": "success", "message": "Message sent.", "data": SupportMessageSerializer(msg).data},
            status=status.HTTP_201_CREATED,
        )
