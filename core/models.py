"""
State Electric — Core Models
Division-based employee separation, customer management, user roles.
"""
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils import timezone


class Division(models.Model):
    """Commercial or Residential division."""
    DIVISION_CHOICES = [
        ('commercial', 'Commercial Electrical'),
        ('residential', 'Residential Electrical'),
    ]
    name = models.CharField(max_length=20, choices=DIVISION_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    max_employees = models.PositiveIntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.display_name

    def employee_count(self):
        return self.employees.count()

    def is_at_capacity(self):
        return self.employee_count() >= self.max_employees


class User(AbstractUser):
    """Extended user with division assignment and role."""
    ROLE_CHOICES = [
        ('owner', 'Owner/Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    division = models.ForeignKey(
        Division, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='members', help_text="Employee's assigned division"
    )
    phone = models.CharField(max_length=20, blank=True)
    is_active_employee = models.BooleanField(default=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_owner(self):
        return self.role == 'owner' or self.is_superuser

    @property
    def is_manager_plus(self):
        return self.role in ('owner', 'manager') or self.is_superuser

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # Auto-assign to Django group matching division
        if self.division and self.is_active_employee:
            group, _ = Group.objects.get_or_create(name=self.division.name)
            self.groups.add(group)


class EmployeeProfile(models.Model):
    """Extended profile for employees."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    hire_date = models.DateField(null=True, blank=True)
    pay_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pay_type = models.CharField(
        max_length=10, choices=[('hourly', 'Hourly'), ('salary', 'Salary')],
        default='hourly'
    )
    title = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Profile: {self.user}"


class Customer(models.Model):
    """Customer — tagged to a division."""
    DIVISION_CHOICES = [
        ('commercial', 'Commercial'),
        ('residential', 'Residential'),
    ]
    name = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)
    division = models.CharField(max_length=20, choices=DIVISION_CHOICES)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def outstanding_balance(self):
        return self.invoices.filter(status__in=['sent', 'overdue']).aggregate(
            total=models.Sum('total_amount') - models.Sum('payments__amount')
        )['total'] or 0


class Invoice(models.Model):
    """Invoice for a customer."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('void', 'Void'),
    ]
    PAYMENT_METHODS = [
        ('check', 'Check'),
        ('cash', 'Cash'),
        ('card', 'Credit Card'),
        ('ach', 'ACH/Bank Transfer'),
        ('other', 'Other'),
    ]
    # Tax rates by state
    TAX_RATES = {
        'NC': 0.0675,  # NC state + avg local
        'SC': 0.06,
        'TN': 0.07,
        'VA': 0.053,
    }

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    tax_rate = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Not shown to customer")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date', '-id']

    def __str__(self):
        return f"Invoice #{self.invoice_number} — {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_number()
        if not self.due_date:
            from datetime import timedelta
            self.due_date = self.issue_date + timedelta(days=30)
        super().save(*args, **kwargs)

    def generate_number(self):
        from datetime import datetime
        prefix = datetime.now().strftime('%Y%m')
        last = Invoice.objects.filter(invoice_number__startswith=prefix).order_by('-invoice_number').first()
        if last:
            try:
                num = int(last.invoice_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                num = 1
        else:
            num = 1
        return f"{prefix}-{num:04d}"

    @property
    def subtotal(self):
        return sum(line.amount for line in self.lines.all())

    @property
    def tax_amount(self):
        return self.subtotal * self.tax_rate

    @property
    def total_amount(self):
        return self.subtotal + self.tax_amount

    @property
    def amount_paid(self):
        return self.payments.aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

    def update_status(self):
        if self.balance_due <= 0 and self.status in ('sent', 'overdue'):
            self.status = 'paid'
            self.save(update_fields=['status'])
        elif self.status == 'sent' and self.due_date < timezone.now().date():
            self.status = 'overdue'
            self.save(update_fields=['status'])


class InvoiceLineItem(models.Model):
    """Line item on an invoice."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    description = models.CharField(max_length=500, blank=True)
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


class Payment(models.Model):
    """Payment recorded against an invoice."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    method = models.CharField(max_length=20, choices=Invoice.PAYMENT_METHODS, default='check')
    reference = models.CharField(max_length=100, blank=True, help_text="Check #, transaction ID, etc.")
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"${self.amount} on {self.date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.update_status()
