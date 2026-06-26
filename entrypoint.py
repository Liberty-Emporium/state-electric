#!/usr/bin/env python3
"""Entrypoint: collectstatic, migrate, seed superusers, start gunicorn."""
import os, subprocess, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

port = os.environ.get('PORT', '8080')

# Collect static files
result = subprocess.run(
    [sys.executable, 'manage.py', 'collectstatic', '--noinput'],
    capture_output=True, text=True
)
print(f"[entrypoint] Collectstatic exit code: {result.returncode}", flush=True)

# Run migrations
result = subprocess.run(
    [sys.executable, 'manage.py', 'migrate', '--noinput'],
    capture_output=True, text=True
)
print(f"[entrypoint] Migrate exit code: {result.returncode}", flush=True)

# Create superusers (raw SQL to handle schema differences)
from django.db import connection
from django.contrib.auth.hashers import make_password
cursor = connection.cursor()

cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='core_user' AND is_nullable='NO'")
not_null = {row[0] for row in cursor.fetchall()}

def create_user(username, first_name, last_name, email, password):
    cursor.execute("SELECT id FROM core_user WHERE username = %s LIMIT 1", [username])
    if cursor.fetchone():
        print(f"[entrypoint] {username} already exists", flush=True)
        return
    cols = ['password', 'username', 'first_name', 'last_name', 'email', 'role', 'is_superuser', 'is_staff', 'is_active', 'date_joined']
    vals = [make_password(password), username, first_name, last_name, email, 'super_admin', True, True, True]
    placeholder_list = ['%s'] * len(vals)
    if 'phone' in not_null:
        cols.insert(-1, 'phone')
        vals.insert(-1, '')
    if 'is_active_employee' in not_null:
        cols.insert(-1, 'is_active_employee')
        vals.insert(-1, True)
    placeholder_list = ['%s'] * (len(cols) - 1)  # all EXCEPT date_joined
    placeholder_list.append('NOW()')  # date_joined = NOW()
    sql = f"INSERT INTO core_user ({','.join(cols)}) VALUES ({','.join(placeholder_list)})"
    cursor.execute(sql, vals)
    print(f"[entrypoint] Superuser created: {username}", flush=True)

create_user('admin', 'Admin', 'User', 'admin@stateelectric.co', 'ChangeMe123!')
create_user('rhonda', 'Rhonda', 'Teague', 'rmc0819@gmail.com', 'StateElectric2026!')
create_user('john', 'John', 'Teague', 'jet@stateelectricco.com', 'StateElectric2026!')

# Start gunicorn (replaces this process)
os.execvp('gunicorn', [
    'gunicorn', 'config.wsgi:application',
    '--bind', f'0.0.0.0:{port}',
    '--timeout', '30', '--workers', '2', '--threads', '4',
    '--access-logfile', '-', '--error-logfile', '-',
])
