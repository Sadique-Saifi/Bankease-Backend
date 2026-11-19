from django.db import models


class InvestmentProduct(models.Model):
    """
    INVESTMENT_PRODUCT entity from ERD.
    """

    class ProductType(models.TextChoices):
        MUTUAL_FUND = "MUTUAL_FUND", "Mutual Fund"
        FIXED_DEPOSIT = "FIXED_DEPOSIT", "Fixed Deposit"
        RECURRING_DEPOSIT = "RECURRING_DEPOSIT", "Recurring Deposit"
        BONDS = "BONDS", "Bonds"
        STOCKS = "STOCKS", "Stocks"

    class RiskLevel(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    product_name = models.CharField(max_length=150)
    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
    )
    risk_level = models.CharField(
        max_length=10,
        choices=RiskLevel.choices,
    )
    minimum_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        db_table = "investment_product"

    def __str__(self):
        return f"{self.product_name} ({self.product_type})"


class InvestmentOrder(models.Model):
    """
    INVESTMENT_ORDER entity from ERD.
    """

    class OrderStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        EXECUTED = "EXECUTED", "Executed"
        CANCELLED = "CANCELLED", "Cancelled"

    customer = models.ForeignKey(
        "accounts.CustomerProfile",
        on_delete=models.PROTECT,
        related_name="investment_orders",
    )
    investment_product = models.ForeignKey(
        InvestmentProduct,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    transaction = models.OneToOneField(
        "transactions.FinancialTransaction",
        on_delete=models.PROTECT,
        related_name="investment_order",
        null=True,
        blank=True,
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    order_status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "investment_order"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} - {self.investment_product.product_name}"


class InvestmentHolding(models.Model):
    """
    INVESTMENT_HOLDING entity from ERD.
    """

    customer = models.ForeignKey(
        "accounts.CustomerProfile",
        on_delete=models.PROTECT,
        related_name="investment_holdings",
    )
    investment_product = models.ForeignKey(
        InvestmentProduct,
        on_delete=models.PROTECT,
        related_name="holdings",
    )
    units = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    invested_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        db_table = "investment_holding"
        unique_together = [("customer", "investment_product")]

    def __str__(self):
        return f"{self.customer} - {self.investment_product} ({self.units} units)"
