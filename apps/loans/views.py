from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.loans.models import LoanProduct, LoanApplication, LoanRepayment
from apps.loans.serializers import (
    LoanProductSerializer,
    LoanApplicationSerializer,
    LoanApplicationCreateSerializer,
    LoanReviewSerializer,
    LoanRepaymentSerializer,
)
from apps.loans.services import LoanService
from apps.accounts.permissions import IsBankOfficer
from apps.notifications.models import Notification, AuditLog


class LoanProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = LoanProduct.objects.all()
        serializer = LoanProductSerializer(products, many=True)
        return Response({"status": "success", "data": serializer.data})


class LoanApplicationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff:
            applications = LoanApplication.objects.all().select_related("customer", "loan_product", "reviewed_by").prefetch_related("repayments")
            # Optional status filter
            st = request.query_params.get("status")
            if st:
                applications = applications.filter(application_status=st.upper())
        else:
            if not hasattr(user, "customer_profile"):
                return Response({"status": "success", "data": []})
            applications = LoanApplication.objects.filter(
                customer=user.customer_profile
            ).select_related("customer", "loan_product", "reviewed_by").prefetch_related("repayments")

        serializer = LoanApplicationSerializer(applications, many=True)
        return Response({"status": "success", "data": serializer.data})

    def post(self, request):
        if not hasattr(request.user, "customer_profile"):
            return Response(
                {"status": "error", "message": "Only registered customers can apply for loans."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = LoanApplicationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        application = LoanApplication.objects.create(
            customer=request.user.customer_profile,
            loan_product=data["product"],
            requested_amount=data["requested_amount"],
            duration_months=data["duration_months"],
            application_status=LoanApplication.ApplicationStatus.PENDING_REVIEW,
        )

        Notification.objects.create(
            user=request.user,
            title="Loan Application Submitted",
            message=(
                "Your loan application has been submitted successfully. "
                "Our Bank Officer will review your application and verify the submitted information. "
                "You can track your application status from your dashboard."
            ),
            notification_type=Notification.NotificationType.LOAN,
        )
        AuditLog.objects.create(
            actor=request.user,
            action="LOAN_APPLICATION_SUBMITTED",
            entity_type="LOAN_APPLICATION",
            entity_id=application.id,
        )

        return Response(
            {
                "status": "success",
                "message": (
                    "Your loan application has been submitted successfully. "
                    "Our Bank Officer will review your application and verify the submitted information. "
                    "You can track your application status from your dashboard."
                ),
                "data": LoanApplicationSerializer(application).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoanApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        try:
            if getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff:
                app = LoanApplication.objects.select_related("customer", "loan_product", "reviewed_by").prefetch_related("repayments").get(pk=pk)
            else:
                app = LoanApplication.objects.select_related("customer", "loan_product", "reviewed_by").prefetch_related("repayments").get(
                    pk=pk, customer=user.customer_profile
                )
        except LoanApplication.DoesNotExist:
            return Response({"status": "error", "message": "Loan application not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = LoanApplicationSerializer(app)
        return Response({"status": "success", "data": serializer.data})


class LoanReviewView(APIView):
    permission_classes = [IsAuthenticated, IsBankOfficer]

    def post(self, request, pk):
        serializer = LoanReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        action = serializer.validated_data["action"]
        try:
            app = LoanService.review_loan(
                officer_user=request.user,
                loan_application_id=pk,
                action=action,
                rejection_reason=serializer.validated_data.get("rejection_reason", ""),
                officer_remarks=serializer.validated_data.get("officer_remarks", "") or serializer.validated_data.get("notes", ""),
                verification_instructions=serializer.validated_data.get("verification_instructions", ""),
                visit_location=serializer.validated_data.get("visit_location", ""),
                appointment_date=serializer.validated_data.get("appointment_date"),
            )
            return Response(
                {
                    "status": "success",
                    "message": f"Loan application #{pk} has been updated to {app.application_status}.",
                    "data": LoanApplicationSerializer(app).data,
                }
            )
        except ValidationError as e:
            return Response({"status": "error", "message": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)


class LoanRepaymentPayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        account_id = request.data.get("account_id")
        if not account_id:
            return Response({"status": "error", "message": "account_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            repayment = LoanService.pay_repayment(user=request.user, repayment_id=pk, account_id=account_id)
            return Response(
                {
                    "status": "success",
                    "message": f"Installment #{repayment.installment_number} paid successfully.",
                    "data": LoanRepaymentSerializer(repayment).data,
                }
            )
        except ValidationError as e:
            return Response({"status": "error", "message": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
