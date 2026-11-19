from django.contrib import admin
from apps.banking.models import BankAccount, AccountHolder, Beneficiary

class AccountHolderInline(admin.TabularInline):
    model = AccountHolder
    extra = 1

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ["account_number", "account_type", "balance", "currency", "account_status", "opened_at"]
    list_filter = ["account_type", "account_status", "currency"]
    search_fields = ["account_number"]
    inlines = [AccountHolderInline]

@admin.register(AccountHolder)
class AccountHolderAdmin(admin.ModelAdmin):
    list_display = ["account", "user", "holder_role"]
    list_filter = ["holder_role"]

@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ["beneficiary_name", "beneficiary_account_number", "bank_name", "owner_user", "status", "created_at"]
    list_filter = ["status", "bank_name"]
    search_fields = ["beneficiary_name", "beneficiary_account_number"]
