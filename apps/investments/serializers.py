from decimal import Decimal
from rest_framework import serializers
from apps.investments.models import InvestmentProduct, InvestmentOrder, InvestmentHolding


class InvestmentProductSerializer(serializers.ModelSerializer):
    product_type_display = serializers.CharField(source="get_product_type_display", read_only=True)
    risk_level_display = serializers.CharField(source="get_risk_level_display", read_only=True)

    class Meta:
        model = InvestmentProduct
        fields = [
            "id",
            "product_name",
            "product_type",
            "product_type_display",
            "risk_level",
            "risk_level_display",
            "minimum_amount",
            "status",
        ]


class InvestmentHoldingSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="investment_product.product_name", read_only=True)
    product_type = serializers.CharField(source="investment_product.product_type", read_only=True)
    risk_level = serializers.CharField(source="investment_product.risk_level", read_only=True)

    class Meta:
        model = InvestmentHolding
        fields = [
            "id",
            "investment_product",
            "product_name",
            "product_type",
            "risk_level",
            "units",
            "invested_amount",
        ]


class InvestmentOrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="investment_product.product_name", read_only=True)
    reference_number = serializers.CharField(source="transaction.reference_number", read_only=True, default=None)

    class Meta:
        model = InvestmentOrder
        fields = [
            "id",
            "customer",
            "investment_product",
            "product_name",
            "transaction",
            "reference_number",
            "amount",
            "order_status",
            "created_at",
        ]
        read_only_fields = ["id", "customer", "transaction", "order_status", "created_at"]


class InvestmentOrderCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    account_id = serializers.IntegerField(required=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True, min_value=Decimal("100.00"))
