import random
import string
from decimal import Decimal
from django.db import transaction
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User, CustomerProfile
from apps.accounts.services import generate_customer_number
from apps.banking.models import BankAccount, AccountHolder
from apps.notifications.models import Notification, AuditLog


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = [
            "id",
            "customer_number",
            "full_name",
            "phone_number",
            "address",
            "created_at",
        ]
        read_only_fields = ["id", "customer_number", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    customer_profile = CustomerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "is_active",
            "is_staff",
            "date_joined",
            "customer_profile",
        ]
        read_only_fields = ["id", "role", "is_active", "is_staff", "date_joined"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(max_length=150, required=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    initial_deposit = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, default=Decimal("10000.00")
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "full_name",
            "phone_number",
            "address",
            "initial_deposit",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        full_name = validated_data.pop("full_name")
        phone_number = validated_data.pop("phone_number", "")
        address = validated_data.pop("address", "")
        initial_deposit = validated_data.pop("initial_deposit", Decimal("10000.00"))
        password = validated_data.pop("password")

        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data["username"],
                email=validated_data["email"],
                password=password,
                role=User.Role.CUSTOMER,
            )

            profile = CustomerProfile.objects.create(
                user=user,
                customer_number=generate_customer_number(),
                full_name=full_name,
                phone_number=phone_number,
                address=address,
            )

            # Generate unique 12-digit account number
            while True:
                acc_num = f"60{''.join(random.choices(string.digits, k=10))}"
                if not BankAccount.objects.filter(account_number=acc_num).exists():
                    break

            account = BankAccount.objects.create(
                account_number=acc_num,
                account_type=BankAccount.AccountType.SAVINGS,
                balance=initial_deposit,
                currency="INR",
                account_status=BankAccount.AccountStatus.ACTIVE,
            )

            AccountHolder.objects.create(
                account=account,
                user=user,
                holder_role=AccountHolder.HolderRole.PRIMARY,
            )

            # Send welcome notification
            Notification.objects.create(
                user=user,
                title="Welcome to BankEase!",
                message=f"Welcome {full_name}! Your primary savings account {acc_num} has been created with an opening balance of ₹{initial_deposit:,.2f}.",
                notification_type=Notification.NotificationType.REGISTRATION,
            )

            # Create audit log
            AuditLog.objects.create(
                actor=user,
                action="USER_REGISTERED",
                entity_type="APP_USER",
                entity_id=user.id,
            )

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            # Check if login via email was attempted
            user_by_email = User.objects.filter(email__iexact=username).first()
            if user_by_email:
                user = authenticate(username=user_by_email.username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("This user account is inactive.")

        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        refresh["username"] = user.username

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_staff": user.is_staff,
                "full_name": user.customer_profile.full_name if hasattr(user, "customer_profile") else user.get_full_name() or user.username,
                "customer_number": user.customer_profile.customer_number if hasattr(user, "customer_profile") else None,
            },
        }


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_new_password"]:
            raise serializers.ValidationError({"confirm_new_password": "New passwords do not match."})
        return attrs
