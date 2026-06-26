"""
Import QuickBooks data - matches actual Railway DB schema.
Run: python manage.py import_qb_data
"""
import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from core.models import Customer, User


class Command(BaseCommand):
    help = 'Import QuickBooks data (schema-aware)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        data_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            'state-electric-data', 'parsed_qb_data.json'
        )
        dry_run = options['dry_run']

        if not os.path.exists(data_file):
            self.stdout.write(self.style.ERROR(f'Not found: {data_file}'))
            return

        with open(data_file, 'r') as f:
            data = json.load(f)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN'))

        with transaction.atomic():
            self.import_customers(data.get('customers', []), dry_run)
            self.import_employees(data.get('employees', []), dry_run)

        self.stdout.write(self.style.SUCCESS('Done!'))

    def import_customers(self, customers, dry_run):
        self.stdout.write(f'Importing {len(customers)} customers...')
        created = skipped = 0
        for c in customers:
            name = c.get('company', '').strip()
            if not name:
                skipped += 1
                continue
            if not dry_run:
                # Use raw SQL to match actual DB columns
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM core_customer WHERE name = %s LIMIT 1", [name]
                    )
                    if cursor.fetchone():
                        skipped += 1
                        continue
                    cursor.execute(
                        """INSERT INTO core_customer (name, phone, email, notes, is_active, created_at, updated_at)
                           VALUES (%s, %s, %s, %s, true, NOW(), NOW())""",
                        [name, c.get('phone', ''), c.get('email', ''),
                         f"Contact: {c.get('full_name', '')}\nBilling: {c.get('billing_address', '')}\nShipping: {c.get('shipping_address', '')}"]
                    )
                    created += 1
            else:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'  {created} created, {skipped} skipped'))

    def import_employees(self, employees, dry_run):
        self.stdout.write(f'Importing {len(employees)} employees...')
        created = skipped = 0
        for e in employees:
            name = e.get('name', '').strip().replace('*', '').strip()
            if not name:
                skipped += 1
                continue
            parts = name.split()
            first = parts[0] if parts else ''
            last = ' '.join(parts[1:]) if len(parts) > 1 else ''
            username = name.lower().replace(' ', '.').replace("'", "")
            if not dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM core_user WHERE username = %s LIMIT 1", [username]
                    )
                    if cursor.fetchone():
                        skipped += 1
                        continue
                    from django.contrib.auth.hashers import make_password
                    cursor.execute(
                        """INSERT INTO core_user (password, username, first_name, last_name, email, phone, role, is_active, is_active_employee, date_joined)
                           VALUES (%s, %s, %s, %s, %s, %s, 'employee', true, true, NOW())""",
                        [make_password('StateElectric2026!'), username, first, last, e.get('email', ''), e.get('phone', '')]
                    )
                    created += 1
            else:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'  {created} created, {skipped} skipped'))
