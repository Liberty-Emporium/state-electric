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

# Create superuser if not exists
import django
django.setup()
from core.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@stateelectric.co', 'ChangeMe123!')
    print("[entrypoint] Default superuser created: admin / ChangeMe123!", flush=True)

# Start gunicorn (replaces this process)
os.execvp('gunicorn', [
    'gunicorn', 'config.wsgi:application',
    '--bind', f'0.0.0.0:{port}',
    '--timeout', '30', '--workers', '2', '--threads', '4',
    '--access-logfile', '-', '--error-logfile', '-',
])
