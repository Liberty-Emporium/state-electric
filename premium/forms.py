"""
Forms for the premium app.
"""
from django import forms
from django.forms import inlineformset_factory

from core.models import Customer, Division
from standard.models import Job
from .models import (
    RecurringInvoice, RecurringInvoiceLine,
    Expense, ExpenseCategory,
    BankAccount, BankTransaction,
    PurchaseOrder, PurchaseOrderLine,
    Contractor, ContractorPayment,
    TaxForm, DataImport, Contract, EstimateTemplate,
)


class RecurringInvoiceForm(forms.ModelForm):
    class Meta:
        model = RecurringInvoice
        fields = ['customer', 'division', 'frequency', 'status', 'start_date', 'end_date', 'next_invoice_date', 'tax_rate', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'division': forms.Select(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


RecurringLineFormSet = inlineformset_factory(
    RecurringInvoice, RecurringInvoiceLine,
    fields=['description', 'quantity', 'rate', 'sort_order'],
    extra=3, can_delete=True,
    widgets={
        'description': forms.TextInput(attrs={'class': 'form-control'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
        'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'category', 'amount', 'date', 'job', 'division', 'vendor', 'receipt', 'status', 'notes']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'job': forms.Select(attrs={'class': 'form-control'}),
            'division': forms.Select(attrs={'class': 'form-control'}),
            'vendor': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['name', 'account_type', 'bank_name', 'last_four', 'division', 'is_active', 'current_balance']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_four': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 4}),
            'division': forms.Select(attrs={'class': 'form-control'}),
            'current_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class BankTransactionForm(forms.ModelForm):
    class Meta:
        model = BankTransaction
        fields = ['bank_account', 'date', 'description', 'amount', 'reference', 'status', 'notes']
        widgets = {
            'bank_account': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['vendor', 'vendor_address', 'vendor_email', 'division', 'job', 'status', 'order_date', 'expected_date', 'tax_rate', 'shipping', 'notes']
        widgets = {
            'vendor': forms.TextInput(attrs={'class': 'form-control'}),
            'vendor_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'vendor_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'division': forms.Select(attrs={'class': 'form-control'}),
            'job': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'shipping': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


POLineFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseOrderLine,
    fields=['description', 'quantity', 'received_quantity', 'rate', 'sort_order'],
    extra=3, can_delete=True,
    widgets={
        'description': forms.TextInput(attrs={'class': 'form-control'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
        'received_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
        'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)


class ContractorForm(forms.ModelForm):
    class Meta:
        model = Contractor
        fields = ['name', 'business_name', 'entity_type', 'email', 'phone', 'address', 'tax_id', 'w9_on_file', 'w9_date', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'entity_type': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'w9_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ContractorPaymentForm(forms.ModelForm):
    class Meta:
        model = ContractorPayment
        fields = ['contractor', 'amount', 'date', 'description', 'job', 'division', 'is_1099_reportable']
        widgets = {
            'contractor': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'job': forms.Select(attrs={'class': 'form-control'}),
            'division': forms.Select(attrs={'class': 'form-control'}),
        }


class TaxFormForm(forms.ModelForm):
    class Meta:
        model = TaxForm
        fields = ['form_type', 'tax_year', 'recipient_name', 'recipient_tax_id', 'recipient_address',
                  'total_compensation', 'federal_withheld', 'state_withheld', 'social_security_wages',
                  'medicare_wages', 'status', 'notes']
        widgets = {
            'form_type': forms.Select(attrs={'class': 'form-control'}),
            'tax_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'recipient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'total_compensation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'federal_withheld': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'state_withheld': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'social_security_wages': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'medicare_wages': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class DataImportForm(forms.ModelForm):
    class Meta:
        model = DataImport
        fields = ['import_type', 'file']
        widgets = {
            'import_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['title', 'customer', 'division', 'amount', 'start_date', 'end_date', 'body']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'division': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        }


class EstimateTemplateForm(forms.ModelForm):
    class Meta:
        model = EstimateTemplate
        fields = ['name', 'description', 'job_type', 'division', 'base_labor_hours', 'labor_rate',
                  'material_estimate', 'overhead_percent', 'profit_margin_percent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'job_type': forms.TextInput(attrs={'class': 'form-control'}),
            'division': forms.Select(attrs={'class': 'form-control'}),
            'base_labor_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'labor_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'material_estimate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'overhead_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'profit_margin_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
