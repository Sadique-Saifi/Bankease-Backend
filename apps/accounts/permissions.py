from rest_framework.permissions import BasePermission

class IsCustomer(BasePermission):
    """Allows access only to authenticated customers."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, "role", None) == "CUSTOMER"
        )


class IsBankOfficer(BasePermission):
    """Allows access only to authenticated bank officers."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (getattr(request.user, "role", None) == "BANK_OFFICER" or request.user.is_staff)
        )


class IsOwnerOrOfficer(BasePermission):
    """Allows access to the owner of an object or bank officers."""
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if getattr(request.user, "role", None) == "BANK_OFFICER" or request.user.is_staff:
            return True
        # Check object ownership
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "owner_user"):
            return obj.owner_user == request.user
        if hasattr(obj, "customer") and hasattr(obj.customer, "user"):
            return obj.customer.user == request.user
        return False
