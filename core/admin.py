"""
Admin configuration for State Electric.
"""
from django.contrib import admin

from core.models import User, Division, Customer, EmployeeProfile, Invoice, InvoiceLineItem, Payment

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'first_name', 'last_name', 'role', 'division', 'is_active']
    list_filter = ['role', 'division', 'is_active']
    search_fields = ['username', 'first_name', 'last_name']

@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'employee_count', 'max_employees', 'is_at_capacity']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'division', 'is_active', 'created_at']
    list_filter = ['division', 'is_active']
    search_fields = ['name', 'company', 'address', 'phone', 'email']

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'hire_date', 'pay_rate', 'pay_type', 'title']
    list_filter = ['pay_type']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'title']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'status', 'issue_date', 'due_date', 'total_amount', 'balance_due']
    list_filter = ['status', 'issue_date']
    search_fields = ['invoice_number', 'customer__name']
    date_hierarchy = 'issue_date'

@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'rate', 'amount']
    search_fields = ['invoice__invoice_number', 'description']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'date', 'method', 'recorded_by']
    list_filter = ['method', 'date']
    search_fields = ['invoice__invoice_number', 'reference']
    date_hierarchy = 'date'
