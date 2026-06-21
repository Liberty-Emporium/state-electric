"""
Management command to migrate data from QuickBooks CSV exports.

Usage:
    python manage.py migrate_quickbooks customers /path/to/customers.csv
    python manage.py migrate_quickbooks employees /path/to/employees.csv
    python manage.py migrate_quickbooks invoices /path/to/invoices.csv
    python manage.py migrate_quickbooks payments /path/to/payments.csv
    python manage.py migrate_quickbooks all /path/to/export_directory/

Expected CSV formats:
  customers: Name,Company,Address,Phone,Email,Division
  employees: FirstName,LastName,Email,Phone,Division,PayRate,HireDate
  invoices: InvoiceNumber,CustomerName,IssueDate,DueDate,Status,TaxRate,Description,Qty,Rate
  payments: InvoiceNumber,Amount,Date,Method,Reference
"""
import csv
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Customer, Division, Invoice, InvoiceLineItem, Payment, User


class Command(BaseCommand):
    help = 'Migrate data from QuickBooks CSV exports'

    def add_arguments(self, parser):
        parser.add_argument('type', type=str, choices=['customers', 'employees', 'invoices', 'payments', 'all'],
                            help='Type of data to import')
        parser.add_argument('path', type=str, help='Path to CSV file or directory (for "all")')
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
        parser.add_argument('--default-division', type=str, default='commercial',
                            help='Default division for records without one (commercial/residential)')

    def handle(self, *args, **options):
        import_type = options['type']
        path = options['path']
        dry_run = options['dry_run']
        default_division = options['default_division']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no data will be saved'))

        if import_type == 'all':
            self.import_all(path, dry_run, default_division)
        elif import_type == 'customers':
            self.import_customers(path, dry_run, default_division)
        elif import_type == 'employees':
            self.import_employees(path, dry_run, default_division)
        elif import_type == 'invoices':
            self.import_invoices(path, dry_run, default_division)
        elif import_type == 'payments':
            self.import_payments(path, dry_run)

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('Import complete!'))
        else:
            self.stdout.write(self.style.SUCCESS('Dry run complete — no data saved.'))

    def parse_date(self, value):
        """Parse various date formats."""
        if not value or not value.strip():
            return None
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%d-%m-%Y'):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
        return None

    def parse_decimal(self, value):
        """Parse decimal values, handling currency symbols."""
        if not value or not value.strip():
            return Decimal('0')
        cleaned = value.strip().replace('$', '').replace(',', '').replace('"', '')
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return Decimal('0')

    def get_or_create_division(self, name):
        """Get or create a division."""
        name = name.lower().strip() if name else 'commercial'
        if name not in ('commercial', 'residential'):
            name = 'commercial'
        div, _ = Division.objects.get_or_create(
            name=name, defaults={'display_name': f'{name.title()} Electrical'}
        )
        return div

    def import_customers(self, path, dry_run, default_division):
        """Import customers from QuickBooks CSV export."""
        if not os.path.exists(path):
            raise CommandError(f'File not found: {path}')

        created = 0
        updated = 0
        errors = 0

        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    name = row.get('Name', row.get('name', row.get('Customer', ''))).strip()
                    if not name:
                        self.stdout.write(self.style.WARNING(f'  Row {row_num}: Skipping — no name'))
                        errors += 1
                        continue

                    company = row.get('Company', row.get('company', '')).strip()
                    address = row.get('Address', row.get('address', row.get('Billing Address', ''))).strip()
                    phone = row.get('Phone', row.get('phone', '')).strip()
                    email = row.get('Email', row.get('email', '')).strip()
                    division_name = row.get('Division', row.get('division', default_division)).strip()

                    division = self.get_or_create_division(division_name)

                    if dry_run:
                        self.stdout.write(f'  [DRY] Would create/update: {name} ({division.name})')
                        created += 1
                        continue

                    customer, was_created = Customer.objects.update_or_create(
                        name=name,
                        defaults={
                            'company': company,
                            'address': address,
                            'phone': phone,
                            'email': email,
                            'division': division.name,
                            'is_active': True,
                        }
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Row {row_num}: Error — {e}'))
                    errors += 1

        self.stdout.write(f'Customers: {created} created, {updated} updated, {errors} errors')

    def import_employees(self, path, dry_run, default_division):
        """Import employees from QuickBooks CSV export."""
        if not os.path.exists(path):
            raise CommandError(f'File not found: {path}')

        created = 0
        updated = 0
        errors = 0

        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    first_name = row.get('FirstName', row.get('first_name', row.get('First', ''))).strip()
                    last_name = row.get('LastName', row.get('last_name', row.get('Last', ''))).strip()
                    email = row.get('Email', row.get('email', '')).strip()
                    phone = row.get('Phone', row.get('phone', '')).strip()
                    division_name = row.get('Division', row.get('division', default_division)).strip()
                    pay_rate = self.parse_decimal(row.get('PayRate', row.get('pay_rate', row.get('Rate', '0'))))
                    hire_date = self.parse_date(row.get('HireDate', row.get('hire_date', row.get('Hire Date', ''))))

                    if not first_name and not last_name:
                        self.stdout.write(self.style.WARNING(f'  Row {row_num}: Skipping — no name'))
                        errors += 1
                        continue

                    division = self.get_or_create_division(division_name)
                    username = email if email else f'{first_name.lower()}.{last_name.lower()}'
                    username = username.replace(' ', '.')[:150]

                    if dry_run:
                        self.stdout.write(f'  [DRY] Would create/update: {first_name} {last_name} ({division.name})')
                        created += 1
                        continue

                    user, was_created = User.objects.update_or_create(
                        username=username,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': email,
                            'phone': phone,
                            'role': 'employee',
                            'division': division,
                            'is_active_employee': True,
                        }
                    )
                    if was_created:
                        user.set_password('changeme123')
                        user.save()

                    # Update or create employee profile
                    from core.models import EmployeeProfile
                    profile, _ = EmployeeProfile.objects.get_or_create(user=user)
                    if pay_rate > 0:
                        profile.pay_rate = pay_rate
                    if hire_date:
                        profile.hire_date = hire_date
                    profile.save()

                    if was_created:
                        created += 1
                    else:
                        updated += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Row {row_num}: Error — {e}'))
                    errors += 1

        self.stdout.write(f'Employees: {created} created, {updated} updated, {errors} errors')

    def import_invoices(self, path, dry_run, default_division):
        """Import invoices from QuickBooks CSV export."""
        if not os.path.exists(path):
            raise CommandError(f'File not found: {path}')

        created = 0
        updated = 0
        errors = 0

        # Group rows by invoice number (QuickBooks exports line items as separate rows)
        invoices_data = {}

        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inv_num = row.get('InvoiceNumber', row.get('invoice_number', row.get('Num', row.get('Invoice #', '')))).strip()
                if not inv_num:
                    continue

                if inv_num not in invoices_data:
                    invoices_data[inv_num] = {
                        'customer': row.get('CustomerName', row.get('customer', row.get('Customer', ''))).strip(),
                        'issue_date': row.get('IssueDate', row.get('issue_date', row.get('Date', ''))).strip(),
                        'due_date': row.get('DueDate', row.get('due_date', '')).strip(),
                        'status': row.get('Status', row.get('status', 'sent')).strip().lower(),
                        'tax_rate': row.get('TaxRate', row.get('tax_rate', '0')).strip(),
                        'lines': [],
                    }

                desc = row.get('Description', row.get('description', row.get('Item', ''))).strip()
                qty = row.get('Qty', row.get('quantity', row.get('Quantity', '1'))).strip()
                rate = row.get('Rate', row.get('rate', row.get('Amount', '0'))).strip()

                if desc or qty or rate:
                    invoices_data[inv_num]['lines'].append({
                        'description': desc,
                        'quantity': qty,
                        'rate': rate,
                    })

        for inv_num, data in invoices_data.items():
            try:
                customer_name = data['customer']
                if not customer_name:
                    self.stdout.write(self.style.WARNING(f'  Invoice {inv_num}: Skipping — no customer'))
                    errors += 1
                    continue

                customer = Customer.objects.filter(name__iexact=customer_name).first()
                if not customer:
                    self.stdout.write(self.style.WARNING(f'  Invoice {inv_num}: Customer "{customer_name}" not found, creating...'))
                    customer = Customer.objects.create(
                        name=customer_name, division=default_division
                    )

                issue_date = self.parse_date(data['issue_date']) or datetime.now().date()
                due_date = self.parse_date(data['due_date']) or issue_date
                tax_rate = self.parse_decimal(data['tax_rate'])
                status = data['status']
                if status not in dict(Invoice.STATUS_CHOICES):
                    status = 'sent'

                if dry_run:
                    self.stdout.write(f'  [DRY] Would create invoice #{inv_num} for {customer.name} ({len(data["lines"])} lines)')
                    created += 1
                    continue

                invoice, was_created = Invoice.objects.update_or_create(
                    invoice_number=inv_num,
                    defaults={
                        'customer': customer,
                        'issue_date': issue_date,
                        'due_date': due_date,
                        'tax_rate': tax_rate,
                        'status': status,
                    }
                )

                # Clear and recreate line items
                if was_created or True:  # Always update lines
                    invoice.lines.all().delete()
                    for idx, line in enumerate(data['lines']):
                        InvoiceLineItem.objects.create(
                            invoice=invoice,
                            description=line['description'] or f'Item {idx + 1}',
                            quantity=self.parse_decimal(line['quantity']) or Decimal('1'),
                            rate=self.parse_decimal(line['rate']),
                            sort_order=idx,
                        )

                if was_created:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Invoice {inv_num}: Error — {e}'))
                errors += 1

        self.stdout.write(f'Invoices: {created} created, {updated} updated, {errors} errors')

    def import_payments(self, path, dry_run):
        """Import payments from QuickBooks CSV export."""
        if not os.path.exists(path):
            raise CommandError(f'File not found: {path}')

        created = 0
        errors = 0

        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                try:
                    inv_num = row.get('InvoiceNumber', row.get('invoice_number', row.get('Invoice #', ''))).strip()
                    amount = self.parse_decimal(row.get('Amount', row.get('amount', '0')))
                    date_str = row.get('Date', row.get('date', '')).strip()
                    method = row.get('Method', row.get('method', 'check')).strip().lower()
                    reference = row.get('Reference', row.get('reference', row.get('Ref', ''))).strip()

                    if not inv_num or amount <= 0:
                        self.stdout.write(self.style.WARNING(f'  Row {row_num}: Skipping — no invoice number or amount'))
                        errors += 1
                        continue

                    invoice = Invoice.objects.filter(invoice_number=inv_num).first()
                    if not invoice:
                        self.stdout.write(self.style.WARNING(f'  Row {row_num}: Invoice #{inv_num} not found'))
                        errors += 1
                        continue

                    payment_date = self.parse_date(date_str) or datetime.now().date()
                    if method not in dict(Invoice.PAYMENT_METHODS):
                        method = 'check'

                    if dry_run:
                        self.stdout.write(f'  [DRY] Would record ${amount} payment on #{inv_num}')
                        created += 1
                        continue

                    Payment.objects.create(
                        invoice=invoice,
                        amount=amount,
                        date=payment_date,
                        method=method,
                        reference=reference,
                    )
                    created += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Row {row_num}: Error — {e}'))
                    errors += 1

        self.stdout.write(f'Payments: {created} created, {errors} errors')

    def import_all(self, directory, dry_run, default_division):
        """Import all CSV files from a directory."""
        if not os.path.isdir(directory):
            raise CommandError(f'Directory not found: {directory}')

        self.stdout.write(self.style.MIGRATE_HEADING(f'Importing all from: {directory}'))

        file_map = {
            'customers': ['customers.csv', 'customer.csv', 'Customers.csv'],
            'employees': ['employees.csv', 'employee.csv', 'Employees.csv'],
            'invoices': ['invoices.csv', 'invoice.csv', 'Invoices.csv'],
            'payments': ['payments.csv', 'payment.csv', 'Payments.csv'],
        }

        for data_type, filenames in file_map.items():
            for filename in filenames:
                filepath = os.path.join(directory, filename)
                if os.path.exists(filepath):
                    self.stdout.write(self.style.MIGRATE_HEADING(f'\n--- Importing {data_type} from {filename} ---'))
                    if data_type == 'customers':
                        self.import_customers(filepath, dry_run, default_division)
                    elif data_type == 'employees':
                        self.import_employees(filepath, dry_run, default_division)
                    elif data_type == 'invoices':
                        self.import_invoices(filepath, dry_run, default_division)
                    elif data_type == 'payments':
                        self.import_payments(filepath, dry_run)
                    break
            else:
                self.stdout.write(self.style.WARNING(f'  No {data_type} file found in {directory}'))
