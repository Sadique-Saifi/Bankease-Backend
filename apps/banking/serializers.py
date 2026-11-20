from decimal import Decimal
from rest_framework import serializers
from apps.banking.models import BankAccount, AccountHolder, Beneficiary, AccountOpeningRequest


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


# --- Account Opening Request Serializers ---

class AccountOpeningRequestSerializer(serializers.ModelSerializer):
    """Read serializer for listing account opening requests."""
    requested_by_name = serializers.SerializerMethodField()
    requested_by_username = serializers.CharField(source="requested_by.username", read_only=True)
    customer_number = serializers.SerializerMethodField()
    account_type_display = serializers.CharField(source="get_account_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()
    created_account_number = serializers.CharField(
        source="created_account.account_number", read_only=True, default=None
    )

    class Meta:
        model = AccountOpeningRequest
        fields = [
            "id",
            "requested_by",
            "requested_by_name",
            "requested_by_username",
            "customer_number",
            "account_type",
            "account_type_display",
            "initial_deposit",
            "status",
            "status_display",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "rejection_reason",
            "officer_remarks",
            "created_account",
            "created_account_number",
            "created_at",
        ]
        read_only_fields = fields

    def get_requested_by_name(self, obj):
        if hasattr(obj.requested_by, "customer_profile"):
            return obj.requested_by.customer_profile.full_name
        return obj.requested_by.get_full_name() or obj.requested_by.username

    def get_customer_number(self, obj):
        if hasattr(obj.requested_by, "customer_profile"):
            return obj.requested_by.customer_profile.customer_number
        return None

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name() or obj.reviewed_by.username
        return None


class AccountOpeningRequestCreateSerializer(serializers.Serializer):
    """Create serializer for submitting an account opening request."""
    account_type = serializers.ChoiceField(
        choices=BankAccount.AccountType.choices,
        default=BankAccount.AccountType.SAVINGS,
    )
    initial_deposit = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, default=Decimal("1000.00")
    )

    def validate_initial_deposit(self, value):
        if value < Decimal("500.00"):
            raise serializers.ValidationError("Minimum initial deposit is ₹500.00.")
        return value


class AccountOpeningReviewSerializer(serializers.Serializer):
    """Serializer for officer to review (approve/reject) account opening request."""
    action = serializers.ChoiceField(choices=["APPROVE", "REJECT"], required=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True, default="")
    officer_remarks = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs["action"] == "REJECT" and not attrs.get("rejection_reason", "").strip():
            raise serializers.ValidationError(
                {"rejection_reason": "A rejection reason is required when rejecting a request."}
            )
        return attrs
