from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User, CustomerProfile
from apps.banking.models import BankAccount, AccountHolder, Beneficiary
from apps.bill_payments.models import Biller
from apps.loans.models import LoanProduct
from apps.investments.models import InvestmentProduct
from apps.notifications.models import Notification


class Command(BaseCommand):
    help = "Seeds initial demo data (officers, customer, billers, loan products, investment products)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding BankEase database...")

        with transaction.atomic():
            # 1. Create Bank Officer
            officer, created = User.objects.get_or_create(
                username="officer1",
                defaults={
                    "email": "officer1@bankease.com",
                    "role": User.Role.BANK_OFFICER,
                    "is_staff": True,
                    "is_superuser": True,
                    "first_name": "Sadiq",
                    "last_name": "Officer",
                },
            )
            if created or not officer.has_usable_password():
                officer.set_password("Admin@1234")
                officer.save()
                self.stdout.write(self.style.SUCCESS("Created Bank Officer: officer1 / Admin@1234"))

            # 2. Create Demo Customer
            customer_user, cust_created = User.objects.get_or_create(
                username="customer1",
                defaults={
                    "email": "customer1@bankease.com",
                    "role": User.Role.CUSTOMER,
                    "first_name": "John",
                    "last_name": "Doe",
                },
            )
            if cust_created or not customer_user.has_usable_password():
                customer_user.set_password("Customer@1234")
                customer_user.save()
                self.stdout.write(self.style.SUCCESS("Created Customer: customer1 / Customer@1234"))

            # Customer Profile
            profile, _ = CustomerProfile.objects.get_or_create(
                user=customer_user,
                defaults={
                    "customer_number": "CUST100001",
                    "full_name": "John Doe",
                    "phone_number": "+91 9876543210",
                    "address": "404 Banking Boulevard, Fintech City, India",
                },
            )

            # Customer Accounts
            acc1, _ = BankAccount.objects.get_or_create(
                account_number="601000123456",
                defaults={
                    "account_type": BankAccount.AccountType.SAVINGS,
                    "balance": Decimal("75000.00"),
                    "currency": "INR",
                    "account_status": BankAccount.AccountStatus.ACTIVE,
                },
            )
            AccountHolder.objects.get_or_create(
                account=acc1, user=customer_user, defaults={"holder_role": AccountHolder.HolderRole.PRIMARY}
            )

            acc2, _ = BankAccount.objects.get_or_create(
                account_number="602000654321",
                defaults={
                    "account_type": BankAccount.AccountType.CURRENT,
                    "balance": Decimal("30000.00"),
                    "currency": "INR",
                    "account_status": BankAccount.AccountStatus.ACTIVE,
                },
            )
            AccountHolder.objects.get_or_create(
                account=acc2, user=customer_user, defaults={"holder_role": AccountHolder.HolderRole.PRIMARY}
            )

            # Sample Beneficiary
            Beneficiary.objects.get_or_create(
                owner_user=customer_user,
                beneficiary_account_number="609999888877",
                defaults={
                    "beneficiary_name": "Alice Smith",
                    "bank_name": "HDFC Bank",
                    "status": Beneficiary.Status.ACTIVE,
                },
            )

            # 3. Billers
            billers_data = [
                ("Maharashtra State Electricity", Biller.Category.ELECTRICITY),
                ("Adani Electricity Mumbai", Biller.Category.ELECTRICITY),
                ("Brihanmumbai Municipal Water", Biller.Category.WATER),
                ("Mahanagar Gas Limited", Biller.Category.GAS),
                ("Airtel Broadband & Fiber", Biller.Category.INTERNET),
                ("Jio Fiber", Biller.Category.INTERNET),
                ("Reliance Jio Mobile Postpaid", Biller.Category.MOBILE),
                ("Tata Play DTH", Biller.Category.DTH),
                ("Life Insurance Corporation (LIC)", Biller.Category.INSURANCE),
            ]
            for name, cat in billers_data:
                Biller.objects.get_or_create(name=name, defaults={"category": cat, "status": Biller.Status.ACTIVE})

            # 4. Loan Products
            loans_data = [
                ("BankEase Home Loan", Decimal("8.50"), Decimal("500000.00"), Decimal("10000000.00"), 240),
                ("Express Personal Loan", Decimal("11.50"), Decimal("25000.00"), Decimal("1500000.00"), 36),
                ("Auto Drive Car Loan", Decimal("9.20"), Decimal("100000.00"), Decimal("3000000.00"), 60),
                ("Global Education Loan", Decimal("8.00"), Decimal("50000.00"), Decimal("4000000.00"), 84),
            ]
            for pname, rate, min_a, max_a, dur in loans_data:
                LoanProduct.objects.get_or_create(
                    product_name=pname,
                    defaults={
                        "interest_rate": rate,
                        "minimum_amount": min_a,
                        "maximum_amount": max_a,
                        "duration_months": dur,
                    },
                )

            # 5. Investment Products
            inv_data = [
                ("BankEase Bluechip Equity Mutual Fund", InvestmentProduct.ProductType.MUTUAL_FUND, InvestmentProduct.RiskLevel.HIGH, Decimal("500.00")),
                ("BankEase Balanced Advantage Hybrid Fund", InvestmentProduct.ProductType.MUTUAL_FUND, InvestmentProduct.RiskLevel.MEDIUM, Decimal("1000.00")),
                ("Sovereign Gold Bonds Series 2026", InvestmentProduct.ProductType.BONDS, InvestmentProduct.RiskLevel.LOW, Decimal("5000.00")),
                ("High Yield 1-Year Fixed Deposit", InvestmentProduct.ProductType.FIXED_DEPOSIT, InvestmentProduct.RiskLevel.LOW, Decimal("10000.00")),
                ("Smart Monthly Recurring Deposit", InvestmentProduct.ProductType.RECURRING_DEPOSIT, InvestmentProduct.RiskLevel.LOW, Decimal("1000.00")),
            ]
            for pname, ptype, risk, min_a in inv_data:
                InvestmentProduct.objects.get_or_create(
                    product_name=pname,
                    defaults={
                        "product_type": ptype,
                        "risk_level": risk,
                        "minimum_amount": min_a,
                        "status": InvestmentProduct.Status.ACTIVE,
                    },
                )

            # Welcome notification
            Notification.objects.get_or_create(
                user=customer_user,
                title="Welcome to BankEase Net Banking",
                defaults={
                    "message": "Welcome to BankEase NextGen Net Banking! Your primary accounts have been provisioned.",
                    "notification_type": Notification.NotificationType.REGISTRATION,
                },
            )

        self.stdout.write(self.style.SUCCESS("BankEase database seeded successfully!"))
