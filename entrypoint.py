#!/usr/bin/env python3
"""Entrypoint: collectstatic, migrate, seed superuser, start gunicorn."""
import os, subprocess, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

port = '8080'
base_dir = '/app'

# Collect static files
result = subprocess.run(
    [sys.executable, 'manage.py', 'collectstatic', '--noinput'],
    capture_output=True, text=True, cwd=base_dir
)
print(f"[entrypoint] Collectstatic exit code: {result.returncode}", flush=True)
if result.returncode != 0:
    print(f"[entrypoint] Static files: {result.stderr}", flush=True)

# Run migrations
result = subprocess.run(
    [sys.executable, 'manage.py', 'migrate', '--noinput'],
    capture_output=True, text=True, cwd=base_dir
)
print(f"[entrypoint] Migrate exit code: {result.returncode}", flush=True)

# Create superuser if not exists
import django
django.setup()
from core.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@stateelectric.co', 'admin123')
    print("[entrypoint] Superuser created: admin / admin123", flush=True)

# Start gunicorn
os.execvp('gunicorn', [
    'gunicorn', 'config.wsgi:application',
    '--bind', f'0.0.0.0:{port}',
    '--timeout', '30', '--workers', '2', '--threads', '4',
    '--access-logfile', '-', '--error-logfile', '-',
])
