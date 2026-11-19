from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.banking.models import BankAccount
from apps.investments.models import InvestmentProduct, InvestmentOrder, InvestmentHolding
from apps.transactions.models import FinancialTransaction, LedgerEntry
from apps.transactions.services import generate_reference_number
from apps.notifications.models import Notification, AuditLog


class InvestmentService:
    @staticmethod
    def place_order(user, product_id, account_id, amount):
        amount = Decimal(str(amount))
        if not hasattr(user, "customer_profile"):
            raise ValidationError("Only registered customers can place investment orders.")

        with transaction.atomic():
            # 1. Product check
            try:
                product = InvestmentProduct.objects.get(id=product_id, status=InvestmentProduct.Status.ACTIVE)
            except InvestmentProduct.DoesNotExist:
                raise ValidationError("Investment product not found or inactive.")

            if amount < product.minimum_amount:
                raise ValidationError(f"Minimum investment for {product.product_name} is ₹{product.minimum_amount:,.2f}.")

            # 2. Account check & lock
            try:
                account = (
                    BankAccount.objects.select_for_update()
                    .get(id=account_id, holders__user=user)
                )
            except BankAccount.DoesNotExist:
                raise ValidationError("Funding account not found or access unauthorized.")

            if account.balance < amount:
                raise ValidationError(f"Insufficient funds in account {account.account_number}. Balance: ₹{account.balance:,.2f}")

            # 3. Transaction
            ref = generate_reference_number(prefix="INV")
            txn = FinancialTransaction.objects.create(
                reference_number=ref,
                initiated_by=user,
                transaction_type=FinancialTransaction.TransactionType.INVESTMENT,
                amount=amount,
                currency=account.currency,
                transaction_status=FinancialTransaction.TransactionStatus.COMPLETED,
            )

            # 4. Debit account
            account.balance -= amount
            account.save(update_fields=["balance"])

            LedgerEntry.objects.create(
                transaction=txn,
                account=account,
                entry_type=LedgerEntry.EntryType.DEBIT,
                amount=amount,
                balance_after=account.balance,
            )

            # 5. Investment Order
            order = InvestmentOrder.objects.create(
                customer=user.customer_profile,
                investment_product=product,
                transaction=txn,
                amount=amount,
                order_status=InvestmentOrder.OrderStatus.EXECUTED,
            )

            # 6. Update or create Holding (simulated NAV = 100.0)
            simulated_nav = Decimal("100.00")
            units_bought = Decimal(f"{amount / simulated_nav:.4f}")

            holding, created = InvestmentHolding.objects.get_or_create(
                customer=user.customer_profile,
                investment_product=product,
                defaults={"units": Decimal("0.0000"), "invested_amount": Decimal("0.00")},
            )
            holding.units += units_bought
            holding.invested_amount += amount
            holding.save(update_fields=["units", "invested_amount"])

            # 7. Notification & Audit Log
            Notification.objects.create(
                user=user,
                title="Investment Order Executed",
                message=f"Invested ₹{amount:,.2f} in {product.product_name}. Allocated {units_bought} units. Ref: {ref}.",
                notification_type=Notification.NotificationType.INVESTMENT,
            )

            AuditLog.objects.create(
                actor=user,
                action="INVESTMENT_ORDER_EXECUTED",
                entity_type="INVESTMENT_ORDER",
                entity_id=order.id,
            )

            return order
