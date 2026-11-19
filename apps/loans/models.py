from django.conf import settings
from django.db import models


class LoanProduct(models.Model):
    """
    LOAN_PRODUCT entity from ERD.
    """

    product_name = models.CharField(max_length=150)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    minimum_amount = models.DecimalField(max_digits=15, decimal_places=2)
    maximum_amount = models.DecimalField(max_digits=15, decimal_places=2)
    duration_months = models.IntegerField()

    class Meta:
        db_table = "loan_product"

    def __str__(self):
        return f"{self.product_name} ({self.interest_rate}%)"


class LoanApplication(models.Model):
    """
    LOAN_APPLICATION entity from ERD.
    """

    class ApplicationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        DISBURSED = "DISBURSED", "Disbursed"

    customer = models.ForeignKey(
        "accounts.CustomerProfile",
        on_delete=models.PROTECT,
        related_name="loan_applications",
    )
    loan_product = models.ForeignKey(
        LoanProduct,
        on_delete=models.PROTECT,
        related_name="applications",
    )
    requested_amount = models.DecimalField(max_digits=15, decimal_places=2)
    duration_months = models.IntegerField()
    application_status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_loan_applications",
        null=True,
        blank=True,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "loan_application"
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Loan #{self.pk} - {self.loan_product.product_name}"


class LoanRepayment(models.Model):
    """
    LOAN_REPAYMENT entity from ERD.
    """

    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        OVERDUE = "OVERDUE", "Overdue"

    loan_application = models.ForeignKey(
        LoanApplication,
        on_delete=models.PROTECT,
        related_name="repayments",
    )
    transaction = models.OneToOneField(
        "transactions.FinancialTransaction",
        on_delete=models.PROTECT,
        related_name="loan_repayment",
        null=True,
        blank=True,
    )
    installment_number = models.IntegerField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    due_date = models.DateField()
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    class Meta:
        db_table = "loan_repayment"
        ordering = ["due_date"]

    def __str__(self):
        return f"Repayment #{self.installment_number} for Loan #{self.loan_application_id}"
