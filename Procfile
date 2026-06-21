web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 30 --workers 2 --threads 4
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py seed_data --noinput 2>/dev/null || true
