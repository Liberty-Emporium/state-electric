"""
Standard tier models: Jobs, Time Tracking, Payroll, Estimates.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import Customer, Division, User


class Job(models.Model):
    """Job/project for a customer."""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    title = models.CharField(max_length=200)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='jobs')
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='jobs')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    scheduled_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date', '-id']

    def __str__(self):
        return f"{self.title} — {self.customer.name}"

    @property
    def is_overdue(self):
        if self.status in ('completed', 'invoiced', 'cancelled'):
            return False
        if self.scheduled_date and self.scheduled_date < timezone.now().date():
            return True
        return False

    @property
    def total_time_hours(self):
        return self.time_entries.aggregate(
            total=models.Sum('hours')
        )['total'] or 0


class TimeEntry(models.Model):
    """Time clock entry for an employee on a job."""
    employee = models.ForeignKey(User, on_delete=models.PROTECT, related_name='time_entries')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='time_entries')
    date = models.DateField(default=timezone.now)
    hours = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField(blank=True)
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    is_overtime = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.job.title} ({self.date})"

    def save(self, *args, **kwargs):
        # Auto-calculate hours from clock_in/clock_out if not set
        if self.clock_in and self.clock_out and not self.hours:
            delta = self.clock_out - self.clock_in
            self.hours = round(delta.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)


class PayPeriod(models.Model):
    """Pay period for payroll processing."""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('processing', 'Processing'),
        ('closed', 'Closed'),
    ]

    start_date = models.DateField()
    end_date = models.DateField()
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='pay_periods')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        unique_together = ['start_date', 'end_date', 'division']

    def __str__(self):
        return f"{self.division.display_name}: {self.start_date} — {self.end_date}"

    @property
    def total_gross(self):
        return self.payroll_entries.aggregate(
            total=models.Sum('gross_pay')
        )['total'] or 0

    @property
    def total_net(self):
        return self.payroll_entries.aggregate(
            total=models.Sum('net_pay')
        )['total'] or 0

    @property
    def employee_count(self):
        return self.payroll_entries.count()


class PayrollEntry(models.Model):
    """Payroll entry for an employee within a pay period."""
    pay_period = models.ForeignKey(PayPeriod, on_delete=models.CASCADE, related_name='payroll_entries')
    employee = models.ForeignKey(User, on_delete=models.PROTECT, related_name='payroll_entries')
    regular_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    federal_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    state_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fica_ss = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Social Security 6.2%
    fica_medicare = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Medicare 1.45%
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee__last_name', 'employee__first_name']
        unique_together = ['pay_period', 'employee']

    def __str__(self):
        return f"{self.employee.get_full_name()} — ${self.net_pay}"

    def calculate_taxes(self, state='NC'):
        """Calculate tax withholdings based on gross pay."""
        # Federal tax brackets (2024, single, simplified)
        gross = float(self.gross_pay)
        if gross <= 0:
            return

        # Simplified federal withholding (2024 single filer)
        if gross <= 442.31:  # weekly equivalent of $23,000/year
            self.federal_tax = round(gross * 0.10, 2)
        elif gross <= 1542.31:  # $80,000/year
            self.federal_tax = round(44.23 + (gross - 442.31) * 0.12, 2)
        elif gross <= 2968.46:  # $154,200/year
            self.federal_tax = round(176.21 + (gross - 1542.31) * 0.22, 2)
        elif gross <= 4393.85:  # $229,000/year
            self.federal_tax = round(490.85 + (gross - 2968.46) * 0.24, 2)
        else:
            self.federal_tax = round(834.73 + (gross - 4393.85) * 0.32, 2)

        # State tax
        state_rates = {
            'NC': 0.0475,   # NC flat rate 2024
            'SC': 0.06,     # SC top rate (simplified)
            'VA': 0.0575,   # VA top rate
            'TN': 0.0,      # No state income tax
        }
        rate = state_rates.get(state, 0.0475)
        self.state_tax = round(gross * rate, 2)

        # FICA
        self.fica_ss = round(gross * 0.062, 2)
        self.fica_medicare = round(gross * 0.0145, 2)

        # Net pay
        total_deductions = (
            self.federal_tax + self.state_tax +
            self.fica_ss + self.fica_medicare + self.other_deductions
        )
        self.net_pay = round(gross - total_deductions, 2)

    def save(self, *args, **kwargs):
        if not self.net_pay and self.gross_pay:
            self.calculate_taxes()
        super().save(*args, **kwargs)


class Estimate(models.Model):
    """Customer estimate/quote."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
        ('converted', 'Converted to Invoice'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='estimates')
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='estimates')
    estimate_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    accepted_date = models.DateField(null=True, blank=True)
    converted_invoice_id = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"Estimate #{self.estimate_number} — {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.estimate_number:
            self.estimate_number = self.generate_number()
        super().save(*args, **kwargs)

    def generate_number(self):
        from datetime import datetime
        prefix = datetime.now().strftime('%Y%m')
        last = Estimate.objects.filter(estimate_number__startswith=prefix).order_by('-estimate_number').first()
        if last:
            try:
                num = int(last.estimate_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                num = 1
        else:
            num = 1
        return f"EST-{prefix}-{num:04d}"

    @property
    def subtotal(self):
        return sum(line.amount for line in self.lines.all())

    @property
    def tax_amount(self):
        return self.subtotal * self.tax_rate

    @property
    def total(self):
        return self.subtotal + self.tax_amount

    def is_expired(self):
        if self.expiry_date and self.status == 'sent':
            return timezone.now().date() > self.expiry_date
        return False


class EstimateLineItem(models.Model):
    """Line item on an estimate."""
    estimate = models.ForeignKey(Estimate, on_delete=models.CASCADE, related_name='lines')
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
