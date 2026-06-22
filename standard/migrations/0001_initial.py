from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '__latest__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(max_length=20, default='scheduled', choices=[('scheduled', 'Scheduled'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('invoiced', 'Invoiced'), ('cancelled', 'Cancelled')])),
                ('priority', models.CharField(max_length=10, default='normal', choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')])),
                ('scheduled_date', models.DateField(blank=True, null=True)),
                ('completed_date', models.DateField(blank=True, null=True)),
                ('estimated_hours', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('actual_hours', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('estimated_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='jobs', to='core.customer')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('division', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='jobs', to='core.division')),
            ],
            options={
                'ordering': ['-scheduled_date', '-id'],
            },
        ),
        migrations.CreateModel(
            name='TimeEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('hours', models.DecimalField(decimal_places=2, max_digits=6)),
                ('description', models.TextField(blank=True)),
                ('clock_in', models.DateTimeField(blank=True, null=True)),
                ('clock_out', models.DateTimeField(blank=True, null=True)),
                ('is_overtime', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='time_entries', to=settings.AUTH_USER_MODEL)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='time_entries', to='standard.job')),
            ],
            options={
                'ordering': ['-date', '-id'],
            },
        ),
        migrations.CreateModel(
            name='PayPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('status', models.CharField(max_length=20, default='open', choices=[('open', 'Open'), ('processing', 'Processing'), ('closed', 'Closed')])),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('division', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pay_periods', to='core.division')),
            ],
            options={
                'ordering': ['-start_date'],
                'unique_together': {('start_date', 'end_date', 'division')},
            },
        ),
        migrations.CreateModel(
            name='PayrollEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('regular_hours', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('overtime_hours', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('gross_pay', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('federal_tax', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('state_tax', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('fica_ss', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('fica_medicare', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('other_deductions', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('net_pay', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payroll_entries', to=settings.AUTH_USER_MODEL)),
                ('pay_period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payroll_entries', to='standard.payperiod')),
            ],
            options={
                'ordering': ['employee__last_name', 'employee__first_name'],
                'unique_together': {('pay_period', 'employee')},
            },
        ),
        migrations.CreateModel(
            name='Estimate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estimate_number', models.CharField(max_length=50, unique=True)),
                ('status', models.CharField(max_length=20, default='draft', choices=[('draft', 'Draft'), ('sent', 'Sent'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('expired', 'Expired'), ('converted', 'Converted to Invoice')])),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('tax_rate', models.DecimalField(decimal_places=4, default=0, max_digits=6)),
                ('notes', models.TextField(blank=True)),
                ('internal_notes', models.TextField(blank=True)),
                ('accepted_date', models.DateField(blank=True, null=True)),
                ('converted_invoice_id', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='estimates', to='core.customer')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('division', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='estimates', to='core.division')),
            ],
            options={
                'ordering': ['-date', '-id'],
            },
        ),
        migrations.CreateModel(
            name='EstimateLineItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=500)),
                ('quantity', models.DecimalField(decimal_places=2, default=1, max_digits=10)),
                ('rate', models.DecimalField(decimal_places=2, max_digits=10)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('estimate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='standard.estimate')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
    ]
