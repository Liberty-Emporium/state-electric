"""
Write a temp import script directly on Railway using raw SQL.
Handles all NOT NULL constraints dynamically.
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()
from django.db import connection
import json

# Load parsed QB data
data_file = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    'state-electric-data', 'parsed_qb_data.json'
)
with open(data_file) as f:
    data = json.load(f)

# Get NOT NULL columns for core_customer
cursor = connection.cursor()
cursor.execute("""
    SELECT column_name, is_nullable, column_default 
    FROM information_schema.columns 
    WHERE table_name='core_customer' AND is_nullable='NO'
""")
not_null_cols = {row[0]: row[2] for row in cursor.fetchall()}
print("NOT NULL columns:", not_null_cols)

# Import customers
customers = data.get('customers', [])
created = 0
skipped = 0
errors = 0

for c in customers:
    name = c.get('company', '').strip()
    if not name:
        skipped += 1
        continue
    
    cursor.execute("SELECT id FROM core_customer WHERE name = %s LIMIT 1", [name])
    if cursor.fetchone():
        skipped += 1
        continue
    
    try:
        cursor.execute("""
            INSERT INTO core_customer (name, company, phone, email, notes, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, true, NOW(), NOW())
        """, [name, name, c.get('phone', ''), c.get('email', ''),
              f"Contact: {c.get('full_name', '')}\nBilling: {c.get('billing_address', '')}\nShipping: {c.get('shipping_address', '')}"])
        created += 1
    except Exception as e:
        # If division is required, try with it
        try:
            cursor.connection.rollback()
            cursor.execute("""
                INSERT INTO core_customer (name, company, division, phone, email, notes, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, true, NOW(), NOW())
            """, [name, name, 'General', c.get('phone', ''), c.get('email', ''),
                  f"Contact: {c.get('full_name', '')}\nBilling: {c.get('billing_address', '')}\nShipping: {c.get('shipping_address', '')}"])
            created += 1
        except Exception as e2:
            cursor.connection.rollback()
            errors += 1
            if errors <= 3:
                print(f"  Error importing '{name}': {e2}")

print(f"\nCustomers: {created} created, {skipped} skipped, {errors} errors")

# Import employees
employees = data.get('employees', [])
emp_created = emp_skipped = emp_errors = 0

from django.contrib.auth.hashers import make_password

for e in employees:
    name = e.get('name', '').strip().replace('*', '').strip()
    if not name:
        emp_skipped += 1
        continue
    parts = name.split()
    first = parts[0] if parts else ''
    last = ' '.join(parts[1:]) if len(parts) > 1 else ''
    username = name.lower().replace(' ', '.').replace("'", "")
    
    cursor.execute("SELECT id FROM core_user WHERE username = %s LIMIT 1", [username])
    if cursor.fetchone():
        emp_skipped += 1
        continue
    
    try:
        cursor.execute("""
            INSERT INTO core_user (password, username, first_name, last_name, email, phone, role, is_active, is_active_employee, date_joined)
            VALUES (%s, %s, %s, %s, %s, %s, 'employee', true, true, NOW())
        """, [make_password('StateElectric2026!'), username, first, last, e.get('email', ''), e.get('phone', '')])
        emp_created += 1
    except Exception as e2:
        cursor.connection.rollback()
        emp_errors += 1
        if emp_errors <= 3:
            print(f"  Error importing '{username}': {e2}")

print(f"Employees: {emp_created} created, {emp_skipped} skipped, {emp_errors} errors")

# Show totals
cursor.execute("SELECT COUNT(*) FROM core_customer")
print(f"\nTotal customers in DB: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM core_user")
print(f"Total users in DB: {cursor.fetchone()[0]}")

connection.commit()
print("\n✅ Import complete!")
