# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy application code
COPY manage.py .
COPY config/ ./config/

# Create log directory
RUN mkdir -p /app/logs

# Collect static files (optional)
RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]