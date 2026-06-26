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

# Create vendor table if not exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS core_vendor (
        id SERIAL PRIMARY KEY,
        name VARCHAR(200) NOT NULL,
        company VARCHAR(200),
        contact_name VARCHAR(200),
        email VARCHAR(200),
        phone VARCHAR(200),
        address TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT '',
        is_active BOOLEAN NOT NULL DEFAULT true,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
""")
print("Vendor table ready")

# Import vendors
vendors = data.get('vendors', [])
created = skipped = errors = 0

for v in vendors:
    name = v.get('company', '').strip()
    if not name:
        skipped += 1
        continue
    
    cursor.execute("SELECT id FROM core_vendor WHERE name = %s LIMIT 1", [name])
    if cursor.fetchone():
        skipped += 1
        continue
    
    try:
        cursor.execute("""
            INSERT INTO core_vendor (name, company, contact_name, email, phone, address, notes, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, true)
        """, [name[:200], name[:200], (v.get('full_name','') or '')[:200], (v.get('email','') or '')[:200], (v.get('phone','') or '')[:200], v.get('billing_address',''), ''])
        created += 1
    except Exception as e:
        cursor.connection.rollback()
        errors += 1
        if errors <= 3:
            print(f"  Error: {name}: {str(e)[:80]}")

cursor.execute("SELECT COUNT(*) FROM core_vendor")
print(f"Vendors: {created} created, {skipped} skipped, {errors} errors")
print(f"Total vendors in DB: {cursor.fetchone()[0]}")

# Final summary
cursor.execute("SELECT COUNT(*) FROM core_customer")
print(f"Total customers: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM core_user WHERE role='employee'")
print(f"Total employees: {cursor.fetchone()[0]}")

connection.commit()
print("\nAll done!")
