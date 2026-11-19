from django.contrib import admin
from apps.transactions.models import FinancialTransaction, LedgerEntry, FundTransfer

class LedgerEntryInline(admin.TabularInline):
    model = LedgerEntry
    extra = 0
    readonly_fields = ["account", "entry_type", "amount", "balance_after", "created_at"]

@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    list_display = ["reference_number", "initiated_by", "transaction_type", "amount", "currency", "transaction_status", "created_at"]
    list_filter = ["transaction_type", "transaction_status", "created_at"]
    search_fields = ["reference_number", "initiated_by__username"]
    inlines = [LedgerEntryInline]

@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ["transaction", "account", "entry_type", "amount", "balance_after", "created_at"]
    list_filter = ["entry_type", "created_at"]
    search_fields = ["transaction__reference_number", "account__account_number"]

@admin.register(FundTransfer)
class FundTransferAdmin(admin.ModelAdmin):
    list_display = ["transaction", "source_account", "destination_account", "beneficiary", "remarks"]
