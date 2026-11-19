import datetime
from decimal import Decimal
from django.db.models import Sum, Count, Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from apps.notifications.models import Notification, AuditLog
from apps.notifications.serializers import NotificationSerializer, AuditLogSerializer
from apps.accounts.models import User, CustomerProfile
from apps.banking.models import BankAccount
from apps.transactions.models import FinancialTransaction, LedgerEntry
from apps.transactions.serializers import FinancialTransactionSerializer
from apps.loans.models import LoanApplication, LoanRepayment
from apps.investments.models import InvestmentHolding
from apps.support.models import SupportTicket
from apps.accounts.permissions import IsBankOfficer


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread_only = request.query_params.get("unread")
        notifications = Notification.objects.filter(user=request.user)
        if unread_only and unread_only.lower() in ("true", "1"):
            notifications = notifications.filter(is_read=False)

        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        serializer = NotificationSerializer(notifications[:50], many=True)
        return Response({
            "status": "success",
            "unread_count": unread_count,
            "data": serializer.data,
        })


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        if pk:
            try:
                notif = Notification.objects.get(id=pk, user=request.user)
                notif.is_read = True
                notif.save(update_fields=["is_read"])
            except Notification.DoesNotExist:
                return Response({"status": "error", "message": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Mark all as read
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

        return Response({"status": "success", "message": "Notification(s) marked as read."})


class AuditLogListView(APIView):
    permission_classes = [IsAuthenticated, IsBankOfficer]

    def get(self, request):
        logs = AuditLog.objects.all().select_related("actor")
        action = request.query_params.get("action")
        if action:
            logs = logs.filter(action=action)
        entity_type = request.query_params.get("entity_type")
        if entity_type:
            logs = logs.filter(entity_type=entity_type)

        paginator = PageNumberPagination()
        paginator.page_size = 25
        page = paginator.paginate_queryset(logs, request)
        serializer = AuditLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class CustomerDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Accounts
        accounts = BankAccount.objects.filter(holders__user=user, account_status=BankAccount.AccountStatus.ACTIVE)
        total_accounts = accounts.count()
        total_balance = accounts.aggregate(total=Sum("balance"))["total"] or Decimal("0.00")

        # Monthly Debits & Credits
        from django.utils import timezone
        now = timezone.now()
        start_of_month = timezone.datetime(now.year, now.month, 1, tzinfo=now.tzinfo)

        monthly_debits = (
            LedgerEntry.objects.filter(
                account__holders__user=user,
                entry_type=LedgerEntry.EntryType.DEBIT,
                created_at__gte=start_of_month,
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        )

        monthly_credits = (
            LedgerEntry.objects.filter(
                account__holders__user=user,
                entry_type=LedgerEntry.EntryType.CREDIT,
                created_at__gte=start_of_month,
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        )

        # Recent transactions (latest 5)
        recent_txns = FinancialTransaction.objects.filter(
            Q(initiated_by=user) | Q(ledger_entries__account__holders__user=user)
        ).distinct().order_by("-created_at")[:5]

        # Loan Summary
        pending_loans = 0
        active_loans = 0
        next_due_repayment = None
        if hasattr(user, "customer_profile"):
            pending_loans = LoanApplication.objects.filter(
                customer=user.customer_profile, application_status=LoanApplication.ApplicationStatus.PENDING
            ).count()
            active_loans = LoanApplication.objects.filter(
                customer=user.customer_profile, application_status=LoanApplication.ApplicationStatus.APPROVED
            ).count()
            next_due_repayment_obj = (
                LoanRepayment.objects.filter(
                    loan_application__customer=user.customer_profile,
                    payment_status=LoanRepayment.PaymentStatus.PENDING,
                )
                .order_by("due_date")
                .first()
            )
            if next_due_repayment_obj:
                next_due_repayment = {
                    "installment_number": next_due_repayment_obj.installment_number,
                    "amount": next_due_repayment_obj.amount,
                    "due_date": next_due_repayment_obj.due_date,
                }

        # Investment Summary
        total_invested = Decimal("0.00")
        total_holdings = 0
        if hasattr(user, "customer_profile"):
            holdings = InvestmentHolding.objects.filter(customer=user.customer_profile)
            total_holdings = holdings.count()
            total_invested = holdings.aggregate(total=Sum("invested_amount"))["total"] or Decimal("0.00")

        # Unread notifications
        unread_notifs = Notification.objects.filter(user=user, is_read=False).count()

        return Response({
            "status": "success",
            "data": {
                "total_accounts": total_accounts,
                "total_balance": total_balance,
                "monthly_debits": monthly_debits,
                "monthly_credits": monthly_credits,
                "recent_transactions": FinancialTransactionSerializer(recent_txns, many=True).data,
                "loan_summary": {
                    "pending_loans": pending_loans,
                    "active_loans": active_loans,
                    "next_due_repayment": next_due_repayment,
                },
                "investment_summary": {
                    "holdings_count": total_holdings,
                    "total_invested": total_invested,
                },
                "unread_notifications": unread_notifs,
            },
        })


class OfficerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsBankOfficer]

    def get(self, request):
        total_customers = CustomerProfile.objects.count()
        total_accounts = BankAccount.objects.count()
        total_deposits = BankAccount.objects.aggregate(total=Sum("balance"))["total"] or Decimal("0.00")

        pending_loans = LoanApplication.objects.filter(
            application_status=LoanApplication.ApplicationStatus.PENDING
        ).count()

        open_tickets = SupportTicket.objects.filter(
            ticket_status__in=[SupportTicket.TicketStatus.OPEN, SupportTicket.TicketStatus.IN_PROGRESS]
        ).count()

        today = datetime.date.today()
        txns_today = FinancialTransaction.objects.filter(created_at__date=today)
        total_txns_today = txns_today.count()
        volume_today = txns_today.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        recent_audits = AuditLog.objects.all().select_related("actor")[:10]

        return Response({
            "status": "success",
            "data": {
                "total_customers": total_customers,
                "total_accounts": total_accounts,
                "total_deposits": total_deposits,
                "pending_loans": pending_loans,
                "open_tickets": open_tickets,
                "transactions_today_count": total_txns_today,
                "transactions_today_volume": volume_today,
                "recent_audits": AuditLogSerializer(recent_audits, many=True).data,
            },
        })
