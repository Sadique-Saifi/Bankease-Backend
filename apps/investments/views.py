from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.investments.models import InvestmentProduct, InvestmentOrder, InvestmentHolding
from apps.investments.serializers import (
    InvestmentProductSerializer,
    InvestmentOrderSerializer,
    InvestmentOrderCreateSerializer,
    InvestmentHoldingSerializer,
)
from apps.investments.services import InvestmentService


class InvestmentProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = InvestmentProduct.objects.filter(status=InvestmentProduct.Status.ACTIVE)
        serializer = InvestmentProductSerializer(products, many=True)
        return Response({"status": "success", "data": serializer.data})


class InvestmentOrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff:
            orders = InvestmentOrder.objects.all().select_related("investment_product", "transaction")
        else:
            if not hasattr(user, "customer_profile"):
                return Response({"status": "success", "data": []})
            orders = InvestmentOrder.objects.filter(
                customer=user.customer_profile
            ).select_related("investment_product", "transaction")

        serializer = InvestmentOrderSerializer(orders, many=True)
        return Response({"status": "success", "data": serializer.data})

    def post(self, request):
        serializer = InvestmentOrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            order = InvestmentService.place_order(
                user=request.user,
                product_id=data["product_id"],
                account_id=data["account_id"],
                amount=data["amount"],
            )
            return Response(
                {
                    "status": "success",
                    "message": "Investment order executed successfully.",
                    "data": InvestmentOrderSerializer(order).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response({"status": "error", "message": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InvestmentHoldingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if getattr(user, "role", None) == "BANK_OFFICER" or user.is_staff:
            holdings = InvestmentHolding.objects.all().select_related("investment_product", "customer")
        else:
            if not hasattr(user, "customer_profile"):
                return Response({"status": "success", "data": []})
            holdings = InvestmentHolding.objects.filter(
                customer=user.customer_profile
            ).select_related("investment_product")

        serializer = InvestmentHoldingSerializer(holdings, many=True)
        return Response({"status": "success", "data": serializer.data})
