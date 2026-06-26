"""
Import QuickBooks data into State Electric database.
Run: python manage.py import_qb_data
"""
import json
import os
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Customer, Vendor, User
from invoicing.models import Invoice, Payment


def safe_decimal(val):
    """Convert a value to Decimal safely."""
    if val is None:
        return Decimal('0')
    try:
        return Decimal(str(val).replace(',', '').replace('$', '').strip())
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0')


class Command(BaseCommand):
    help = 'Import QuickBooks export data into the database'

    def add_arguments(self, parser):
        parser.add_argument('--data-dir', type=str, default=None,
                            help='Directory containing parsed_qb_data.json')
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')

    def handle(self, *args, **options):
        data_dir = options['data_dir'] or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            'state-electric-data'
        )
        data_file = os.path.join(data_dir, 'parsed_qb_data.json')
        dry_run = options['dry_run']

        if not os.path.exists(data_file):
            self.stdout.write(self.style.ERROR(f'Data file not found: {data_file}'))
            self.stdout.write('Run the QB parser first or specify --data-dir')
            return

        with open(data_file, 'r') as f:
            data = json.load(f)

        self.stdout.write(self.style.SUCCESS(f'Loaded data from {data_file}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no data will be saved'))

        with transaction.atomic():
            self.import_customers(data.get('customers', []), dry_run)
            self.import_vendors(data.get('vendors', []), dry_run)
            self.import_employees(data.get('employees', []), dry_run)
            self.summarize_financials(data, dry_run)

        self.stdout.write(self.style.SUCCESS('\nImport complete!'))

    def import_customers(self, customers, dry_run):
        self.stdout.write(f'\nImporting {len(customers)} customers...')
        created = 0
        updated = 0
        skipped = 0
        for c in customers:
            name = c.get('company', '').strip()
            if not name:
                skipped += 1
                continue
            if not dry_run:
                obj, was_created = Customer.objects.get_or_create(
                    name=name,
                    defaults={
                        'contact_name': c.get('full_name', ''),
                        'email': c.get('email', ''),
                        'phone': c.get('phone', ''),
                        'billing_address': c.get('billing_address', ''),
                        'shipping_address': c.get('shipping_address', ''),
                    }
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            else:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f'  Customers: {created} created, {updated} updated, {skipped} skipped'))

    def import_vendors(self, vendors, dry_run):
        self.stdout.write(f'\nImporting {len(vendors)} vendors...')
        created = 0
        updated = 0
        skipped = 0
        for v in vendors:
            name = v.get('company', '').strip()
            if not name:
                skipped += 1
                continue
            if not dry_run:
                obj, was_created = Vendor.objects.get_or_create(
                    name=name,
                    defaults={
                        'contact_name': v.get('full_name', ''),
                        'email': v.get('email', ''),
                        'phone': v.get('phone', ''),
                        'address': v.get('billing_address', ''),
                    }
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            else:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f'  Vendors: {created} created, {updated} updated, {skipped} skipped'))

    def import_employees(self, employees, dry_run):
        self.stdout.write(f'\nImporting {len(employees)} employees...')
        created = 0
        updated = 0
        skipped = 0
        for e in employees:
            name = e.get('name', '').strip().replace('*', '').strip()
            if not name:
                skipped += 1
                continue
            parts = name.split()
            first_name = parts[0] if parts else ''
            last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
            username = name.lower().replace(' ', '.').replace("'", "").replace('-', '')
            if not dry_run:
                obj, was_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': e.get('email', ''),
                        'phone': e.get('phone', ''),
                        'role': 'employee',
                    }
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            else:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f'  Employees: {created} created, {updated} updated, {skipped} skipped'))

    def summarize_financials(self, data, dry_run):
        self.stdout.write('\nFinancial Summary:')
        for label in ['balance_sheet', 'profit_loss', 'trial_balance']:
            items = data.get(label, [])
            if items:
                total = sum(item.get('amount', 0) for item in items)
                self.stdout.write(f'  {label}: {len(items)} line items')
        gl = data.get('general_ledger', [])
        if gl:
            total_debits = sum(e.get('debit', 0) for e in gl)
            total_credits = sum(e.get('credit', 0) for e in gl)
            self.stdout.write(f'  general_ledger: {len(gl)} transactions')
            self.stdout.write(f'    Total Debits: ${total_debits:,.2f}')
            self.stdout.write(f'    Total Credits: ${total_credits:,.2f}')
