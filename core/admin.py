"""Admin configuration for State Electric."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Division, User, EmployeeProfile, Customer, Invoice, InvoiceLineItem, Payment


class EmployeeProfileInline(admin.StackedInline):
    model = EmployeeProfile
    can_delete = False


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'role', 'division', 'is_active_employee']
    list_filter = ['role', 'division', 'is_active_employee', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('State Electric', {'fields': ('role', 'division', 'phone', 'is_active_employee')}),
    )
    inlines = [EmployeeProfileInline]


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'employee_count', 'max_employees']


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 1


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'status', 'total_amount', 'balance_due', 'issue_date']
    list_filter = ['status', 'issue_date']
    search_fields = ['invoice_number', 'customer__name']
    inlines = [InvoiceLineItemInline, PaymentInline]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'division', 'phone', 'is_active']
    list_filter = ['division', 'is_active']
    search_fields = ['name', 'company']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'date', 'method', 'recorded_by']
    list_filter = ['method', 'date']
