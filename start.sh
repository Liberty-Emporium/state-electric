#!/bin/sh
set -e

python manage.py migrate --noinput 2>/dev/null || true

PORT=${PORT:-8080}
echo "Starting gunicorn on port $PORT"
exec gunicorn config.wsgi:application --bind "0.0.0.0:$PORT" --timeout 30 --workers 2 --threads 4
