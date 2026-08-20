# syntax=docker/dockerfile:1

# -----------------------------------------------
# MotoShop API - production image
# -----------------------------------------------
FROM python:3.12-slim

# Python runtime tweaks
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code (secrets/local files are excluded via .dockerignore)
COPY . .

EXPOSE 8000

# Production server: gunicorn with async uvicorn workers.
# Settings (DATABASE_URL, SECRET_KEY, ...) are injected as environment
# variables by the deploy platform - file.env is never shipped in the image.
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
