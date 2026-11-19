from django.contrib import admin
from apps.investments.models import InvestmentProduct, InvestmentOrder, InvestmentHolding

@admin.register(InvestmentProduct)
class InvestmentProductAdmin(admin.ModelAdmin):
    list_display = ["product_name", "product_type", "risk_level", "minimum_amount", "status"]
    list_filter = ["product_type", "risk_level", "status"]

@admin.register(InvestmentOrder)
class InvestmentOrderAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "investment_product", "amount", "order_status", "created_at"]
    list_filter = ["order_status"]

@admin.register(InvestmentHolding)
class InvestmentHoldingAdmin(admin.ModelAdmin):
    list_display = ["customer", "investment_product", "units", "invested_amount"]
