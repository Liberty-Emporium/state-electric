"""Forms for invoicing."""
from django import forms
from core.models import Customer, Invoice, InvoiceLineItem, Payment


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'company', 'division', 'address', 'phone', 'email', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer name'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company (optional)'}),
            'division': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Full address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal notes'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not user.is_owner:
            # Non-owners can only assign to their own division
            self.fields['division'].choices = [
                (user.division.name, user.division.display_name)
            ] if user.division else []


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer', 'issue_date', 'due_date', 'tax_rate', 'notes', 'internal_notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Shown on invoice'}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Internal only'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            if user.is_owner:
                self.fields['customer'].queryset = Customer.objects.filter(is_active=True)
            elif user.division:
                self.fields['customer'].queryset = Customer.objects.filter(
                    is_active=True, division=user.division.name
                )
            else:
                self.fields['customer'].queryset = Customer.objects.none()


class InvoiceLineFormSet(forms.inlineformset_factory(
    Invoice, InvoiceLineItem,
    fields=['description', 'quantity', 'rate'],
    extra=3,
    can_delete=True,
    widgets={
        'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
    }
)):
    pass


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'date', 'method', 'reference', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Check #, etc.'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
