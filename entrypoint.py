#!/usr/bin/env python3
"""Entrypoint that handles migrations, seeding, and starting gunicorn."""
import os
import sys
import subprocess

port = '8080'

print("[entrypoint] Running migrations...", flush=True)
ret = subprocess.run(['python', 'manage.py', 'migrate', '--noinput'], capture_output=False)
print(f"[entrypoint] Migrations returned: {ret.returncode}", flush=True)

# Seed data if divisions don't exist
print("[entrypoint] Checking if seed is needed...", flush=True)
try:
    import django
    django.setup()
    from core.models import Division, User
    if not Division.objects.exists():
        print("[entrypoint] Seeding initial data...", flush=True)
        subprocess.run(['python', 'manage.py', 'seed_data'], capture_output=False)
    else:
        print("[entrypoint] Database already has data, skipping seed.", flush=True)
    
    # Create superuser if not exists
    if not User.objects.filter(username='jay').exists():
        print("[entrypoint] Creating superuser...", flush=True)
        User.objects.create_superuser('jay', 'jay@alexanderai.site', 'password123')
        print("[entrypoint] Superuser created: jay / password123", flush=True)
except Exception as e:
    print(f"[entrypoint] Seed check failed (may need migration first): {e}", flush=True)

print(f"[entrypoint] Starting gunicorn on port {port}...", flush=True)
os.execvp('gunicorn', [
    'gunicorn',
    'config.wsgi:application',
    '--bind', f'0.0.0.0:{port}',
    '--timeout', '30',
    '--workers', '2',
    '--threads', '4',
    '--access-logfile', '-',
    '--error-logfile', '-',
])
