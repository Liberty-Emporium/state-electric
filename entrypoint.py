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

# Create superusers (raw SQL to handle schema differences)
try:
    import django
    django.setup()
    from django.db import connection
    from django.contrib.auth.hashers import make_password
    cursor = connection.cursor()

    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='core_user' AND is_nullable='NO'")
    not_null = {row[0] for row in cursor.fetchall()}
    print(f"[entrypoint] NOT NULL columns: {not_null}", flush=True)

    def create_user(username, first_name, last_name, email, password):
        try:
            cursor.execute("SELECT id FROM core_user WHERE username = %s LIMIT 1", [username])
            if cursor.fetchone():
                print(f"[entrypoint] {username} already exists, skipping", flush=True)
                return
            cols = ['password', 'username', 'first_name', 'last_name', 'email', 'role', 'is_superuser', 'is_staff', 'is_active']
            vals = [make_password(password), username, first_name, last_name, email, 'super_admin', True, True, True]
            if 'phone' in not_null:
                cols.append('phone')
                vals.append('')
            if 'is_active_employee' in not_null:
                cols.append('is_active_employee')
                vals.append(True)
            cols.append('date_joined')
            ph = ', '.join(['%s'] * len(vals)) + ', NOW()'
            sql = f"INSERT INTO core_user ({','.join(cols)}) VALUES ({ph})"
            cursor.execute(sql, vals)
            print(f"[entrypoint] Created: {username}", flush=True)
        except Exception as e:
            print(f"[entrypoint] Error creating {username}: {e}", flush=True)

    create_user('admin', 'Admin', 'User', 'admin@stateelectric.co', 'ChangeMe123!')
    create_user('rhonda', 'Rhonda', 'Teague', 'rmc0819@gmail.com', 'StateElectric2026!')
    create_user('john', 'John', 'Teague', 'jet@stateelectricco.com', 'StateElectric2026!')
    
    # Also reset rhonda's password to make sure it's correct
    cursor.execute("UPDATE core_user SET password = %s WHERE username = 'rhonda'", [make_password('StateElectric2026!')])
    cursor.execute("UPDATE core_user SET password = %s WHERE username = 'john'", [make_password('StateElectric2026!')])
    cursor.execute("UPDATE core_user SET password = %s WHERE username = 'admin'", [make_password('ChangeMe123!')])
    print("[entrypoint] Passwords reset", flush=True)
except Exception as e:
    print(f"[entrypoint] Superuser creation error: {e}", flush=True)

# Start gunicorn (replaces this process)
print(f"[entrypoint] Starting gunicorn on port {port}", flush=True)
os.execvp('gunicorn', [
    'gunicorn', 'config.wsgi:application',
    '--bind', f'0.0.0.0:{port}',
    '--timeout', '30', '--workers', '2', '--threads', '4',
    '--access-logfile', '-', '--error-logfile', '-',
])
