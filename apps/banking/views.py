from django.db import transaction
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.banking.models import BankAccount, AccountHolder, Beneficiary, AccountOpeningRequest
from apps.banking.serializers import (
    BankAccountSerializer,
    BankAccountCreateSerializer,
    BeneficiarySerializer,
    AccountOpeningRequestSerializer,
    AccountOpeningRequestCreateSerializer,
    AccountOpeningReviewSerializer,
)
from apps.banking.services import create_bank_account_for_user
from apps.notifications.models import Notification, AuditLog
from apps.accounts.permissions import IsBankOfficer, IsCustomer


class BankAccountListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff:
            accounts = BankAccount.objects.all().prefetch_related("holders__user")
        else:
            accounts = BankAccount.objects.filter(holders__user=user).distinct().prefetch_related("holders__user")
        
        serializer = BankAccountSerializer(accounts, many=True)
        return Response({"status": "success", "data": serializer.data})

    def post(self, request):
        """Now creates an AccountOpeningRequest instead of directly creating the account."""
        serializer = AccountOpeningRequestCreateSerializer(data=request.data)
        if serializer.is_valid():
            req_obj = AccountOpeningRequest.objects.create(
                requested_by=request.user,
                account_type=serializer.validated_data["account_type"],
                initial_deposit=serializer.validated_data["initial_deposit"],
                status=AccountOpeningRequest.RequestStatus.PENDING_REVIEW,
            )
            Notification.objects.create(
                user=request.user,
                title="Account Opening Request Submitted",
                message=(
                    "Your account opening request has been submitted successfully. "
                    "Our Bank Officer will verify your details. Please allow up to 24 hours "
                    "for the review process. You can track your application status from your dashboard."
                ),
                notification_type=Notification.NotificationType.SYSTEM,
            )
            AuditLog.objects.create(
                actor=request.user,
                action="ACCOUNT_REQUEST_SUBMITTED",
                entity_type="ACCOUNT_OPENING_REQUEST",
                entity_id=req_obj.id,
            )
            return Response(
                {
                    "status": "success",
                    "message": (
                        "Your account opening request has been submitted successfully. "
                        "Our Bank Officer will verify your details. Please allow up to 24 hours "
                        "for the review process. You can track your application status from your dashboard."
                    ),
                    "data": AccountOpeningRequestSerializer(req_obj).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class BankAccountDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        try:
            if getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff:
                account = BankAccount.objects.get(pk=pk)
            else:
                account = BankAccount.objects.get(pk=pk, holders__user=user)
        except BankAccount.DoesNotExist:
            return Response(
                {"status": "error", "message": "Account not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BankAccountSerializer(account)
        return Response({"status": "success", "data": serializer.data})


class BeneficiaryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        beneficiaries = Beneficiary.objects.filter(owner_user=request.user, status=Beneficiary.Status.ACTIVE)
        serializer = BeneficiarySerializer(beneficiaries, many=True)
        return Response({"status": "success", "data": serializer.data})

    def post(self, request):
        serializer = BeneficiarySerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            beneficiary = serializer.save(owner_user=request.user)
            AuditLog.objects.create(
                actor=request.user,
                action="BENEFICIARY_ADDED",
                entity_type="BENEFICIARY",
                entity_id=beneficiary.id,
            )
            return Response(
                {
                    "status": "success",
                    "message": "Beneficiary registered successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class BeneficiaryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            beneficiary = Beneficiary.objects.get(pk=pk, owner_user=request.user)
            beneficiary.status = Beneficiary.Status.INACTIVE
            beneficiary.save()
            AuditLog.objects.create(
                actor=request.user,
                action="BENEFICIARY_REMOVED",
                entity_type="BENEFICIARY",
                entity_id=beneficiary.id,
            )
            return Response({"status": "success", "message": "Beneficiary deleted successfully."})
        except Beneficiary.DoesNotExist:
            return Response(
                {"status": "error", "message": "Beneficiary not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


# --- Account Opening Request Views ---

class AccountOpeningRequestListView(APIView):
    """Customer: list own requests. Officer: list all requests (optionally filtered by status)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff:
            qs = AccountOpeningRequest.objects.all().select_related(
                "requested_by", "reviewed_by", "created_account"
            )
            st = request.query_params.get("status")
            if st:
                qs = qs.filter(status=st.upper())
        else:
            qs = AccountOpeningRequest.objects.filter(requested_by=user).select_related(
                "requested_by", "reviewed_by", "created_account"
            )
        serializer = AccountOpeningRequestSerializer(qs, many=True)
        return Response({"status": "success", "data": serializer.data})


class AccountOpeningReviewView(APIView):
    """Officer reviews (approves/rejects) an account opening request."""
    permission_classes = [IsAuthenticated, IsBankOfficer]

    def post(self, request, pk):
        with transaction.atomic():
            try:
                req_obj = AccountOpeningRequest.objects.select_for_update().get(pk=pk)
            except AccountOpeningRequest.DoesNotExist:
                return Response(
                    {"status": "error", "message": "Account opening request not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if req_obj.status != AccountOpeningRequest.RequestStatus.PENDING_REVIEW:
                return Response(
                    {"status": "error", "message": f"Cannot review a request with status '{req_obj.status}'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = AccountOpeningReviewSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            action = serializer.validated_data["action"]
            req_obj.reviewed_by = request.user
            req_obj.reviewed_at = timezone.now()
            req_obj.officer_remarks = serializer.validated_data.get("officer_remarks", "")

            if action == "APPROVE":
                # Create the actual bank account using existing logic
                account = create_bank_account_for_user(
                    user=req_obj.requested_by,
                    account_type=req_obj.account_type,
                    initial_deposit=req_obj.initial_deposit,
                )
                req_obj.status = AccountOpeningRequest.RequestStatus.APPROVED
                req_obj.created_account = account
                req_obj.save()

                Notification.objects.create(
                    user=req_obj.requested_by,
                    title="Account Opening Request Approved!",
                    message=(
                        f"Congratulations! Your {req_obj.get_account_type_display()} account opening request "
                        f"has been approved. Your new account number is {account.account_number}. "
                        f"Initial deposit: ₹{req_obj.initial_deposit:,.2f}."
                    ),
                    notification_type=Notification.NotificationType.SYSTEM,
                )
                AuditLog.objects.create(
                    actor=request.user,
                    action="ACCOUNT_REQUEST_APPROVED",
                    entity_type="ACCOUNT_OPENING_REQUEST",
                    entity_id=req_obj.id,
                )

                return Response({
                    "status": "success",
                    "message": f"Account opening request #{pk} has been approved. Account {account.account_number} created.",
                    "data": AccountOpeningRequestSerializer(req_obj).data,
                })
            else:
                req_obj.status = AccountOpeningRequest.RequestStatus.REJECTED
                req_obj.rejection_reason = serializer.validated_data.get("rejection_reason", "")
                req_obj.save()

                Notification.objects.create(
                    user=req_obj.requested_by,
                    title="Account Opening Request Update",
                    message=(
                        f"We regret to inform you that your {req_obj.get_account_type_display()} "
                        f"account opening request has been declined. "
                        f"Reason: {req_obj.rejection_reason}"
                    ),
                    notification_type=Notification.NotificationType.SYSTEM,
                )
                AuditLog.objects.create(
                    actor=request.user,
                    action="ACCOUNT_REQUEST_REJECTED",
                    entity_type="ACCOUNT_OPENING_REQUEST",
                    entity_id=req_obj.id,
                )

                return Response({
                    "status": "success",
                    "message": f"Account opening request #{pk} has been rejected.",
                    "data": AccountOpeningRequestSerializer(req_obj).data,
                })
