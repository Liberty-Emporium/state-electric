import os, sys, json, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()
from django.db import connection

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(BASE_DIR, 'state-electric-data', 'parsed_qb_data.json')
with open(data_file) as f:
    data = json.load(f)

cursor = connection.cursor()

# Just test with first 10 customers
customers = data.get('customers', [])[:10]
created = 0
for c in customers:
    name = c.get('company', '').strip()
    if not name:
        continue
    cursor.execute("SELECT id FROM core_customer WHERE name = %s LIMIT 1", [name])
    if cursor.fetchone():
        print(f"  Already exists: {name}")
        continue
    try:
        cursor.execute("""
            INSERT INTO core_customer (name, company, phone, email, notes, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, true, NOW(), NOW())
        """, [name, name, c.get('phone',''), c.get('email',''), f"Contact: {c.get('full_name','')}"])
        created += 1
        print(f"  Created: {name}")
    except Exception as e:
        cursor.connection.rollback()
        print(f"  Error: {name}: {e}")

cursor.execute("SELECT COUNT(*) FROM core_customer")
print(f"\nTotal customers: {cursor.fetchone()[0]}")
print(f"Created this run: {created}")
connection.commit()
