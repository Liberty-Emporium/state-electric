"""
Import QuickBooks data into Railway database - FINAL VERSION.
Handles all NOT NULL constraints and varchar limits.
"""
import os, sys, json, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.db import connection
from django.contrib.auth.hashers import make_password

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(BASE_DIR, 'state-electric-data', 'parsed_qb_data.json')
with open(data_file) as f:
    data = json.load(f)

cursor = connection.cursor()

# ============================================
# IMPORT CUSTOMERS
# ============================================
customers = data.get('customers', [])
created = skipped = errors = 0

for c in customers:
    name = c.get('company', '').strip()
    if not name:
        skipped += 1
        continue
    
    cursor.execute("SELECT id FROM core_customer WHERE name = %s LIMIT 1", [name])
    if cursor.fetchone():
        skipped += 1
        continue
    
    # Truncate fields to match varchar limits
    phone = (c.get('phone', '') or '')[:20]
    email = (c.get('email', '') or '')[:200]
    notes = f"Contact: {c.get('full_name', '')}\nBilling: {c.get('billing_address', '')}\nShipping: {c.get('shipping_address', '')}"
    
    try:
        cursor.execute("""
            INSERT INTO core_customer (name, company, division, address, phone, email, notes, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, [name[:200], name[:200], 'GEN', '', phone, email, notes, True])
        created += 1
    except Exception as e:
        cursor.connection.rollback()
        errors += 1
        if errors <= 3:
            print(f"  Error: {name}: {str(e)[:80]}")

print(f"Customers: {created} created, {skipped} skipped, {errors} errors")

# ============================================
# IMPORT EMPLOYEES
# ============================================
employees = data.get('employees', [])
emp_created = emp_skipped = emp_errors = 0

for e in employees:
    name = e.get('name', '').strip().replace('*', '').strip()
    if not name:
        emp_skipped += 1
        continue
    parts = name.split()
    first = parts[0] if parts else ''
    last = ' '.join(parts[1:]) if len(parts) > 1 else ''
    username = (name.lower().replace(' ', '.').replace("'", ""))[:150]
    phone = (e.get('phone', '') or '')[:20]
    email = (e.get('email', '') or '')[:200]
    
    cursor.execute("SELECT id FROM core_user WHERE username = %s LIMIT 1", [username])
    if cursor.fetchone():
        emp_skipped += 1
        continue
    
    try:
        cursor.execute("""
            INSERT INTO core_user (password, username, first_name, last_name, email, phone, role, is_active, is_active_employee, date_joined)
            VALUES (%s, %s, %s, %s, %s, %s, 'employee', true, true, NOW())
        """, [make_password('StateElectric2026!'), username, first[:150], last[:150], email, phone])
        emp_created += 1
    except Exception as e:
        cursor.connection.rollback()
        emp_errors += 1
        if emp_errors <= 3:
            print(f"  Error: {username}: {str(e)[:80]}")

print(f"Employees: {emp_created} created, {emp_skipped} skipped, {emp_errors} errors")

# ============================================
# SUMMARY
# ============================================
cursor.execute("SELECT COUNT(*) FROM core_customer")
print(f"\nTotal customers in DB: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM core_user WHERE role='employee'")
print(f"Total employees in DB: {cursor.fetchone()[0]}")

connection.commit()
print("\nDone!")
