#!/usr/bin/env python3
"""Entrypoint that properly handles the PORT env var on Railway."""
import os
import sys

# Railway sometimes sets PORT to literal '$PORT' string
# Try multiple sources to get the actual port
port = os.environ.get('PORT', '')
if port == '$PORT' or not port:
    # Try to find port from Railway's environment
    port = '8080'
    # Check if there's a PORT_FILE or similar
    for key in ['RAILWAY_PORT', 'SERVER_PORT', 'HTTP_PORT']:
        val = os.environ.get(key, '')
        if val and val != '$PORT':
            port = val
            break

print(f"[entrypoint] PORT env var = {repr(os.environ.get('PORT'))}", flush=True)
print(f"[entrypoint] Using port: {port}", flush=True)

# Run migrations (non-critical if they fail)
print("[entrypoint] Running migrations...", flush=True)
os.system('python manage.py migrate --noinput')

# Exec gunicorn, replacing this process entirely
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
