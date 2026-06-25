from django.db import models
from django.conf import settings


class PayrollRun(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    pay_date = models.DateField()
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_gross = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_net = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-pay_date']

    def __str__(self):
        return f"Payroll {self.pay_date} — {self.status}"


class Paystub(models.Model):
    """Individual employee pay stub within a payroll run."""
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='paystubs')
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='paystubs')

    # Earnings
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # NC State Taxes (W-2 employees only, no 1099s)
    federal_income_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    nc_state_income_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    social_security = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # 6.2%
    medicare = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # 1.45%
    nc_unemployment = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Pre-tax deductions
    health_insurance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    aflac = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    retirement_401k = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Post-tax deductions
    child_support = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Totals
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Direct deposit
    deposit_account = models.CharField(max_length=100, blank=True, default='')
    deposit_type = models.CharField(max_length=20, choices=[
        ('checking', 'Checking'),
        ('savings', 'Savings'),
    ], default='checking')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payroll_run__pay_date', 'employee__last_name']

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.payroll_run.pay_date} — ${self.net_pay}"

    def save(self, *args, **kwargs):
        self.total_deductions = (
            self.federal_income_tax + self.nc_state_income_tax +
            self.social_security + self.medicare + self.nc_unemployment +
            self.health_insurance + self.aflac + self.retirement_401k +
            self.child_support + self.other_deductions
        )
        self.net_pay = self.gross_pay - self.total_deductions
        super().save(*args, **kwargs)


class TaxRate(models.Model):
    """NC tax rates for payroll calculations. W-2 only."""
    year = models.IntegerField()
    federal_ss_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.062)  # Social Security
    federal_ss_wage_base = models.DecimalField(max_digits=10, decimal_places=2, default=168600)
    federal_medicare_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0145)
    federal_futa_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.006)
    nc_income_tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.045)  # NC flat 4.5%
    nc_unemployment_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.01)
    nc_unemployment_wage_base = models.DecimalField(max_digits=10, decimal_places=2, default=29600)

    class Meta:
        ordering = ['-year']

    def __str__(self):
        return f"Tax Rates {self.year}"
