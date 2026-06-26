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
cursor = connection.cursor()
cursor.execute("SELECT id FROM core_user WHERE username = 'admin' LIMIT 1")
if not cursor.fetchone():
    from django.contrib.auth.hashers import make_password
    cursor.execute(
        "INSERT INTO core_user (password, username, first_name, last_name, email, role, is_superuser, is_staff, is_active, date_joined) VALUES (%s, 'admin', 'Admin', 'User', 'admin@stateelectric.co', 'super_admin', true, true, true, NOW())",
        [make_password('ChangeMe123!')]
    )
    print("[entrypoint] Superuser created: admin / ChangeMe123!", flush=True)

# Ensure rhonda and john exist
for uname, fname, lname, email in [('rhonda', 'Rhonda', 'Teague', 'rmc0819@gmail.com'), ('john', 'John', 'Teague', 'jet@stateelectricco.com')]:
    cursor.execute("SELECT id FROM core_user WHERE username = %s LIMIT 1", [uname])
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO core_user (password, username, first_name, last_name, email, role, is_superuser, is_staff, is_active, date_joined) VALUES (%s, %s, %s, %s, %s, 'super_admin', true, true, true, NOW())",
            [make_password('StateElectric2026!'), uname, fname, lname, email]
        )
        print(f"[entrypoint] Superuser created: {uname} / StateElectric2026!", flush=True)

# Start gunicorn (replaces this process)
os.execvp('gunicorn', [
    'gunicorn', 'config.wsgi:application',
    '--bind', f'0.0.0.0:{port}',
    '--timeout', '30', '--workers', '2', '--threads', '4',
    '--access-logfile', '-', '--error-logfile', '-',
])
