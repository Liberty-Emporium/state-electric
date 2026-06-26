#!/usr/bin/env python3
"""Entrypoint: collectstatic, migrate, seed superuser, start gunicorn."""
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

# Create superusers if not exists (using raw SQL to avoid model/DB mismatch)
from django.db import connection
from django.contrib.auth.hashers import make_password
cursor = connection.cursor()

# Check NOT NULL columns for core_user
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='core_user' AND is_nullable='NO'")
not_null = {row[0] for row in cursor.fetchall()}
print(f"[entrypoint] User NOT NULL columns: {not_null}", flush=True)

def create_user(username, first_name, last_name, email, password):
    cursor.execute("SELECT id FROM core_user WHERE username = %s LIMIT 1", [username])
    if cursor.fetchone():
        return
    # Build INSERT dynamically based on NOT NULL columns
    base_cols = ['password', 'username', 'first_name', 'last_name', 'email', 'role', 'is_superuser', 'is_staff', 'is_active', 'date_joined']
    base_vals = [make_password(password), username, first_name, last_name, email, 'super_admin', True, True, True, 'NOW()']
    
    if 'phone' in not_null:
        base_cols.append('phone')
        base_vals.append('')
    if 'is_active_employee' in not_null:
        base_cols.append('is_active_employee')
        base_vals.append(True)
    
    cols = ', '.join(base_cols)
    placeholders = ', '.join(['%s'] * (len(base_cols) - 1)) + ', NOW()'
    sql = f"INSERT INTO core_user ({cols}) VALUES ({placeholders})"
    cursor.execute(sql, base_vals)
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
