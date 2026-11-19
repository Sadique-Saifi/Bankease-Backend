import random
import string
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.banking.models import BankAccount, AccountHolder, Beneficiary
from apps.transactions.models import FinancialTransaction, LedgerEntry, FundTransfer
from apps.notifications.models import Notification, AuditLog


def generate_reference_number(prefix="TXN"):
    """Generate a unique transaction reference number."""
    while True:
        ref = f"{prefix}{''.join(random.choices(string.ascii_uppercase + string.digits, k=12))}"
        if not FinancialTransaction.objects.filter(reference_number=ref).exists():
            return ref


class TransferService:
    @staticmethod
    def execute_transfer(
        user,
        source_account_id,
        amount,
        destination_account_number=None,
        beneficiary_id=None,
        remarks="",
    ):
        """
        Executes a fund transfer atomically with balance locks, ledger updates,
        and notification dispatch.
        """
        amount = Decimal(str(amount))
        if amount <= Decimal("0.00"):
            raise ValidationError("Transfer amount must be strictly greater than zero.")

        with transaction.atomic():
            # 1. Validate source account ownership & lock row
            try:
                source_account = (
                    BankAccount.objects.select_for_update()
                    .get(id=source_account_id, holders__user=user)
                )
            except BankAccount.DoesNotExist:
                raise ValidationError("Source account not found or access unauthorized.")

            if source_account.account_status != BankAccount.AccountStatus.ACTIVE:
                raise ValidationError(f"Source account is {source_account.get_account_status_display().lower()} and cannot be debited.")

            # 2. Check sufficient balance
            if source_account.balance < amount:
                raise ValidationError(
                    f"Insufficient funds. Available balance: ₹{source_account.balance:,.2f}, Requested: ₹{amount:,.2f}"
                )

            # 3. Resolve destination
            beneficiary = None
            dest_account = None

            if beneficiary_id:
                try:
                    beneficiary = Beneficiary.objects.get(
                        id=beneficiary_id, owner_user=user, status=Beneficiary.Status.ACTIVE
                    )
                    target_account_number = beneficiary.beneficiary_account_number
                except Beneficiary.DoesNotExist:
                    raise ValidationError("Selected beneficiary is invalid or inactive.")
            elif destination_account_number:
                target_account_number = destination_account_number.strip()
            else:
                raise ValidationError("Either a destination account number or beneficiary must be provided.")

            if target_account_number == source_account.account_number:
                raise ValidationError("Cannot transfer funds to the same source account.")

            # Check if internal account in BankEase
            dest_account = (
                BankAccount.objects.select_for_update()
                .filter(account_number=target_account_number)
                .first()
            )

            if dest_account and dest_account.account_status != BankAccount.AccountStatus.ACTIVE:
                raise ValidationError("Destination account is inactive or frozen.")

            # 4. Generate transaction record
            ref_num = generate_reference_number(prefix="TXN")
            txn = FinancialTransaction.objects.create(
                reference_number=ref_num,
                initiated_by=user,
                transaction_type=FinancialTransaction.TransactionType.TRANSFER,
                amount=amount,
                currency=source_account.currency,
                transaction_status=FinancialTransaction.TransactionStatus.COMPLETED,
            )

            # 5. Debit source account & write ledger entry
            source_account.balance -= amount
            source_account.save(update_fields=["balance"])

            LedgerEntry.objects.create(
                transaction=txn,
                account=source_account,
                entry_type=LedgerEntry.EntryType.DEBIT,
                amount=amount,
                balance_after=source_account.balance,
            )

            # 6. If internal destination, credit destination account & write ledger entry
            if dest_account:
                dest_account.balance += amount
                dest_account.save(update_fields=["balance"])

                LedgerEntry.objects.create(
                    transaction=txn,
                    account=dest_account,
                    entry_type=LedgerEntry.EntryType.CREDIT,
                    amount=amount,
                    balance_after=dest_account.balance,
                )

            # 7. Create FundTransfer link
            fund_transfer = FundTransfer.objects.create(
                transaction=txn,
                source_account=source_account,
                destination_account=dest_account,
                beneficiary=beneficiary,
                remarks=remarks or f"Transfer to {target_account_number}",
            )

            # 8. Notifications
            Notification.objects.create(
                user=user,
                title="Fund Transfer Successful",
                message=f"Debited ₹{amount:,.2f} from {source_account.account_number}. Transferred to {target_account_number}. Ref: {ref_num}.",
                notification_type=Notification.NotificationType.TRANSFER,
            )

            # Notify internal recipient holders if any
            if dest_account:
                for holder in dest_account.holders.all():
                    if holder.user != user:
                        Notification.objects.create(
                            user=holder.user,
                            title="Funds Received",
                            message=f"Credited ₹{amount:,.2f} to account {dest_account.account_number} from {source_account.account_number}. Ref: {ref_num}.",
                            notification_type=Notification.NotificationType.TRANSFER,
                        )

            # 9. Audit Log
            AuditLog.objects.create(
                actor=user,
                action="FUND_TRANSFER_COMPLETED",
                entity_type="FINANCIAL_TRANSACTION",
                entity_id=txn.id,
            )

            return txn, fund_transfer
