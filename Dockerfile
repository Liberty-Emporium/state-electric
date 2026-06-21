FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Release phase
RUN python manage.py migrate --noinput 2>/dev/null || true
RUN python manage.py collectstatic --noinput
RUN python manage.py seed_data --noinput 2>/dev/null || true

# Start
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--timeout", "30", "--workers", "2", "--threads", "4"]
