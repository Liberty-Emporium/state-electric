#!/bin/sh
set -e

# Run migrations
python manage.py migrate --noinput 2>/dev/null || true

# Replace PORT in CMD if set
if [ -n "$PORT" ]; then
    exec gunicorn config.wsgi:application --bind "0.0.0.0:$PORT" --timeout 30 --workers 2 --threads 4
else
    exec "$@"
fi
