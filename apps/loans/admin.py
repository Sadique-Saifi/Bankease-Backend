from django.contrib import admin
from apps.loans.models import LoanProduct, LoanApplication, LoanRepayment

class LoanRepaymentInline(admin.TabularInline):
    model = LoanRepayment
    extra = 0

@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    list_display = ["product_name", "interest_rate", "minimum_amount", "maximum_amount", "duration_months"]

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "loan_product", "requested_amount", "duration_months", "application_status", "reviewed_by", "submitted_at"]
    list_filter = ["application_status", "loan_product"]
    inlines = [LoanRepaymentInline]

@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ["loan_application", "installment_number", "amount", "due_date", "payment_status", "transaction"]
    list_filter = ["payment_status", "due_date"]
