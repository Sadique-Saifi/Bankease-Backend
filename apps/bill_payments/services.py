from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.banking.models import BankAccount
from apps.bill_payments.models import Biller, BillPayment
from apps.transactions.models import FinancialTransaction, LedgerEntry
from apps.transactions.services import generate_reference_number
from apps.notifications.models import Notification, AuditLog


class BillPaymentService:
    @staticmethod
    def pay_bill(user, account_id, biller_id, consumer_reference, amount, due_date=None):
        amount = Decimal(str(amount))
        if amount <= Decimal("0.00"):
            raise ValidationError("Payment amount must be greater than zero.")

        if not consumer_reference or not consumer_reference.strip():
            raise ValidationError("Consumer reference / account number is required.")

        with transaction.atomic():
            # 1. Validate Biller
            try:
                biller = Biller.objects.get(id=biller_id, status=Biller.Status.ACTIVE)
            except Biller.DoesNotExist:
                raise ValidationError("Biller not found or currently inactive.")

            # 2. Lock and validate bank account
            try:
                account = (
                    BankAccount.objects.select_for_update()
                    .get(id=account_id, holders__user=user)
                )
            except BankAccount.DoesNotExist:
                raise ValidationError("Payment account not found or access unauthorized.")

            if account.account_status != BankAccount.AccountStatus.ACTIVE:
                raise ValidationError("Payment account is not active.")

            if account.balance < amount:
                raise ValidationError(
                    f"Insufficient balance. Available: ₹{account.balance:,.2f}, Required: ₹{amount:,.2f}"
                )

            # 3. Create Financial Transaction
            ref = generate_reference_number(prefix="BIL")
            txn = FinancialTransaction.objects.create(
                reference_number=ref,
                initiated_by=user,
                transaction_type=FinancialTransaction.TransactionType.BILL_PAYMENT,
                amount=amount,
                currency=account.currency,
                transaction_status=FinancialTransaction.TransactionStatus.COMPLETED,
            )

            # 4. Debit account and write ledger
            account.balance -= amount
            account.save(update_fields=["balance"])

            LedgerEntry.objects.create(
                transaction=txn,
                account=account,
                entry_type=LedgerEntry.EntryType.DEBIT,
                amount=amount,
                balance_after=account.balance,
            )

            # 5. Create BillPayment record
            bill_payment = BillPayment.objects.create(
                transaction=txn,
                account=account,
                biller=biller,
                consumer_reference=consumer_reference.strip(),
                due_date=due_date,
            )

            # 6. Notification & Audit Log
            Notification.objects.create(
                user=user,
                title="Bill Payment Successful",
                message=f"Paid ₹{amount:,.2f} to {biller.name} (Ref: {consumer_reference}). Transaction Ref: {ref}.",
                notification_type=Notification.NotificationType.BILL_PAYMENT,
            )

            AuditLog.objects.create(
                actor=user,
                action="BILL_PAID",
                entity_type="BILL_PAYMENT",
                entity_id=bill_payment.id,
            )

            return txn, bill_payment
