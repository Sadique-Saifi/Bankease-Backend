import random
import string
from decimal import Decimal
from django.db import transaction
from apps.banking.models import BankAccount, AccountHolder
from apps.notifications.models import Notification, AuditLog

def generate_account_number():
    """Generate a unique 12-digit account number."""
    while True:
        num = f"60{''.join(random.choices(string.digits, k=10))}"
        if not BankAccount.objects.filter(account_number=num).exists():
            return num

def create_bank_account_for_user(user, account_type=BankAccount.AccountType.SAVINGS, initial_deposit=Decimal("0.00")):
    with transaction.atomic():
        acc_num = generate_account_number()
        account = BankAccount.objects.create(
            account_number=acc_num,
            account_type=account_type,
            balance=initial_deposit,
            currency="INR",
            account_status=BankAccount.AccountStatus.ACTIVE,
        )
        AccountHolder.objects.create(
            account=account,
            user=user,
            holder_role=AccountHolder.HolderRole.PRIMARY,
        )
        Notification.objects.create(
            user=user,
            title="New Account Opened",
            message=f"Your new {account.get_account_type_display()} account {acc_num} has been opened with balance ₹{initial_deposit:,.2f}.",
            notification_type=Notification.NotificationType.SYSTEM,
        )
        AuditLog.objects.create(
            actor=user,
            action="ACCOUNT_OPENED",
            entity_type="BANK_ACCOUNT",
            entity_id=account.id,
        )
        return account
