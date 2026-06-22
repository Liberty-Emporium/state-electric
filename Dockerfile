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

# Start with a Python script that handles PORT properly
CMD ["python", "-c", "import os, subprocess; port = os.environ.get('PORT', '8080'); subprocess.run(['python', 'manage.py', 'migrate', '--noinput'], capture_output=True); subprocess.run(['gunicorn', 'config.wsgi:application', '--bind', f'0.0.0.0:{port}', '--timeout', '30', '--workers', '2', '--threads', '4'])"]
