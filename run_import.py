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

# Clean up any partial employees
cursor.execute("DELETE FROM core_user WHERE role='employee'")
print(f"Cleaned partial employees")

# Import employees
employees = data.get('employees', [])
emp_created = 0

for e in employees:
    name = e.get('name', '').strip().replace('*', '').strip()
    if not name:
        continue
    parts = name.split()
    first = parts[0] if parts else ''
    last = ' '.join(parts[1:]) if len(parts) > 1 else ''
    username = (name.lower().replace(' ', '.').replace("'", ""))[:150]
    phone = (e.get('phone', '') or '')[:20]
    email = (e.get('email', '') or '')[:200]
    
    cursor.execute("""
        INSERT INTO core_user (password, username, first_name, last_name, email, phone, role, is_active, is_active_employee, is_superuser, is_staff, date_joined)
        VALUES (%s, %s, %s, %s, %s, %s, 'employee', true, true, false, false, NOW())
    """, [make_password('StateElectric2026!'), username, first[:150], last[:150], email, phone])
    emp_created += 1
    print(f"  Created: {name}")

cursor.execute("SELECT COUNT(*) FROM core_customer")
customers = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM core_user WHERE role='employee'")
emps = cursor.fetchone()[0]

print(f"\nTotal customers: {customers}")
print(f"Total employees: {emps}")
connection.commit()
print("Done!")
