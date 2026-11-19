from decimal import Decimal
from rest_framework import serializers
from apps.bill_payments.models import Biller, BillPayment


class BillerSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Biller
        fields = ["id", "name", "category", "category_display", "status"]


class BillPaymentSerializer(serializers.ModelSerializer):
    biller_name = serializers.CharField(source="biller.name", read_only=True)
    biller_category = serializers.CharField(source="biller.category", read_only=True)
    account_number = serializers.CharField(source="account.account_number", read_only=True)
    amount = serializers.DecimalField(source="transaction.amount", max_digits=15, decimal_places=2, read_only=True)
    reference_number = serializers.CharField(source="transaction.reference_number", read_only=True)
    created_at = serializers.DateTimeField(source="transaction.created_at", read_only=True)

    class Meta:
        model = BillPayment
        fields = [
            "id",
            "transaction",
            "reference_number",
            "account",
            "account_number",
            "biller",
            "biller_name",
            "biller_category",
            "consumer_reference",
            "due_date",
            "amount",
            "created_at",
        ]


class BillPaymentCreateSerializer(serializers.Serializer):
    account_id = serializers.IntegerField(required=True)
    biller_id = serializers.IntegerField(required=True)
    consumer_reference = serializers.CharField(max_length=100, required=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True, min_value=Decimal("1.00"))
    due_date = serializers.DateField(required=False, allow_null=True, default=None)
