from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.accounts.serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    UserSerializer,
    CustomerProfileSerializer,
    ChangePasswordSerializer,
)
from apps.notifications.models import Notification, AuditLog


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": "User registered successfully.",
                    "data": UserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            user_id = data["user"]["id"]

            # Log audit
            AuditLog.objects.create(
                actor_id=user_id,
                action="USER_LOGGED_IN",
                entity_type="APP_USER",
                entity_id=user_id,
            )

            return Response(
                {
                    "status": "success",
                    "message": "Login successful.",
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"status": "error", "message": "Invalid credentials", "errors": serializer.errors},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({"status": "success", "data": serializer.data})

    def patch(self, request):
        if not hasattr(request.user, "customer_profile"):
            return Response(
                {"status": "error", "message": "No customer profile found for this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile = request.user.customer_profile
        serializer = CustomerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            AuditLog.objects.create(
                actor=request.user,
                action="PROFILE_UPDATED",
                entity_type="CUSTOMER_PROFILE",
                entity_id=profile.id,
            )
            return Response({"status": "success", "message": "Profile updated.", "data": serializer.data})
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data["old_password"]):
                return Response(
                    {"status": "error", "message": "Incorrect old password."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(serializer.validated_data["new_password"])
            user.save()

            Notification.objects.create(
                user=user,
                title="Password Changed",
                message="Your BankEase account password was successfully updated.",
                notification_type=Notification.NotificationType.LOGIN,
            )

            AuditLog.objects.create(
                actor=user,
                action="PASSWORD_CHANGED",
                entity_type="APP_USER",
                entity_id=user.id,
            )

            return Response({"status": "success", "message": "Password changed successfully."})
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
