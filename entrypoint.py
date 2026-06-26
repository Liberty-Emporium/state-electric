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
if result.returncode != 0:
    print(f"[entrypoint] Collectstatic stderr: {result.stderr[:500]}", flush=True)

# Run migrations
result = subprocess.run(
    [sys.executable, 'manage.py', 'migrate', '--noinput'],
    capture_output=True, text=True
)
print(f"[entrypoint] Migrate exit code: {result.returncode}", flush=True)
if result.returncode != 0:
    print(f"[entrypoint] Migrate stderr: {result.stderr[:500]}", flush=True)

# Fix missing columns and create superusers
try:
    import django
    django.setup()
    from django.db import connection
    from django.contrib.auth.hashers import make_password
    cursor = connection.cursor()

    # Add ALL missing columns to core_user (idempotent)
    missing_cols = [
        ('created_at', 'TIMESTAMP DEFAULT NOW()'),
        ('updated_at', 'TIMESTAMP DEFAULT NOW()'),
        ('last_login', 'TIMESTAMP DEFAULT NULL'),
        ('date_joined', 'TIMESTAMP DEFAULT NOW()'),
        ('is_superuser', 'BOOLEAN DEFAULT false'),
        ('is_staff', 'BOOLEAN DEFAULT false'),
        ('is_active', 'BOOLEAN DEFAULT true'),
        ('first_name', 'VARCHAR(150) DEFAULT \'\''),
        ('last_name', 'VARCHAR(150) DEFAULT \'\''),
        ('email', 'VARCHAR(254) DEFAULT \'\''),
        ('password', 'VARCHAR(128) DEFAULT \'\''),
        ('username', 'VARCHAR(150) DEFAULT \'\''),
        ('phone', 'VARCHAR(30) DEFAULT \'\''),
        ('role', 'VARCHAR(20) DEFAULT \'employee\''),
        ('is_active_employee', 'BOOLEAN DEFAULT true'),
        ('hourly_rate', 'DECIMAL(7,2) DEFAULT 25.00'),
    ]
    for col_name, col_def in missing_cols:
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='core_user' AND column_name='{col_name}'")
        if not cursor.fetchone():
            cursor.execute(f"ALTER TABLE core_user ADD COLUMN {col_name} {col_def}")
            print(f"[entrypoint] Added core_user.{col_name}", flush=True)

    # Add missing columns to core_customer
    cust_cols = [
        ('division', 'VARCHAR(20) DEFAULT \'GEN\''),
        ('address', 'TEXT DEFAULT \'\''),
        ('updated_at', 'TIMESTAMP DEFAULT NOW()'),
        ('created_at', 'TIMESTAMP DEFAULT NOW()'),
        ('is_active', 'BOOLEAN DEFAULT true'),
        ('name', 'VARCHAR(200) DEFAULT \'\''),
        ('company', 'VARCHAR(200) DEFAULT \'\''),
        ('contact_name', 'VARCHAR(200) DEFAULT \'\''),
        ('phone', 'VARCHAR(30) DEFAULT \'\''),
        ('email', 'VARCHAR(200) DEFAULT \'\''),
        ('notes', 'TEXT DEFAULT \'\''),
    ]
    for col_name, col_def in cust_cols:
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='core_customer' AND column_name='{col_name}'")
        if not cursor.fetchone():
            cursor.execute(f"ALTER TABLE core_customer ADD COLUMN {col_name} {col_def}")
            print(f"[entrypoint] Added core_customer.{col_name}", flush=True)

    # Create/reset superusers
    for uname, fname, lname, email, pwd in [
        ('admin', 'Admin', 'User', 'admin@stateelectric.co', 'ChangeMe123!'),
        ('rhonda', 'Rhonda', 'Teague', 'rmc0819@gmail.com', 'StateElectric2026!'),
        ('john', 'John', 'Teague', 'jet@stateelectricco.com', 'StateElectric2026!'),
    ]:
        cursor.execute("SELECT id FROM core_user WHERE username = %s LIMIT 1", [uname])
        if cursor.fetchone():
            cursor.execute("UPDATE core_user SET password = %s, is_superuser = true, is_staff = true, role = 'super_admin' WHERE username = %s", [make_password(pwd), uname])
            print(f"[entrypoint] Reset: {uname}", flush=True)
        else:
            cursor.execute(
                "INSERT INTO core_user (password, username, first_name, last_name, email, role, is_superuser, is_staff, is_active, phone, is_active_employee, date_joined) VALUES (%s, %s, %s, %s, %s, 'super_admin', true, true, true, '', true, NOW())",
                [make_password(pwd), uname, fname, lname, email]
            )
            print(f"[entrypoint] Created: {uname}", flush=True)

    print("[entrypoint] Superusers ready", flush=True)
except Exception as e:
    print(f"[entrypoint] Error: {e}", flush=True)

# Start gunicorn (replaces this process)
print(f"[entrypoint] Starting gunicorn on port {port}", flush=True)
os.execvp('gunicorn', [
    'gunicorn', 'config.wsgi:application',
    '--bind', f'0.0.0.0:{port}',
    '--timeout', '30', '--workers', '2', '--threads', '4',
    '--access-logfile', '-', '--error-logfile', '-',
])
