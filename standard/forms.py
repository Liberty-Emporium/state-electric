"""
Forms for the standard app.
"""
from django import forms
from django.forms import inlineformset_factory

from core.models import Customer, Division
from .models import (
    Job, TimeEntry, PayPeriod, PayrollEntry,
    Estimate, EstimateLineItem,
)


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'customer', 'division', 'description',
            'status', 'priority', 'scheduled_date', 'completed_date',
            'estimated_hours', 'estimated_cost',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'division': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'completed_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            if user.division:
                self.fields['division'].initial = user.division
                self.fields['customer'].queryset = Customer.objects.filter(
                    division=user.division.name
                )


class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ['employee', 'job', 'date', 'hours', 'description', 'clock_in', 'clock_out']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'job': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'clock_in': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'clock_out': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class PayPeriodForm(forms.ModelForm):
    class Meta:
        model = PayPeriod
        fields = ['start_date', 'end_date', 'division', 'status', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'division': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PayrollEntryForm(forms.ModelForm):
    class Meta:
        model = PayrollEntry
        fields = [
            'employee', 'regular_hours', 'overtime_hours',
            'gross_pay', 'other_deductions', 'notes',
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'regular_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'overtime_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'gross_pay': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_deductions': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class EstimateForm(forms.ModelForm):
    class Meta:
        model = Estimate
        fields = [
            'customer', 'division', 'date', 'expiry_date',
            'tax_rate', 'notes', 'internal_notes',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'division': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            if user.division:
                self.fields['division'].initial = user.division
                self.fields['customer'].queryset = Customer.objects.filter(
                    division=user.division.name
                )


EstimateLineFormSet = inlineformset_factory(
    Estimate, EstimateLineItem,
    fields=['description', 'quantity', 'rate', 'sort_order'],
    extra=3, can_delete=True,
    widgets={
        'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
        'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)
