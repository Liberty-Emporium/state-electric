"""
Admin configuration for the premium app.
"""
from django.contrib import admin

from .models import (
    RecurringInvoice, RecurringInvoiceLine,
    Expense, ExpenseCategory,
    BankAccount, BankTransaction,
    PurchaseOrder, PurchaseOrderLine,
    Contractor, ContractorPayment,
    TaxForm, DataImport, Contract, EstimateTemplate,
)


class RecurringLineInline(admin.TabularInline):
    model = RecurringInvoiceLine
    extra = 0


class POLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 0


@admin.register(RecurringInvoice)
class RecurringInvoiceAdmin(admin.ModelAdmin):
    list_display = ['customer', 'division', 'frequency', 'status', 'next_invoice_date']
    list_filter = ['status', 'frequency', 'division']
    search_fields = ['customer__name']
    inlines = [RecurringLineInline]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'category', 'amount', 'date', 'status', 'division']
    list_filter = ['status', 'category', 'division', 'date']
    search_fields = ['description', 'vendor']
    date_hierarchy = 'date'


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'bank_name', 'account_type', 'division', 'current_balance', 'is_active']
    list_filter = ['account_type', 'division']


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'description', 'amount', 'status', 'bank_account']
    list_filter = ['status', 'bank_account']
    search_fields = ['description', 'reference']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'vendor', 'division', 'status', 'order_date', 'total']
    list_filter = ['status', 'division']
    search_fields = ['po_number', 'vendor']
    inlines = [POLineInline]


@admin.register(Contractor)
class ContractorAdmin(admin.ModelAdmin):
    list_display = ['name', 'entity_type', 'w9_on_file', 'is_active']
    list_filter = ['entity_type', 'is_active']
    search_fields = ['name', 'business_name']


@admin.register(ContractorPayment)
class ContractorPaymentAdmin(admin.ModelAdmin):
    list_display = ['contractor', 'amount', 'date', 'is_1099_reportable']
    list_filter = ['is_1099_reportable', 'date']
    search_fields = ['contractor__name']


@admin.register(TaxForm)
class TaxFormAdmin(admin.ModelAdmin):
    list_display = ['form_type', 'tax_year', 'recipient_name', 'total_compensation', 'status']
    list_filter = ['form_type', 'tax_year', 'status']
    search_fields = ['recipient_name']


@admin.register(DataImport)
class DataImportAdmin(admin.ModelAdmin):
    list_display = ['import_type', 'status', 'total_rows', 'imported_rows', 'error_rows', 'created_at']
    list_filter = ['status', 'import_type']
    readonly_fields = ['error_log']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['title', 'customer', 'status', 'amount', 'start_date']
    list_filter = ['status', 'division']
    search_fields = ['title', 'customer__name']


@admin.register(EstimateTemplate)
class EstimateTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'job_type', 'division', 'estimated_total']
    list_filter = ['division']
    search_fields = ['name', 'job_type']
