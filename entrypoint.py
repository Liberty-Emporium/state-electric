#!/usr/bin/env python3
"""Entrypoint: migrate, seed, create superuser, start gunicorn."""
import os
import subprocess
import sys

print("[entrypoint] Starting...", flush=True)

# Step 1: Run migrations
print("[entrypoint] Running migrations...", flush=True)
result = subprocess.run(
    [sys.executable, 'manage.py', 'migrate', '--noinput'],
    capture_output=True, text=True
)
print(f"[entrypoint] Migrations exit code: {result.returncode}", flush=True)
if result.stdout:
    print(f"[entrypoint] STDOUT: {result.stdout[-200:]}", flush=True)
if result.stderr:
    print(f"[entrypoint] STDERR: {result.stderr[-200:]}", flush=True)

# Step 2: Create superuser and seed data via raw subprocess
print("[entrypoint] Setting up user...", flush=True)
setup_script = '''
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from core.models import User, Division

# Create divisions
Division.objects.get_or_create(name="commercial", defaults={"display_name": "Commercial Electrical"})
Division.objects.get_or_create(name="residential", defaults={"display_name": "Residential Electrical"})

# Create superuser
if not User.objects.filter(username="jay").exists():
    User.objects.create_superuser("jay", "jay@alexanderai.site", "password123")
    print("Superuser created: jay")
else:
    print("Superuser already exists")
'''
result = subprocess.run(
    [sys.executable, '-c', setup_script],
    capture_output=True, text=True
)
print(f"[entrypoint] User setup exit code: {result.returncode}", flush=True)
if result.stdout:
    print(f"[entrypoint] STDOUT: {result.stdout}", flush=True)
if result.stderr:
    print(f"[entrypoint] STDERR: {result.stderr[-300:]}", flush=True)

# Step 3: Start gunicorn
print("[entrypoint] Starting gunicorn on port 8080...", flush=True)
os.execvp('gunicorn', [
    'gunicorn', 'config.wsgi:application',
    '--bind', '0.0.0.0:8080',
    '--timeout', '30', '--workers', '2', '--threads', '4',
    '--access-logfile', '-', '--error-logfile', '-',
])
