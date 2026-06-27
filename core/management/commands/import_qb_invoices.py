"""
Import QuickBooks data into the database.
Run: python manage.py import_qb_invoices
"""
import json
import os
from django.core.management.base import BaseCommand
from django.db import connection
from core.models import Customer, Vendor, User


class Command(BaseCommand):
    help = 'Import QuickBooks data from parsed JSON'

    def handle(self, *args, **options):
        data_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            'state-electric-data', 'parsed_qb_data.json'
        )

        if not os.path.exists(data_file):
            self.stdout.write(self.style.ERROR(f'File not found: {data_file}'))
            return

        with open(data_file) as f:
            data = json.load(f)

        # Import Customers
        customers = data.get('customers', [])
        created = 0
        for c in customers:
            name = c.get('company', '').strip()
            if not name:
                continue
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
        self.stdout.write(self.style.SUCCESS(f'Customers: {created} created, {len(customers) - created} already existed'))

        # Import Vendors
        vendors = data.get('vendors', [])
        created = 0
        for v in vendors:
            name = v.get('company', '').strip()
            if not name:
                continue
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
        self.stdout.write(self.style.SUCCESS(f'Vendors: {created} created, {len(vendors) - created} already existed'))

        # Import Employees
        employees = data.get('employees', [])
        created = 0
        for e in employees:
            name = e.get('name', '').strip().replace('*', '').strip()
            if not name:
                continue
            username = name.lower().replace(' ', '.').replace("'", "")
            obj, was_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': name.split()[0] if name else '',
                    'last_name': ' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                    'email': e.get('email', ''),
                    'phone': e.get('phone', ''),
                    'role': 'employee',
                }
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Employees: {created} created, {len(employees) - created} already existed'))

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\nDatabase now has:'))
        self.stdout.write(f'  Customers: {Customer.objects.count()}')
        self.stdout.write(f'  Vendors: {Vendor.objects.count()}')
        self.stdout.write(f'  Employees: {User.objects.filter(role="employee").count()}')
