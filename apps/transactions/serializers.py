from decimal import Decimal
from rest_framework import serializers
from apps.transactions.models import FinancialTransaction, LedgerEntry, FundTransfer


class LedgerEntrySerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(source="account.account_number", read_only=True)

    class Meta:
        model = LedgerEntry
        fields = [
            "id",
            "account",
            "account_number",
            "entry_type",
            "amount",
            "balance_after",
            "created_at",
        ]


class FundTransferSerializer(serializers.ModelSerializer):
    source_account_number = serializers.CharField(source="source_account.account_number", read_only=True)
    destination_account_number = serializers.SerializerMethodField()
    beneficiary_name = serializers.CharField(source="beneficiary.beneficiary_name", read_only=True, default=None)

    class Meta:
        model = FundTransfer
        fields = [
            "id",
            "source_account",
            "source_account_number",
            "destination_account",
            "destination_account_number",
            "beneficiary",
            "beneficiary_name",
            "remarks",
        ]

    def get_destination_account_number(self, obj):
        if obj.destination_account:
            return obj.destination_account.account_number
        if obj.beneficiary:
            return obj.beneficiary.beneficiary_account_number
        return None


class FinancialTransactionSerializer(serializers.ModelSerializer):
    fund_transfer = FundTransferSerializer(read_only=True)
    ledger_entries = LedgerEntrySerializer(many=True, read_only=True)
    initiated_by_name = serializers.CharField(source="initiated_by.username", read_only=True)

    class Meta:
        model = FinancialTransaction
        fields = [
            "id",
            "reference_number",
            "initiated_by",
            "initiated_by_name",
            "transaction_type",
            "amount",
            "currency",
            "transaction_status",
            "created_at",
            "fund_transfer",
            "ledger_entries",
        ]


class FundTransferRequestSerializer(serializers.Serializer):
    source_account_id = serializers.IntegerField(required=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True, min_value=Decimal("1.00"))
    destination_account_number = serializers.CharField(required=False, allow_blank=True, default=None)
    beneficiary_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    remarks = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if not attrs.get("destination_account_number") and not attrs.get("beneficiary_id"):
            raise serializers.ValidationError(
                "You must specify either a destination account number or select a beneficiary."
            )
        return attrs
