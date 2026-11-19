from rest_framework import serializers
from apps.loans.models import LoanProduct, LoanApplication, LoanRepayment


class LoanProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanProduct
        fields = [
            "id",
            "product_name",
            "interest_rate",
            "minimum_amount",
            "maximum_amount",
            "duration_months",
        ]


class LoanRepaymentSerializer(serializers.ModelSerializer):
    transaction_ref = serializers.CharField(source="transaction.reference_number", read_only=True, default=None)

    class Meta:
        model = LoanRepayment
        fields = [
            "id",
            "loan_application",
            "installment_number",
            "amount",
            "due_date",
            "payment_status",
            "transaction",
            "transaction_ref",
        ]
        read_only_fields = ["id", "installment_number", "amount", "due_date", "payment_status"]


class LoanApplicationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="loan_product.product_name", read_only=True)
    interest_rate = serializers.DecimalField(source="loan_product.interest_rate", max_digits=5, decimal_places=2, read_only=True)
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    customer_number = serializers.CharField(source="customer.customer_number", read_only=True)
    repayments = LoanRepaymentSerializer(many=True, read_only=True)

    class Meta:
        model = LoanApplication
        fields = [
            "id",
            "customer",
            "customer_name",
            "customer_number",
            "loan_product",
            "product_name",
            "interest_rate",
            "requested_amount",
            "duration_months",
            "application_status",
            "reviewed_by",
            "submitted_at",
            "repayments",
        ]
        read_only_fields = ["id", "customer", "application_status", "reviewed_by", "submitted_at", "repayments"]


class LoanApplicationCreateSerializer(serializers.Serializer):
    loan_product_id = serializers.IntegerField(required=True)
    requested_amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    duration_months = serializers.IntegerField(required=True, min_value=1, max_value=360)

    def validate(self, attrs):
        try:
            product = LoanProduct.objects.get(id=attrs["loan_product_id"])
        except LoanProduct.DoesNotExist:
            raise serializers.ValidationError({"loan_product_id": "Invalid loan product."})

        amt = attrs["requested_amount"]
        if amt < product.minimum_amount or amt > product.maximum_amount:
            raise serializers.ValidationError({
                "requested_amount": f"Amount must be between ₹{product.minimum_amount:,.2f} and ₹{product.maximum_amount:,.2f}."
            })
        attrs["product"] = product
        return attrs


class LoanReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["APPROVE", "REJECT"], required=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
