from django.db import models


class Biller(models.Model):
    """
    BILLER entity from ERD.
    """

    class Category(models.TextChoices):
        ELECTRICITY = "ELECTRICITY", "Electricity"
        WATER = "WATER", "Water"
        GAS = "GAS", "Gas"
        INTERNET = "INTERNET", "Internet"
        MOBILE = "MOBILE", "Mobile"
        DTH = "DTH", "DTH"
        INSURANCE = "INSURANCE", "Insurance"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    name = models.CharField(max_length=150)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        db_table = "biller"

    def __str__(self):
        return f"{self.name} ({self.category})"


class BillPayment(models.Model):
    """
    BILL_PAYMENT entity from ERD.
    """

    transaction = models.OneToOneField(
        "transactions.FinancialTransaction",
        on_delete=models.PROTECT,
        related_name="bill_payment",
    )
    account = models.ForeignKey(
        "banking.BankAccount",
        on_delete=models.PROTECT,
        related_name="bill_payments",
    )
    biller = models.ForeignKey(
        Biller,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    consumer_reference = models.CharField(max_length=100)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "bill_payment"

    def __str__(self):
        return f"Bill {self.biller.name} - {self.consumer_reference}"
