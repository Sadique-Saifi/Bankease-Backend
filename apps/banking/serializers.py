from decimal import Decimal
from rest_framework import serializers
from apps.banking.models import BankAccount, AccountHolder, Beneficiary


class AccountHolderSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = AccountHolder
        fields = ["id", "user", "username", "full_name", "holder_role"]

    def get_full_name(self, obj):
        if hasattr(obj.user, "customer_profile"):
            return obj.user.customer_profile.full_name
        return obj.user.get_full_name() or obj.user.username


class BankAccountSerializer(serializers.ModelSerializer):
    holders = AccountHolderSerializer(many=True, read_only=True)
    account_type_display = serializers.CharField(source="get_account_type_display", read_only=True)
    account_status_display = serializers.CharField(source="get_account_status_display", read_only=True)

    class Meta:
        model = BankAccount
        fields = [
            "id",
            "account_number",
            "account_type",
            "account_type_display",
            "balance",
            "currency",
            "account_status",
            "account_status_display",
            "opened_at",
            "holders",
        ]
        read_only_fields = ["id", "account_number", "balance", "currency", "opened_at", "holders"]


class BankAccountCreateSerializer(serializers.Serializer):
    account_type = serializers.ChoiceField(
        choices=BankAccount.AccountType.choices,
        default=BankAccount.AccountType.SAVINGS,
    )
    initial_deposit = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, default=Decimal("1000.00")
    )


class BeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiary
        fields = [
            "id",
            "beneficiary_account_number",
            "beneficiary_name",
            "bank_name",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_beneficiary_account_number(self, value):
        user = self.context["request"].user
        # Check if beneficiary already registered for this user
        if Beneficiary.objects.filter(owner_user=user, beneficiary_account_number=value).exists():
            raise serializers.ValidationError("This beneficiary account is already registered.")
        return value
