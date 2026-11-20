from django.conf import settings
from django.db import models


class BankAccount(models.Model):
    """
    BANK_ACCOUNT entity from ERD.
    """

    class AccountType(models.TextChoices):
        SAVINGS = "SAVINGS", "Savings"
        CURRENT = "CURRENT", "Current"
        FIXED_DEPOSIT = "FIXED_DEPOSIT", "Fixed Deposit"

    class AccountStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        FROZEN = "FROZEN", "Frozen"
        CLOSED = "CLOSED", "Closed"

    account_number = models.CharField(max_length=20, unique=True)
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.SAVINGS,
    )
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="INR")
    account_status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
    )
    opened_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bank_account"
        indexes = [
            models.Index(fields=["account_number"]),
            models.Index(fields=["account_status"]),
        ]

    def __str__(self):
        return f"{self.account_number} ({self.account_type})"


class AccountHolder(models.Model):
    """
    ACCOUNT_HOLDER entity from ERD.
    Many-to-many junction between User and BankAccount.
    """

    class HolderRole(models.TextChoices):
        PRIMARY = "PRIMARY", "Primary"
        JOINT = "JOINT", "Joint"
        NOMINEE = "NOMINEE", "Nominee"

    account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name="holders",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account_holdings",
    )
    holder_role = models.CharField(
        max_length=20,
        choices=HolderRole.choices,
        default=HolderRole.PRIMARY,
    )

    class Meta:
        db_table = "account_holder"
        unique_together = [("account", "user")]

    def __str__(self):
        return f"{self.user} - {self.account} ({self.holder_role})"


class Beneficiary(models.Model):
    """
    BENEFICIARY entity from ERD.
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="beneficiaries",
    )
    beneficiary_account_number = models.CharField(max_length=20)
    beneficiary_name = models.CharField(max_length=150)
    bank_name = models.CharField(max_length=150, blank=True, default="BankEase")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "beneficiary"
        verbose_name_plural = "beneficiaries"

    def __str__(self):
        return f"{self.beneficiary_name} ({self.beneficiary_account_number})"


class AccountOpeningRequest(models.Model):
    """
    Tracks account-opening requests that require officer approval.
    """

    class RequestStatus(models.TextChoices):
        PENDING_REVIEW = "PENDING_REVIEW", "Pending Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account_opening_requests",
    )
    account_type = models.CharField(
        max_length=20,
        choices=BankAccount.AccountType.choices,
        default=BankAccount.AccountType.SAVINGS,
    )
    initial_deposit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING_REVIEW,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_account_requests",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    officer_remarks = models.TextField(blank=True, default="")
    created_account = models.ForeignKey(
        BankAccount,
        on_delete=models.SET_NULL,
        related_name="opening_request",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "account_opening_request"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Request #{self.pk} by {self.requested_by} - {self.status}"
