from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    NOTIFICATION entity from ERD.
    """

    class NotificationType(models.TextChoices):
        REGISTRATION = "REGISTRATION", "Registration"
        LOGIN = "LOGIN", "Login"
        TRANSFER = "TRANSFER", "Transfer"
        BILL_PAYMENT = "BILL_PAYMENT", "Bill Payment"
        LOAN = "LOAN", "Loan"
        INVESTMENT = "INVESTMENT", "Investment"
        SUPPORT = "SUPPORT", "Support"
        SYSTEM = "SYSTEM", "System"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.user}"


class AuditLog(models.Model):
    """
    AUDIT_LOG entity from ERD.
    Note: entity_type and entity_id are generic references,
    not conventional foreign keys. They record which model/table
    and which record ID was affected.
    """

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        null=True,
    )
    action = models.CharField(max_length=50)
    entity_type = models.CharField(max_length=50)
    entity_id = models.BigIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} on {self.entity_type}#{self.entity_id} by {self.actor}"
