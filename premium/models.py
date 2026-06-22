"""
Premium tier models: Recurring Invoices, Expenses, Bank Reconciliation,
Purchase Orders, 1099 Support, AI Estimates, Tax Forms, Data Import, Contracts.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import Customer, Division, User
from standard.models import Job, Estimate


# ─── RECURRING INVOICES ──────────────────────────────────────────

class RecurringInvoice(models.Model):
    """Template for auto-generated recurring invoices."""
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('ended', 'Ended'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='recurring_invoices')
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='recurring_invoices')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    next_invoice_date = models.DateField()
    tax_rate = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Recurring #{self.customer.name} ({self.get_frequency_display()})"


class RecurringInvoiceLine(models.Model):
    """Line items for recurring invoice templates."""
    recurring = models.ForeignKey(RecurringInvoice, on_delete=models.CASCADE, related_name='lines')
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.description} × {self.quantity}"

    @property
    def amount(self):
        return self.quantity * self.rate


# ─── EXPENSE TRACKING ────────────────────────────────────────────

class ExpenseCategory(models.Model):
    """Categories for expense tracking."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Expense Categories'

    def __str__(self):
        return self.name


class Expense(models.Model):
    """Business expense tracking."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('reimbursed', 'Reimbursed'),
    ]

    description = models.CharField(max_length=300)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='expenses')
    vendor = models.CharField(max_length=200, blank=True)
    receipt = models.FileField(upload_to='receipts/%Y/%m/', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.description} — ${self.amount}"


# ─── BANK RECONCILIATION ────────────────────────────────────────

class BankAccount(models.Model):
    """Bank accounts for reconciliation."""
    ACCOUNT_TYPES = [
        ('checking', 'Checking'),
        ('savings', 'Savings'),
        ('credit', 'Credit Card'),
        ('line_of_credit', 'Line of Credit'),
    ]

    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='checking')
    bank_name = models.CharField(max_length=200, blank=True)
    last_four = models.CharField(max_length=4, blank=True)
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='bank_accounts')
    is_active = models.BooleanField(default=True)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.bank_name})"


class BankTransaction(models.Model):
    """Imported bank transactions for reconciliation."""
    STATUS_CHOICES = [
        ('unmatched', 'Unmatched'),
        ('matched', 'Matched'),
        ('reconciled', 'Reconciled'),
        ('excluded', 'Excluded'),
    ]

    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField()
    description = models.CharField(max_length=300)
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # positive = deposit, negative = withdrawal
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unmatched')
    matched_payment = models.ForeignKey('core.Payment', on_delete=models.SET_NULL, null=True, blank=True)
    matched_expense = models.ForeignKey(Expense, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.date} — {self.description} (${self.amount})"


# ─── PURCHASE ORDERS ─────────────────────────────────────────────

class PurchaseOrder(models.Model):
    """Purchase orders to vendors/suppliers."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('partial', 'Partially Received'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=50, unique=True)
    vendor = models.CharField(max_length=200)
    vendor_address = models.TextField(blank=True)
    vendor_email = models.CharField(max_length=200, blank=True)
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='purchase_orders')
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    order_date = models.DateField(default=timezone.now)
    expected_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date', '-id']

    def __str__(self):
        return f"PO #{self.po_number} — {self.vendor}"

    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = self.generate_number()
        super().save(*args, **kwargs)

    def generate_number(self):
        from datetime import datetime
        prefix = datetime.now().strftime('%Y%m')
        last = PurchaseOrder.objects.filter(po_number__startswith=prefix).order_by('-po_number').first()
        if last:
            try:
                num = int(last.po_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                num = 1
        else:
            num = 1
        return f"PO-{prefix}-{num:04d}"

    @property
    def subtotal(self):
        return sum(line.amount for line in self.lines.all())

    @property
    def tax_amount(self):
        return self.subtotal * self.tax_rate

    @property
    def total(self):
        return self.subtotal + self.tax_amount + self.shipping


class PurchaseOrderLine(models.Model):
    """Line items on a purchase order."""
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    received_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.description} × {self.quantity}"

    @property
    def amount(self):
        return self.quantity * self.rate


# ─── 1099 CONTRACTOR SUPPORT ─────────────────────────────────────

class Contractor(models.Model):
    """Independent contractor for 1099 tracking."""
    ENTITY_TYPES = [
        ('individual', 'Individual'),
        ('llc', 'LLC'),
        ('s_corp', 'S-Corp'),
        ('c_corp', 'C-Corp'),
        ('partnership', 'Partnership'),
    ]

    name = models.CharField(max_length=200)
    business_name = models.CharField(max_length=200, blank=True)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES, default='individual')
    email = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True, help_text="EIN or SSN (encrypted in production)")
    w9_on_file = models.BooleanField(default=False)
    w9_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_paid_ytd(self):
        from django.db.models import Sum
        current_year = timezone.now().year
        return self.payments.filter(
            date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0


class ContractorPayment(models.Model):
    """Payment to a contractor (tracked for 1099)."""
    contractor = models.ForeignKey(Contractor, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=300, blank=True)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name='contractor_payments')
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='contractor_payments')
    is_1099_reportable = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.contractor.name} — ${self.amount} ({self.date})"


# ─── TAX FORMS ───────────────────────────────────────────────────

class TaxForm(models.Model):
    """Generated tax forms (W-2, 1099-NEC, etc.)."""
    FORM_TYPES = [
        ('w2', 'W-2 Wage and Tax Statement'),
        ('1099_nec', '1099-NEC Nonemployee Compensation'),
        ('1099_misc', '1099-MISC Miscellaneous Income'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('final', 'Final'),
        ('filed', 'Filed'),
    ]

    form_type = models.CharField(max_length=20, choices=FORM_TYPES)
    tax_year = models.PositiveIntegerField()
    recipient_name = models.CharField(max_length=200)
    recipient_tax_id = models.CharField(max_length=50, blank=True)
    recipient_address = models.TextField(blank=True)
    total_compensation = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    federal_withheld = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    state_withheld = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    social_security_wages = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    medicare_wages = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-tax_year', 'form_type']
        unique_together = ['form_type', 'tax_year', 'recipient_name']

    def __str__(self):
        return f"{self.get_form_type_display()} — {self.recipient_name} ({self.tax_year})"


# ─── DATA IMPORT ─────────────────────────────────────────────────

class DataImport(models.Model):
    """Track data import jobs."""
    IMPORT_TYPES = [
        ('customers', 'Customers'),
        ('employees', 'Employees'),
        ('invoices', 'Invoices'),
        ('payments', 'Payments'),
        ('expenses', 'Expenses'),
        ('all', 'All Data'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    import_type = models.CharField(max_length=20, choices=IMPORT_TYPES)
    file = models.FileField(upload_to='imports/%Y/%m/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_rows = models.PositiveIntegerField(default=0)
    imported_rows = models.PositiveIntegerField(default=0)
    error_rows = models.PositiveIntegerField(default=0)
    error_log = models.TextField(blank=True)
    column_mapping = models.JSONField(default=dict, blank=True)
    dry_run = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_import_type_display()} import — {self.status} ({self.created_at:%m/%d})"


# ─── CONTRACTS / E-SIGNATURE ────────────────────────────────────

class Contract(models.Model):
    """Customer contracts with e-signature support."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent for Signature'),
        ('signed', 'Signed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=300)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='contracts')
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='contracts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    body = models.TextField(help_text="Contract terms and conditions")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    signature_data = models.TextField(blank=True, help_text="Base64-encoded signature image")
    signer_name = models.CharField(max_length=200, blank=True)
    signer_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.customer.name}"


# ─── AI ESTIMATE TEMPLATES ──────────────────────────────────────

class EstimateTemplate(models.Model):
    """Reusable estimate templates for AI-powered estimates."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    job_type = models.CharField(max_length=100, blank=True, help_text="e.g., 'Panel Upgrade', 'Wiring', 'Inspection'")
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='estimate_templates')
    base_labor_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    labor_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    material_estimate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overhead_percent = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    profit_margin_percent = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def estimated_total(self):
        labor = float(self.base_labor_hours) * float(self.labor_rate)
        materials = float(self.material_estimate)
        subtotal = labor + materials
        overhead = subtotal * (float(self.overhead_percent) / 100)
        with_overhead = subtotal + overhead
        profit = with_overhead * (float(self.profit_margin_percent) / 100)
        return round(with_overhead + profit, 2)
