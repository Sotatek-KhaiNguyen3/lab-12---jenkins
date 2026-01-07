FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=off

WORKDIR /app

# Install build dependencies (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./app.py
COPY todolist ./todolist

# Create a non-root user for running the app
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Default env for DB; override in runtime
ENV DB_NAME=todolist.db

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]

