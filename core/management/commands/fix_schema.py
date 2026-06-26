"""
Fix missing database columns. Run: python manage.py fix_schema
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Add missing columns to match model definitions'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        # Check and add missing columns for core_user
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'core_user' AND column_name = 'hourly_rate'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE core_user ADD COLUMN hourly_rate DECIMAL(7,2) DEFAULT 25.00")
            self.stdout.write(self.style.SUCCESS('Added core_user.hourly_rate'))
        else:
            self.stdout.write('core_user.hourly_rate already exists')
        
        # Check and add missing columns for core_customer
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'core_customer' AND column_name = 'division'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE core_customer ADD COLUMN division VARCHAR(20) NOT NULL DEFAULT 'GEN'")
            self.stdout.write(self.style.SUCCESS('Added core_customer.division'))
        else:
            self.stdout.write('core_customer.division already exists')
        
        # Check and add missing columns for core_customer address
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'core_customer' AND column_name = 'address'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE core_customer ADD COLUMN address TEXT NOT NULL DEFAULT ''")
            self.stdout.write(self.style.SUCCESS('Added core_customer.address'))
        else:
            self.stdout.write('core_customer.address already exists')
        
        # Check and add missing columns for core_customer updated_at
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'core_customer' AND column_name = 'updated_at'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE core_customer ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT NOW()")
            self.stdout.write(self.style.SUCCESS('Added core_customer.updated_at'))
        else:
            self.stdout.write('core_customer.updated_at already exists')
        
        self.stdout.write(self.style.SUCCESS('Schema fix complete!'))
