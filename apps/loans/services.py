import datetime
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.loans.models import LoanApplication, LoanRepayment
from apps.banking.models import BankAccount
from apps.transactions.models import FinancialTransaction, LedgerEntry
from apps.transactions.services import generate_reference_number
from apps.notifications.models import Notification, AuditLog


def add_months(sourcedate, months):
    """Add integer months to a datetime.date object without dateutil."""
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, 28)  # safe day for all months
    return datetime.date(year, month, day)


class LoanService:
    @staticmethod
    def calculate_monthly_installment(principal, annual_interest_rate, duration_months):
        """Calculates monthly EMI based on standard formula."""
        P = float(principal)
        r = (float(annual_interest_rate) / 100.0) / 12.0
        n = int(duration_months)

        if r == 0:
            emi = P / n
        else:
            emi = (P * r * ((1 + r) ** n)) / (((1 + r) ** n) - 1)
        return Decimal(f"{emi:.2f}")

    @staticmethod
    def approve_loan(officer_user, loan_application_id, approve=True):
        with transaction.atomic():
            application = LoanApplication.objects.select_for_update().get(id=loan_application_id)
            if application.application_status not in [
                LoanApplication.ApplicationStatus.PENDING,
                LoanApplication.ApplicationStatus.UNDER_REVIEW,
            ]:
                raise ValidationError(f"Application cannot be updated from status {application.application_status}.")

            application.reviewed_by = officer_user
            if approve:
                application.application_status = LoanApplication.ApplicationStatus.APPROVED
                application.save()

                # Generate repayment installments
                monthly_emi = LoanService.calculate_monthly_installment(
                    principal=application.requested_amount,
                    annual_interest_rate=application.loan_product.interest_rate,
                    duration_months=application.duration_months,
                )

                today = datetime.date.today()
                for i in range(1, application.duration_months + 1):
                    due_date = add_months(today, i)
                    LoanRepayment.objects.create(
                        loan_application=application,
                        installment_number=i,
                        amount=monthly_emi,
                        due_date=due_date,
                        payment_status=LoanRepayment.PaymentStatus.PENDING,
                    )

                # Send notification to customer
                Notification.objects.create(
                    user=application.customer.user,
                    title="Loan Application Approved!",
                    message=f"Congratulations! Your application for {application.loan_product.product_name} of ₹{application.requested_amount:,.2f} has been approved. Monthly EMI: ₹{monthly_emi:,.2f}.",
                    notification_type=Notification.NotificationType.LOAN,
                )

                AuditLog.objects.create(
                    actor=officer_user,
                    action="LOAN_APPROVED",
                    entity_type="LOAN_APPLICATION",
                    entity_id=application.id,
                )
            else:
                application.application_status = LoanApplication.ApplicationStatus.REJECTED
                application.save()

                Notification.objects.create(
                    user=application.customer.user,
                    title="Loan Application Update",
                    message=f"We regret to inform you that your loan application for {application.loan_product.product_name} was not approved at this time.",
                    notification_type=Notification.NotificationType.LOAN,
                )

                AuditLog.objects.create(
                    actor=officer_user,
                    action="LOAN_REJECTED",
                    entity_type="LOAN_APPLICATION",
                    entity_id=application.id,
                )

            return application

    @staticmethod
    def pay_repayment(user, repayment_id, account_id):
        with transaction.atomic():
            repayment = LoanRepayment.objects.select_for_update().get(
                id=repayment_id,
                loan_application__customer__user=user,
            )

            if repayment.payment_status == LoanRepayment.PaymentStatus.PAID:
                raise ValidationError("This installment has already been paid.")

            account = BankAccount.objects.select_for_update().get(id=account_id, holders__user=user)
            if account.balance < repayment.amount:
                raise ValidationError(f"Insufficient funds in account {account.account_number} to pay EMI of ₹{repayment.amount:,.2f}.")

            ref = generate_reference_number(prefix="LNR")
            txn = FinancialTransaction.objects.create(
                reference_number=ref,
                initiated_by=user,
                transaction_type=FinancialTransaction.TransactionType.LOAN_REPAYMENT,
                amount=repayment.amount,
                currency=account.currency,
                transaction_status=FinancialTransaction.TransactionStatus.COMPLETED,
            )

            account.balance -= repayment.amount
            account.save(update_fields=["balance"])

            LedgerEntry.objects.create(
                transaction=txn,
                account=account,
                entry_type=LedgerEntry.EntryType.DEBIT,
                amount=repayment.amount,
                balance_after=account.balance,
            )

            repayment.transaction = txn
            repayment.payment_status = LoanRepayment.PaymentStatus.PAID
            repayment.save(update_fields=["transaction", "payment_status"])

            Notification.objects.create(
                user=user,
                title="Loan Installment Paid",
                message=f"Installment #{repayment.installment_number} of ₹{repayment.amount:,.2f} for Loan #{repayment.loan_application_id} paid successfully. Ref: {ref}.",
                notification_type=Notification.NotificationType.LOAN,
            )

            return repayment
