import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()
from django.db import connection

cursor = connection.cursor()
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
print("Tables in DB:")
for row in cursor.fetchall():
    print(f"  {row[0]}")
