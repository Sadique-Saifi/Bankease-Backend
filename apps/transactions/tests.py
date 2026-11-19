from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User, CustomerProfile
from apps.banking.models import BankAccount, AccountHolder
from apps.transactions.models import FinancialTransaction, LedgerEntry

class TransferTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="transfer_tester",
            email="transfer_tester@bankease.com",
            password="Password@123",
            role=User.Role.CUSTOMER,
        )
        self.profile = CustomerProfile.objects.create(
            user=self.user,
            customer_number="CUST999001",
            full_name="Transfer Tester",
        )
        self.acc1 = BankAccount.objects.create(
            account_number="601111111111",
            account_type=BankAccount.AccountType.SAVINGS,
            balance=Decimal("5000.00"),
            currency="INR",
            account_status=BankAccount.AccountStatus.ACTIVE,
        )
        AccountHolder.objects.create(account=self.acc1, user=self.user, holder_role=AccountHolder.HolderRole.PRIMARY)

        # Recipient
        self.recipient_user = User.objects.create_user(
            username="recipient_tester",
            email="recipient_tester@bankease.com",
            password="Password@123",
            role=User.Role.CUSTOMER,
        )
        self.acc2 = BankAccount.objects.create(
            account_number="602222222222",
            account_type=BankAccount.AccountType.SAVINGS,
            balance=Decimal("1000.00"),
            currency="INR",
            account_status=BankAccount.AccountStatus.ACTIVE,
        )
        AccountHolder.objects.create(account=self.acc2, user=self.recipient_user, holder_role=AccountHolder.HolderRole.PRIMARY)

        # Authenticate
        self.client.force_authenticate(user=self.user)
        self.transfer_url = reverse("fund-transfer-create")

    def test_successful_transfer(self):
        payload = {
            "source_account_id": self.acc1.id,
            "destination_account_number": self.acc2.account_number,
            "amount": "1000.00",
            "remarks": "Unit test transfer",
        }
        res = self.client.post(self.transfer_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        self.acc1.refresh_from_db()
        self.acc2.refresh_from_db()
        self.assertEqual(self.acc1.balance, Decimal("4000.00"))
        self.assertEqual(self.acc2.balance, Decimal("2000.00"))

        # Verify ledger entries
        debit_entry = LedgerEntry.objects.filter(account=self.acc1, entry_type=LedgerEntry.EntryType.DEBIT).first()
        credit_entry = LedgerEntry.objects.filter(account=self.acc2, entry_type=LedgerEntry.EntryType.CREDIT).first()
        self.assertIsNotNone(debit_entry)
        self.assertIsNotNone(credit_entry)
        self.assertEqual(debit_entry.amount, Decimal("1000.00"))
        self.assertEqual(credit_entry.amount, Decimal("1000.00"))

    def test_insufficient_balance_rejected(self):
        payload = {
            "source_account_id": self.acc1.id,
            "destination_account_number": self.acc2.account_number,
            "amount": "99999.00",
        }
        res = self.client.post(self.transfer_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.acc1.refresh_from_db()
        self.assertEqual(self.acc1.balance, Decimal("5000.00"))
