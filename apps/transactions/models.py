from django.conf import settings
from django.db import models


class FinancialTransaction(models.Model):
    """
    FINANCIAL_TRANSACTION entity from ERD.
    Central transaction record for all financial operations.
    """

    class TransactionType(models.TextChoices):
        TRANSFER = "TRANSFER", "Transfer"
        BILL_PAYMENT = "BILL_PAYMENT", "Bill Payment"
        LOAN_REPAYMENT = "LOAN_REPAYMENT", "Loan Repayment"
        INVESTMENT = "INVESTMENT", "Investment"
        DEPOSIT = "DEPOSIT", "Deposit"
        WITHDRAWAL = "WITHDRAWAL", "Withdrawal"

    class TransactionStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        REVERSED = "REVERSED", "Reversed"

    reference_number = models.CharField(max_length=50, unique=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    transaction_status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "financial_transaction"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["reference_number"]),
            models.Index(fields=["transaction_status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.reference_number} - {self.transaction_type} - {self.amount}"


class LedgerEntry(models.Model):
    """
    LEDGER_ENTRY entity from ERD.
    Double-entry bookkeeping records.
    """

    class EntryType(models.TextChoices):
        DEBIT = "DEBIT", "Debit"
        CREDIT = "CREDIT", "Credit"

    transaction = models.ForeignKey(
        FinancialTransaction,
        on_delete=models.PROTECT,
        related_name="ledger_entries",
    )
    account = models.ForeignKey(
        "banking.BankAccount",
        on_delete=models.PROTECT,
        related_name="ledger_entries",
    )
    entry_type = models.CharField(
        max_length=10,
        choices=EntryType.choices,
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_entry"
        verbose_name_plural = "ledger entries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.entry_type} {self.amount} on {self.account}"


class FundTransfer(models.Model):
    """
    FUND_TRANSFER entity from ERD.
    """

    transaction = models.OneToOneField(
        FinancialTransaction,
        on_delete=models.PROTECT,
        related_name="fund_transfer",
    )
    source_account = models.ForeignKey(
        "banking.BankAccount",
        on_delete=models.PROTECT,
        related_name="outgoing_transfers",
    )
    destination_account = models.ForeignKey(
        "banking.BankAccount",
        on_delete=models.PROTECT,
        related_name="incoming_transfers",
        null=True,
        blank=True,
    )
    beneficiary = models.ForeignKey(
        "banking.Beneficiary",
        on_delete=models.SET_NULL,
        related_name="transfers",
        null=True,
        blank=True,
    )
    remarks = models.TextField(blank=True, default="")

    class Meta:
        db_table = "fund_transfer"

    def __str__(self):
        return f"Transfer {self.transaction.reference_number}"
