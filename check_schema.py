import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='core_customer' ORDER BY ordinal_position")
print("Customer columns:", [r[0] for r in cursor.fetchall()])
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='core_vendor' ORDER BY ordinal_position")
print("Vendor columns:", [r[0] for r in cursor.fetchall()])
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='core_user' ORDER BY ordinal_position")
print("User columns:", [r[0] for r in cursor.fetchall()])
