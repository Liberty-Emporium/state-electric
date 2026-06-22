FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway does NOT inject $PORT into Dockerfile builds.
# Hardcode 8080 which is Railway's default port for containers.
CMD ["sh", "-c", "python manage.py migrate --noinput 2>/dev/null; exec gunicorn config.wsgi:application --bind 0.0.0.0:8080 --timeout 30 --workers 2 --threads 4 --access-logfile - --error-logfile -"]
