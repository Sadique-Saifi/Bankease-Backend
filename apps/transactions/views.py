from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from apps.transactions.models import FinancialTransaction
from apps.transactions.serializers import (
    FinancialTransactionSerializer,
    FundTransferRequestSerializer,
)
from apps.transactions.services import TransferService


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class TransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff:
            txns = FinancialTransaction.objects.all().select_related("initiated_by", "fund_transfer").prefetch_related("ledger_entries__account")
        else:
            txns = FinancialTransaction.objects.filter(
                Q(initiated_by=user) | Q(ledger_entries__account__holders__user=user)
            ).distinct().select_related("initiated_by", "fund_transfer").prefetch_related("ledger_entries__account")

        # Filters
        txn_type = request.query_params.get("type")
        if txn_type:
            txns = txns.filter(transaction_type=txn_type)

        txn_status = request.query_params.get("status")
        if txn_status:
            txns = txns.filter(transaction_status=txn_status)

        account_id = request.query_params.get("account_id")
        if account_id:
            txns = txns.filter(ledger_entries__account_id=account_id)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(txns, request)
        serializer = FinancialTransactionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class TransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        try:
            if getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff:
                txn = FinancialTransaction.objects.get(pk=pk)
            else:
                txn = FinancialTransaction.objects.filter(
                    Q(initiated_by=user) | Q(ledger_entries__account__holders__user=user)
                ).distinct().get(pk=pk)
        except FinancialTransaction.DoesNotExist:
            return Response(
                {"status": "error", "message": "Transaction not found or access unauthorized."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = FinancialTransactionSerializer(txn)
        return Response({"status": "success", "data": serializer.data})


class FundTransferCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FundTransferRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            txn, transfer = TransferService.execute_transfer(
                user=request.user,
                source_account_id=data["source_account_id"],
                amount=data["amount"],
                destination_account_number=data.get("destination_account_number"),
                beneficiary_id=data.get("beneficiary_id"),
                remarks=data.get("remarks", ""),
            )
            return Response(
                {
                    "status": "success",
                    "message": "Fund transfer processed successfully.",
                    "data": FinancialTransactionSerializer(txn).data,
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
                {"status": "error", "message": f"Transfer processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
