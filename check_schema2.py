import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()
from django.db import connection

cursor = connection.cursor()
cursor.execute("SELECT column_name, character_maximum_length, is_nullable FROM information_schema.columns WHERE table_name='core_customer'")
print("Customer columns:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1] or ''} | nullable={row[2]}")

cursor.execute("SELECT DISTINCT division FROM core_customer WHERE division IS NOT NULL")
print("\nExisting division values:")
for row in cursor.fetchall():
    print(f"  '{row[0]}'")

cursor.execute("SELECT COUNT(*) FROM core_customer")
print(f"\nTotal customers: {cursor.fetchone()[0]}")
