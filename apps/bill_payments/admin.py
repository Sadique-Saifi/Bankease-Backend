from django.contrib import admin
from apps.bill_payments.models import Biller, BillPayment

@admin.register(Biller)
class BillerAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "status"]
    list_filter = ["category", "status"]
    search_fields = ["name"]

@admin.register(BillPayment)
class BillPaymentAdmin(admin.ModelAdmin):
    list_display = ["transaction", "account", "biller", "consumer_reference", "due_date"]
    list_filter = ["biller__category"]
    search_fields = ["consumer_reference", "transaction__reference_number"]
