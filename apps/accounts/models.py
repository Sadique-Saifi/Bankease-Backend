from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    APP_USER entity from ERD.
    Maps to Django's AbstractUser with role-based access.
    """

    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        BANK_OFFICER = "BANK_OFFICER", "Bank Officer"

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )

    class Meta:
        db_table = "app_user"

    def __str__(self):
        return self.username

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    @property
    def is_bank_officer(self):
        return self.role == self.Role.BANK_OFFICER


class CustomerProfile(models.Model):
    """
    CUSTOMER_PROFILE entity from ERD.
    One-to-one extension of User for customer-specific data.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    customer_number = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True, default="")
    address = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "customer_profile"

    def __str__(self):
        return f"{self.customer_number} - {self.full_name}"
