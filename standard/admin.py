"""
Admin configuration for the standard app.
"""
from django.contrib import admin

from .models import (
    Job, TimeEntry, PayPeriod, PayrollEntry,
    Estimate, EstimateLineItem,
)


class TimeEntryInline(admin.TabularInline):
    model = TimeEntry
    extra = 0
    readonly_fields = ['created_at']


class EstimateLineInline(admin.TabularInline):
    model = EstimateLineItem
    extra = 0


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'customer', 'division', 'status', 'priority', 'scheduled_date', 'is_overdue']
    list_filter = ['status', 'priority', 'division', 'created_at']
    search_fields = ['title', 'customer__name', 'description']
    list_editable = ['status', 'priority']
    readonly_fields = ['created_at', 'updated_at', 'actual_hours']
    inlines = [TimeEntryInline]
    date_hierarchy = 'scheduled_date'

    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'job', 'date', 'hours', 'is_overtime', 'clock_in', 'clock_out']
    list_filter = ['is_overtime', 'date', 'employee']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name', 'job__title']
    date_hierarchy = 'date'


@admin.register(PayPeriod)
class PayPeriodAdmin(admin.ModelAdmin):
    list_display = ['division', 'start_date', 'end_date', 'status', 'employee_count', 'total_gross', 'total_net']
    list_filter = ['status', 'division']
    list_editable = ['status']
    date_hierarchy = 'start_date'


@admin.register(PayrollEntry)
class PayrollEntryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'pay_period', 'regular_hours', 'overtime_hours', 'gross_pay', 'federal_tax', 'state_tax', 'net_pay']
    list_filter = ['pay_period__division', 'pay_period']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['fica_ss', 'fica_medicare', 'net_pay', 'created_at', 'updated_at']


@admin.register(Estimate)
class EstimateAdmin(admin.ModelAdmin):
    list_display = ['estimate_number', 'customer', 'division', 'status', 'date', 'total', 'expiry_date']
    list_filter = ['status', 'division', 'date']
    search_fields = ['estimate_number', 'customer__name', 'notes']
    list_editable = ['status']
    inlines = [EstimateLineInline]
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EstimateLineItem)
class EstimateLineItemAdmin(admin.ModelAdmin):
    list_display = ['estimate', 'description', 'quantity', 'rate', 'amount']
    list_filter = ['estimate__division']
    search_fields = ['description', 'estimate__estimate_number']
