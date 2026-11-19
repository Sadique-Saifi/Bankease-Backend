from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.bill_payments.models import Biller, BillPayment
from apps.bill_payments.serializers import (
    BillerSerializer,
    BillPaymentSerializer,
    BillPaymentCreateSerializer,
)
from apps.bill_payments.services import BillPaymentService


class BillerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        category = request.query_params.get("category")
        billers = Biller.objects.filter(status=Biller.Status.ACTIVE)
        if category:
            billers = billers.filter(category=category.upper())
        serializer = BillerSerializer(billers, many=True)
        return Response({"status": "success", "data": serializer.data})


class BillPaymentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff:
            payments = BillPayment.objects.all().select_related("transaction", "account", "biller")
        else:
            payments = BillPayment.objects.filter(
                account__holders__user=user
            ).distinct().select_related("transaction", "account", "biller")

        serializer = BillPaymentSerializer(payments, many=True)
        return Response({"status": "success", "data": serializer.data})

    def post(self, request):
        serializer = BillPaymentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            txn, payment = BillPaymentService.pay_bill(
                user=request.user,
                account_id=data["account_id"],
                biller_id=data["biller_id"],
                consumer_reference=data["consumer_reference"],
                amount=data["amount"],
                due_date=data.get("due_date"),
            )
            return Response(
                {
                    "status": "success",
                    "message": "Bill payment processed successfully.",
                    "data": BillPaymentSerializer(payment).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response(
                {"status": "error", "message": str(e.message if hasattr(e, "message") else e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": f"Bill payment failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
